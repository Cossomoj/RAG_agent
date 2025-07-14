from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
import sqlite3
import asyncio
import websockets
import json
import requests
from datetime import datetime
import logging


app = Flask(__name__)

# Расширенная настройка CORS для кросс-доменных запросов
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
DATABASE_URL = os.environ.get('DATABASE_URL', '/app/src/main_version/AI_agent.db')
WEBSOCKET_URL = os.environ.get('WEBSOCKET_URL', 'ws://127.0.0.1:8000/ws')

# Кеш для ответов (аналогично Telegram боту)
cache_dict = {}
cache_by_specialization = {}

def get_cache_type_for_question(question_id):
    """
    Определяет тип кеша для вопроса.
    
    УНИФИЦИРОВАННАЯ ЛОГИКА (как в телеграм боте):
    ВСЕ вопросы из библиотеки кешируются по специализации пользователя.
    
    Returns:
        'by_specialization' - для всех вопросов из библиотеки
        'no_cache' - для системных вопросов (777, 888) которые не кешируются
    """
    try:
        # Системные вопросы не кешируются
        if question_id in [777, 888]:
            return 'no_cache'
        
        # Проверяем, что вопрос существует в БД
        conn = get_db_connection()
        if not conn:
            logger.warning(f"Нет подключения к БД для question_id {question_id}, отключаем кеш")
            return 'no_cache'
            
        cursor = conn.cursor()
        cursor.execute("SELECT question_id FROM Questions WHERE question_id = ?", (question_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            # Если вопрос не найден в БД, не кешируем
            logger.warning(f"Question ID {question_id} не найден в БД, кеширование отключено")
            return 'no_cache'
        
        # ВСЕ вопросы из библиотеки кешируются по специализации пользователя
        return 'by_specialization'
            
    except Exception as e:
        logger.error(f"Ошибка при определении типа кеша для question_id {question_id}: {e}")
        return 'no_cache'  # Fallback к отключению кеша

# Функции для работы с базой данных Questions
def get_db_connection():
    """Получение подключения к базе данных"""
    try:
        # Детальное логирование для диагностики
        logger.info(f"=== DATABASE CONNECTION DEBUG ===")
        logger.info(f"DATABASE_URL from env: {repr(os.environ.get('DATABASE_URL'))}")
        logger.info(f"DATABASE_URL used: {repr(DATABASE_URL)}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"DB file exists: {os.path.exists(DATABASE_URL)}")
        if os.path.exists(DATABASE_URL):
            logger.info(f"DB file stats: {os.stat(DATABASE_URL)}")
            logger.info(f"DB file permissions: {oct(os.stat(DATABASE_URL).st_mode)}")
            logger.info(f"DB file readable: {os.access(DATABASE_URL, os.R_OK)}")
            logger.info(f"DB file writable: {os.access(DATABASE_URL, os.W_OK)}")
        logger.info(f"Current process UID: {os.getuid()}")
        logger.info(f"Current process GID: {os.getgid()}")
        logger.info(f"=== ATTEMPTING SQLITE CONNECTION ===")
        
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        logger.info(f"=== DATABASE CONNECTION SUCCESS ===")
        return conn
    except sqlite3.Error as e:
        logger.error(f"=== DATABASE CONNECTION FAILED ===")
        logger.error(f"SQLite Error type: {type(e).__name__}")
        logger.error(f"SQLite Error details: {str(e)}")
        logger.error(f"SQLite Error args: {e.args}")
        return None
    except Exception as e:
        logger.error(f"=== UNEXPECTED ERROR IN DB CONNECTION ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        return None

def get_questions_from_db(specialization=None, category=None, is_active=True):
    """Получение вопросов из базы данных с фильтрацией (убран параметр role)"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
            
        cursor = conn.cursor()
        
        # Базовый запрос
        query = """
        SELECT q.*, p.prompt_template, v.display_name as vector_store_display
        FROM Questions q
        LEFT JOIN Prompts p ON q.prompt_id = p.question_id
        LEFT JOIN VectorStores v ON q.vector_store = v.name
        WHERE q.is_active = ?
        """
        params = [is_active]
        
        # Добавляем фильтры
        if specialization:
            query += " AND (q.specialization IS NULL OR q.specialization = ?)"
            params.append(specialization)
            
        if category:
            query += " AND q.category = ?"
            params.append(category)
            
        query += " ORDER BY q.order_position, q.id"
        
        cursor.execute(query, params)
        questions = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return questions
        
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении вопросов из БД: {e}")
        return []

def get_question_by_id(question_id):
    """Получение вопроса по ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.*, p.prompt_template
            FROM Questions q
            LEFT JOIN Prompts p ON q.prompt_id = p.question_id
            WHERE q.question_id = ?
        """, (question_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
        
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении вопроса по ID: {e}")
        return None

def get_question_categories():
    """Получение списка всех категорий вопросов"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as count 
            FROM Questions 
            WHERE category IS NOT NULL AND is_active = 1
            GROUP BY category 
            ORDER BY category
        """)
        
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return categories
        
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении категорий: {e}")
        return []

# Специализации (роли удалены)
SPECIALIZATIONS = [
    {"value": "Аналитик", "label": "Аналитик"},
    {"value": "Тестировщик", "label": "Тестировщик"},
    {"value": "WEB", "label": "WEB"},
    {"value": "Java", "label": "Java"},
    {"value": "Python", "label": "Python"}
]

# Функции для работы с базой данных продолжение


def clear_all_cache():
    """
    Функция для полной очистки всех кешей веб-приложения.
    
    НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
    Очищает cache_dict и cache_by_specialization.
    """
    global cache_dict, cache_by_specialization
    
    try:
        cache_dict_count = len(cache_dict)
        spec_count = len(cache_by_specialization)
        total_questions = sum(len(questions) for questions in cache_by_specialization.values())
        
        # Очищаем основной кеш
        cache_dict.clear()
        
        # Очищаем кеш по специализациям
        cache_by_specialization.clear()
        
        logger.info(f"🧹 ВСЕ КЕШИ ВЕБ-ПРИЛОЖЕНИЯ ОЧИЩЕНЫ: cache_dict({cache_dict_count}) + {spec_count} специализаций({total_questions} вопросов)")
        return cache_dict_count + total_questions
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке кешей веб-приложения: {e}")
        return 0

def clear_cache_for_specialization(specialization):
    """
    Функция для очистки кеша конкретной специализации в веб-приложении.
    
    НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
    Теперь очистка стала очень простой - просто удаляем ключ специализации.
    """
    global cache_by_specialization
    
    try:
        cleared_count = 0
        
        if specialization in cache_by_specialization:
            # Подсчитываем количество вопросов для данной специализации
            cleared_count = len(cache_by_specialization[specialization])
            # Удаляем всю специализацию из кэша
            del cache_by_specialization[specialization]
            logger.info(f"🧹 Очищен кэш веб-приложения для специализации '{specialization}': удалено {cleared_count} вопросов")
        else:
            logger.info(f"✅ Кэш веб-приложения для специализации '{specialization}' уже пуст")
        
        return cleared_count
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке кеша веб-приложения для специализации '{specialization}': {e}")
        return 0

def sync_clear_cache_with_telegram_bot(specialization):
    """
    Синхронизация очистки кеша с телеграм-ботом.
    Отправляет запрос на очистку кеша конкретной специализации в телеграм-боте.
    """
    try:
        # URL для очистки кеша в телеграм-боте
        telegram_bot_url = os.environ.get('TELEGRAM_BOT_CACHE_URL', 'http://127.0.0.1:8007/clear-cache-specialization')
        
        # Отправляем запрос на очистку кеша в телеграм-боте
        response = requests.post(telegram_bot_url, json={'specialization': specialization}, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info(f"Кеш телеграм-бота для специализации '{specialization}' успешно очищен. Очищено записей: {result.get('cleared_count', 0)}")
                return True
            else:
                logger.warning(f"Ошибка при очистке кеша телеграм-бота: {result.get('error', 'неизвестная ошибка')}")
                return False
        else:
            logger.warning(f"Ошибка HTTP при очистке кеша телеграм-бота: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.warning("Не удалось подключиться к телеграм-боту для очистки кеша (возможно, бот не запущен)")
        return False
    except requests.exceptions.Timeout:
        logger.warning("Превышено время ожидания при очистке кеша телеграм-бота")
        return False
    except Exception as e:
        logger.error(f"Ошибка при синхронизации очистки кеша с телеграм-ботом: {e}")
        return False

@app.route('/api/clear-cache', methods=['POST'])
def clear_webapp_cache():
    """Эндпоинт для очистки кеша веб-приложения."""
    try:
        count = clear_all_cache()
        return jsonify({"success": True, "message": f"Кеш веб-приложения успешно очищен, удалено {count} записей."})
    except Exception as e:
        logger.error(f"Ошибка при очистке кеша веб-приложения: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

async def handle_cached_request(question_id, question, user_id, specialization):
    """Обработка кешированного запроса на основе типа вопроса из БД"""
    try:
        cache_type = get_cache_type_for_question(question_id)
        
        if cache_type == 'by_specialization':
            # НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
            if specialization in cache_by_specialization and question_id in cache_by_specialization[specialization]:
                cached_answer_parts = cache_by_specialization[specialization][question_id]
                logger.info(f"✅ Найден кешированный ответ в веб-приложении для specialization='{specialization}', question_id={question_id}")
            else:
                logger.info(f"❌ Кеш не найден в веб-приложении для specialization='{specialization}', question_id={question_id}")
                return None
        else:
            logger.info(f"🚫 Вопрос question_id={question_id} не кешируется (cache_type={cache_type})")
            return None
        
        # Объединяем части ответа (как в телеграм боте)
        if isinstance(cached_answer_parts, list):
            full_cached_answer = "".join(cached_answer_parts)
        else:
            full_cached_answer = str(cached_answer_parts)
        
        # Сохраняем в историю
        save_to_history(user_id, question, full_cached_answer, specialization)
        
        # Генерируем предложенные вопросы для кешированных ответов
        try:
            suggested_questions = []
            if full_cached_answer:
                # Создаем payload для генерации связанных вопросов
                suggestion_payload = {
                    'user_question': question,
                                                'bot_answer': full_cached_answer[:4000],  # Обрезаем как в боте
                    'specialization': specialization
                }
                
                # Отправляем запрос на генерацию связанных вопросов
                suggested_questions = await generate_suggested_questions_async(suggestion_payload)
            
            return {
                "answer": full_cached_answer,
                "suggested_questions": suggested_questions[:3],  # Берем только первые 3
                "cached": True
            }
        except Exception as e:
            logger.warning(f"Ошибка генерации связанных вопросов для кешированного ответа: {e}")
            return {
                "answer": full_cached_answer,
                "suggested_questions": [],
                "cached": True
            }
        
    except Exception as e:
        logger.error(f"Ошибка при работе с кешем: {e}")
        return None

def get_question_id_from_text(question_text):
    """
    УПРОЩЕННАЯ ВЕРСИЯ: Всегда возвращает 888 для свободного ввода
    (как в телеграм боте)
    """
    logger.info(f"Свободный ввод: '{question_text}' -> question_id=888")
    return "888"  # Всегда свободный ввод

def get_dialog_context(user_id, max_messages=12):
    """Получает контекст диалога из последних сообщений пользователя (как в телеграм боте)"""
    try:
        conn = get_db_connection()
        if not conn:
            return "[]"
            
        cursor = conn.cursor()
        cursor.execute(
            """SELECT message, role, time FROM Message_history 
               WHERE user_id = ? 
               ORDER BY time DESC 
               LIMIT ?""",
            (user_id, max_messages)
        )
        
        messages = cursor.fetchall()
        conn.close()
        
        if not messages:
            return "[]"
        
        # Формируем контекст в JSON формате (как в телеграм боте)
        dialogue_context = []
        # Обрабатываем сообщения в обратном порядке (от старых к новым)
        for msg in reversed(messages):
            dialogue_context.append({
                "role": msg["role"],
                "content": msg["message"]
            })
        
        # Ограничиваем контекст до последних 12 сообщений (6 пар: 6 user + 6 assistant)
        if len(dialogue_context) > 12:
            dialogue_context = dialogue_context[-12:]
        
        # Возвращаем в JSON формате (как в телеграм боте)
        return json.dumps(dialogue_context, ensure_ascii=False, indent=4)
        
    except Exception as e:
        logger.error(f"Ошибка получения контекста диалога: {e}")
        return "[]"

async def send_websocket_question(question, user_id, specialization="", question_id=None, vector_store='auto'):
    """Отправка вопроса через WebSocket к RAG-агенту (убран параметр role)"""
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Определяем question_id на основе текста вопроса, если не передан
            if question_id is None:
                question_id = get_question_id_from_text(question)
            
            # Получаем контекст диалога для свободного ввода (id=888)
            context = "[]"
            if int(question_id) == 888:
                context = get_dialog_context(user_id, max_messages=12)
                logger.info(f"Контекст диалога для пользователя {user_id}: {context[:100]}...")
            
            logger.info(f"Отправляем вопрос: '{question}' с question_id: {question_id}, specialization: '{specialization}'")
            logger.info(f"WebSocket URL: {WEBSOCKET_URL}")
            
            # Отправляем данные в том же порядке, что ожидает RAG-сервис (КАК В ТЕЛЕГРАМ БОТЕ)
            await websocket.send(question)          # 1. question
            await websocket.send("")                # 2. role (пустая строка, так как роль не используется)
            await websocket.send(specialization)    # 3. specialization
            await websocket.send(str(question_id))  # 4. question_id
            await websocket.send(context)           # 5. context
            await websocket.send("1")               # 6. count (1 для первого вопроса)
            await websocket.send(vector_store)      # 7. vector_store (ДОБАВЛЕН НЕДОСТАЮЩИЙ ПАРАМЕТР)
            
            # Получаем потоковый ответ (ТОЧНО как в телеграм боте)
            full_answer = ""
            answer_for_cache = []
            answer_for_continue_dialog = ""
            empty_message_count = 0
            max_empty_messages = 10  # Максимум пустых сообщений подряд
            
            try:
                while True:
                    try:
                        # Добавляем таймаут для recv (как в телеграм боте)
                        answer_part = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    except asyncio.TimeoutError:
                        logger.warning("Таймаут ожидания ответа от RAG сервиса")
                        break
                    
                    if answer_part:
                        empty_message_count = 0  # Сбрасываем счетчик пустых сообщений
                        logger.debug(f"Получена часть ответа: '{answer_part[:100]}...' (длина: {len(answer_part)})")
                        
                        # ТОЧНО как в телеграм-боте: просто накапливаем части БЕЗ изменения
                        full_answer += answer_part
                    else:
                        # Пустое сообщение может означать конец потока
                        empty_message_count += 1
                        logger.debug(f"Получено пустое сообщение #{empty_message_count} от WebSocket")
                        
                        # Если получили слишком много пустых сообщений подряд - выходим
                        if empty_message_count >= max_empty_messages:
                            logger.info(f"Получено {empty_message_count} пустых сообщений подряд, завершаем обработку")
                            break
                        
                        # Небольшая пауза и продолжаем (как в телеграм боте)
                        await asyncio.sleep(0.1)
                        continue
                        
            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket соединение закрыто")
                pass  # WebSocket закрылся - это нормально
            
            # После завершения цикла сохраняем весь накопленный ответ
            if full_answer != "":
                # В телеграм-боте answer_for_cache накапливает части по времени
                # Здесь мы сохраняем весь полученный ответ как одну часть
                answer_for_cache = [full_answer]  # Массив с одним элементом - полным ответом
                answer_for_continue_dialog = full_answer
            
            logger.info(f"Получен ответ от RAG сервиса: '{answer_for_continue_dialog[:200]}...' (длина: {len(answer_for_continue_dialog)})")
            logger.info(f"Последние 100 символов ответа: '{answer_for_continue_dialog[-100:]}'")
            logger.info(f"Количество частей в answer_for_cache: {len(answer_for_cache)}")
            
            # Дополнительная диагностика для проблемы с неполными ответами
            if len(answer_for_continue_dialog) < 500:
                logger.warning(f"ВНИМАНИЕ: Короткий ответ! Длина: {len(answer_for_continue_dialog)}")
                logger.warning(f"Полный ответ: '{answer_for_continue_dialog}'")
            
            # Проверяем, заканчивается ли ответ корректно
            if not answer_for_continue_dialog.endswith(('.', '!', '?', ':', ';')):
                logger.warning(f"ВНИМАНИЕ: Ответ может быть обрезан! Последние символы: '{answer_for_continue_dialog[-20:]}'")
            
            # Проверяем наличие ключевых слов из примера
            keywords = ['SDLC', 'Software Development Life Cycle', 'этапы', 'разработки']
            found_keywords = [kw for kw in keywords if kw.lower() in answer_for_continue_dialog.lower()]
            logger.info(f"Найденные ключевые слова: {found_keywords}")
            
            # Кешируем ответы на основе типа вопроса из БД
            if question_id:
                question_id_int = int(question_id)
                cache_type = get_cache_type_for_question(question_id_int)
                
                if cache_type == 'by_specialization':
                    # НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
                    if specialization not in cache_by_specialization:
                        cache_by_specialization[specialization] = {}
                    cache_by_specialization[specialization][question_id_int] = answer_for_cache
                    logger.info(f"💾 Ответ сохранен в кэш веб-приложения: specialization='{specialization}', question_id={question_id_int}, фрагментов={len(answer_for_cache)}")
                elif cache_type == 'no_cache':
                    logger.info(f"🚫 Вопрос question_id={question_id_int} не кешируется (системный вопрос)")
                else:
                    logger.warning(f"⚠️ Неизвестный тип кеша '{cache_type}' для question_id={question_id_int}")
            
            return {
                "answer": answer_for_continue_dialog.strip(),
                "suggested_questions": []
            }
    except Exception as e:
        logger.error(f"Ошибка WebSocket: {e}")
        return {
            "answer": "Извините, сервис временно недоступен. Попробуйте позже.",
            "suggested_questions": []
        }

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Обработка вопроса пользователя с автоматическим определением question_id"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        user_id = data.get('user_id', 'guest')
        specialization = data.get('specialization', '')
        question_id = data.get('question_id', None)
        vector_store = data.get('vector_store', 'auto')
        
        if not question:
            return jsonify({"error": "Вопрос не может быть пустым"}), 400
        
        # Если question_id не передан, пытаемся определить его автоматически
        if not question_id:
            question_id = get_question_id_from_text(question)
            logger.info(f"Автоматически определен question_id={question_id} для вопроса: {question[:50]}...")
        
        # Если question_id определен и это известный вопрос, используем библиотечную логику с кешированием
        if question_id and question_id != "888":
            logger.info(f"Перенаправляем на ask_library для question_id={question_id}")
            
            # ИСПРАВЛЕНО: Определяем правильный vector_store для универсальных вопросов
            question_id_int = int(question_id)
            question_info = get_question_by_id(question_id_int)
            
            if question_info:
                question_text = question_info.get('question_text', '')
                
                # Список универсальных вопросов
                universal_questions = [
                    "матрица компетенций", "компетенц", "развиваться", "обратная связь",
                    "лучшие практики", "sdlc", "тайм-менеджмент", "agile", "взаимодействовать"
                ]
                
                is_universal = any(keyword in question_text.lower() for keyword in universal_questions)
                
                if is_universal:
                    vector_store = "by_specialization"
                    logger.info(f"Универсальный вопрос при ручном вводе '{question_text}' - используем by_specialization для {specialization}")
                elif vector_store == 'auto' and question_info.get('vector_store'):
                    vector_store = question_info['vector_store']
            
            # Проверяем кеш сначала
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            cached_result = loop.run_until_complete(
                handle_cached_request(question_id_int, question, user_id, specialization)
            )
            
            if cached_result:
                logger.info(f"Возвращаем кешированный ответ для question_id={question_id_int}")
                loop.close()
                save_to_history(user_id, question, cached_result.get('answer', ''), specialization)
                return jsonify(cached_result)
            
            # Если в кеше нет, отправляем запрос к RAG сервису
            logger.info(f"Ручной ввод: отправляем в RAG с question_id={question_id} и vector_store={vector_store}")
            result = loop.run_until_complete(
                send_websocket_question(question, user_id, specialization, question_id, vector_store)
            )
            loop.close()
            
            # Генерируем предложенные вопросы для библиотечных вопросов
            try:
                if result.get('answer'):
                    suggestion_payload = {
                        'user_question': question,
                        'bot_answer': result['answer'][:4000],
                        'specialization': specialization
                    }
                    
                    suggestion_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(suggestion_loop)
                    
                    try:
                        suggested_questions = suggestion_loop.run_until_complete(
                            generate_suggested_questions_async(suggestion_payload)
                        )
                        result['suggested_questions'] = suggested_questions[:3]
                    except Exception as e:
                        logger.warning(f"Не удалось сгенерировать связанные вопросы: {e}")
                        result['suggested_questions'] = []
                    finally:
                        suggestion_loop.close()
            except Exception as e:
                logger.warning(f"Ошибка генерации связанных вопросов: {e}")
                result['suggested_questions'] = []
        else:
            # Для свободного ввода используем обычную логику
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                send_websocket_question(question, user_id, specialization, "888", vector_store)  # 888 для свободного ввода
            )
            loop.close()
        
        # Сохраняем в историю
        save_to_history(user_id, question, result.get('answer', ''), specialization)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка обработки вопроса: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.route('/api/ask_library', methods=['POST'])
def ask_library_question():
    """Обработка вопроса из библиотеки с кешированием (аналогично Telegram боту)"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        user_id = data.get('user_id', 'guest')
        specialization = data.get('specialization', '')
        question_id = data.get('question_id', None)
        vector_store = data.get('vector_store', 'auto')  # Добавляем поддержку vector_store
        
        if not question:
            return jsonify({"error": "Вопрос не может быть пустым"}), 400
        
        if not question_id:
            return jsonify({"error": "Для библиотечных вопросов обязателен question_id"}), 400
        
        question_id_int = int(question_id)
        
        # ИСПРАВЛЕНО: Определяем vector_store для универсальных вопросов
        question_info = get_question_by_id(question_id_int)
        if question_info:
            question_text = question_info.get('question_text', '')
            
            # Список универсальных вопросов, которые должны адаптироваться под специализацию пользователя
            universal_questions = [
                "матрица компетенций", "компетенц", "развиваться", "обратная связь",
                "лучшие практики", "sdlc", "тайм-менеджмент", "agile", "взаимодействовать"
            ]
            
            is_universal = any(keyword in question_text.lower() for keyword in universal_questions)
            
            if is_universal:
                # Для универсальных вопросов используем специализацию пользователя
                vector_store = "by_specialization"
                logger.info(f"Универсальный вопрос '{question_text}' - используем by_specialization для {specialization}")
            elif vector_store == 'auto' and question_info.get('vector_store'):
                # Для специфических вопросов используем настройку из базы
                vector_store = question_info['vector_store']
                logger.info(f"Специфический вопрос - используем vector_store из БД: {vector_store} для question_id={question_id_int}")
        
        # Fallback если ничего не определилось
        if vector_store == 'auto':
            vector_store = 'by_specialization'
        
        # Проверяем кеш сначала (аналогично Telegram боту)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        cached_result = loop.run_until_complete(
            handle_cached_request(question_id_int, question, user_id, specialization)
        )
        
        if cached_result:
            logger.info(f"Возвращаем кешированный ответ для question_id={question_id_int}")
            loop.close()
            return jsonify(cached_result)
        
        # Если в кеше нет, отправляем запрос к RAG сервису
        logger.info(f"Кеш не найден, отправляем запрос к RAG сервису для question_id={question_id_int} с vector_store={vector_store}")
        result = loop.run_until_complete(
            send_websocket_question(question, user_id, specialization, question_id, vector_store)
        )
        loop.close()
        
        # Сохраняем в историю
        save_to_history(user_id, question, result.get('answer', ''), specialization)
        
        # Генерируем предложенные вопросы для библиотечных вопросов (аналогично Telegram боту)
        try:
            suggested_questions = []
            if result.get('answer'):
                # Создаем payload для генерации связанных вопросов
                suggestion_payload = {
                    'user_question': question,
                    'bot_answer': result['answer'][:4000],  # Обрезаем как в боте
                    'specialization': specialization
                }
                
                # Отправляем запрос на генерацию связанных вопросов
                suggestion_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(suggestion_loop)
                
                try:
                    suggested_questions = suggestion_loop.run_until_complete(
                        generate_suggested_questions_async(suggestion_payload)
                    )
                except Exception as e:
                    logger.warning(f"Не удалось сгенерировать связанные вопросы: {e}")
                    suggested_questions = []
                finally:
                    suggestion_loop.close()
            
            # Добавляем связанные вопросы к результату
            result['suggested_questions'] = suggested_questions[:3]  # Берем только первые 3
            
        except Exception as e:
            logger.warning(f"Ошибка генерации связанных вопросов: {e}")
            result['suggested_questions'] = []
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка обработки библиотечного вопроса: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """Получение списка вопросов из базы данных с фильтрацией"""
    specialization = request.args.get('specialization')
    category = request.args.get('category')
    
    logger.info(f"Запрос вопросов для специализации: {specialization}, категории: {category}")
    
    try:
        # Получаем вопросы из базы данных
        questions = get_questions_from_db(specialization=specialization, category=category)
        
        # Преобразуем в формат, ожидаемый фронтендом
        formatted_questions = []
        for q in questions:
            formatted_question = {
                'id': q['question_id'],
                'text': q['question_text'],
                'title': q['question_text'][:50] + '...' if len(q['question_text']) > 50 else q['question_text'],
                'category': q['category'] or 'general',
                'specialization': q['specialization'],
                'vector_store': q['vector_store'],
                'prompt_id': q['prompt_id'],  # ИСПРАВЛЕНО: Добавляем prompt_id для фронтенда
                'callback_data': q['callback_data'],
                'preview': q['question_text'][:120] + '...' if len(q['question_text']) > 120 else q['question_text']
            }
            formatted_questions.append(formatted_question)
        
        logger.info(f"Найдено {len(formatted_questions)} вопросов")
        return jsonify(formatted_questions)
        
    except Exception as e:
        logger.error(f"Ошибка при получении вопросов: {e}")
        # Fallback к пустому списку если БД недоступна
        logger.warning("БД недоступна, возвращаем пустой список вопросов")
        return jsonify([])

@app.route('/api/questions/categories', methods=['GET'])
def get_categories():
    """Получение списка категорий вопросов"""
    try:
        categories = get_question_categories()
        return jsonify(categories)
    except Exception as e:
        logger.error(f"Ошибка при получении категорий: {e}")
        return jsonify([])

# API endpoint для ролей удален, так как роли больше не используются

@app.route('/api/specializations', methods=['GET'])
def get_specializations():
    """Получение списка специализаций"""
    try:
        return jsonify(SPECIALIZATIONS)
    except Exception as e:
        logger.error(f"Ошибка получения специализаций: {e}")
        return jsonify({"error": "Ошибка получения специализаций"}), 500

@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    """Получение профиля пользователя (убрана роль)"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Ошибка подключения к БД"}), 500
            
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Specialization, reminder, is_onboarding FROM Users WHERE user_id = ?",
            (user_id,)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                "specialization": user["Specialization"] or "",
                "reminder_enabled": bool(user["reminder"]) if user["reminder"] is not None else True,
                "is_onboarding": int(user["is_onboarding"]) if user["is_onboarding"] is not None else 0
            })
        else:
            # Пользователь не найден
            return jsonify({
                "specialization": "",
                "reminder_enabled": True,
                "is_onboarding": 0
            }), 404
            
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {e}")
        return jsonify({"error": "Ошибка получения профиля"}), 500

@app.route('/api/profile/<user_id>', methods=['POST'])
def save_profile(user_id):
    """Сохранение профиля пользователя"""
    try:
        data = request.get_json()
        logger.info(f"Получен запрос на сохранение профиля для user_id: {user_id}")
        logger.info(f"Данные: {data}")
        
        if not data:
            return jsonify({'error': 'Отсутствуют данные для сохранения'}), 400
            
        # Получаем данные из запроса
        new_specialization = data.get('specialization', '')
        reminder_enabled = data.get('reminder_enabled', True)
        is_onboarding = data.get('is_onboarding', None)
        
        if not new_specialization:
            return jsonify({'error': 'Специализация обязательна'}), 400
        
        # Больше не используем previousSpecialization - кеш не очищается
        
        # Сохраняем новые данные в БД
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Ошибка подключения к базе данных'}), 500
            
        cursor = conn.cursor()
        
        # Проверяем существование пользователя
        cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (user_id,))
        current_user = cursor.fetchone()
        
        # Обновляем или создаем запись пользователя
        if current_user:
            # Обновляем существующего пользователя
            if is_onboarding is not None:
                cursor.execute("""
                    UPDATE Users 
                    SET Specialization = ?, reminder = ?, is_onboarding = ?
                    WHERE user_id = ?
                """, (new_specialization, reminder_enabled, is_onboarding, user_id))
            else:
                cursor.execute("""
                    UPDATE Users 
                    SET Specialization = ?, reminder = ?
                    WHERE user_id = ?
                """, (new_specialization, reminder_enabled, user_id))
        else:
            # Создаем нового пользователя
            cursor.execute("""
                INSERT INTO Users (user_id, Specialization, reminder, create_time, is_onboarding)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, new_specialization, reminder_enabled, datetime.now(), is_onboarding if is_onboarding is not None else 1))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Профиль пользователя {user_id} успешно сохранен")
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Ошибка сохранения профиля: {e}")
        return jsonify({'error': 'Ошибка сохранения профиля'}), 500

@app.route('/api/profile/<user_id>/reminder', methods=['GET'])
def get_reminder_settings(user_id):
    """Получение настроек регулярных сообщений"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Ошибка подключения к базе данных'}), 500
            
        cursor = conn.cursor()
        cursor.execute("SELECT reminder FROM Users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            reminder_enabled = bool(result[0])
        else:
            reminder_enabled = True  # По умолчанию включено
            
        return jsonify({
            'reminder_enabled': reminder_enabled,
            'schedule': {
                'day': 'Пятница',
                'time': '19:00',
                'timezone': 'Москва (UTC+3)'
            },
            'description': 'Регулярные сообщения - это еженедельные персональные отчеты от ИИ-агента с анализом вашей активности и развития компетенций.'
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении настроек напоминаний: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500

@app.route('/api/profile/<user_id>/reminder', methods=['POST'])
def update_reminder_settings(user_id):
    """Обновление настроек регулярных сообщений"""
    try:
        data = request.get_json()
        logger.info(f"Получен запрос на обновление настроек напоминаний для user_id: {user_id}")
        logger.info(f"Данные: {data}")
        
        if not data:
            return jsonify({'error': 'Отсутствуют данные для обновления'}), 400
            
        reminder_enabled = data.get('reminder_enabled', True)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Ошибка подключения к базе данных'}), 500
            
        cursor = conn.cursor()
        
        # Проверяем существование пользователя
        cursor.execute("SELECT user_id FROM Users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            # Создаем пользователя если его нет
            cursor.execute("""
                INSERT INTO Users (user_id, reminder, Specialization, create_time, is_onboarding)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, reminder_enabled, 'Не указана', datetime.now(), False))
        else:
            # Обновляем существующего пользователя
            cursor.execute("""
                UPDATE Users SET reminder = ?
                WHERE user_id = ?
            """, (reminder_enabled, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Настройки напоминаний для пользователя {user_id} обновлены: {reminder_enabled}")
        return jsonify({
            'success': True,
            'message': f"Регулярные сообщения {'включены' if reminder_enabled else 'отключены'}",
            'reminder_enabled': reminder_enabled
        })
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении настроек напоминаний: {e}")
        return jsonify({'error': 'Ошибка сервера'}), 500

@app.route('/api/history/<user_id>', methods=['GET'])
def get_history(user_id):
    """Получение истории диалогов пользователя"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Ошибка подключения к БД"}), 500
            
        cursor = conn.cursor()
        cursor.execute(
            """SELECT message, role, time FROM Message_history 
               WHERE user_id = ? 
               ORDER BY time ASC 
               LIMIT 100""",
            (user_id,)
        )
        
        messages = cursor.fetchall()
        conn.close()
        
        # Группируем сообщения в пары (user -> assistant)
        history = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            if msg["role"] == "user":
                question = msg["message"]
                timestamp = msg["time"]
                answer = ""
                # Ищем ближайший следующий ответ ассистента
                j = i + 1
                while j < len(messages):
                    next_msg = messages[j]
                    if next_msg["role"] == "assistant":
                        answer = next_msg["message"]
                        break
                    j += 1
                history.append({
                    "id": len(history),
                    "question": question,
                    "answer": answer,
                    "timestamp": timestamp,
                    "role": "user",
                    "specialization": ""
                })
            i += 1
        
        # Сортируем историю по времени в обратном порядке (новые сверху)
        history.reverse()
        return jsonify(history)
        
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        return jsonify({"error": "Ошибка получения истории"}), 500

@app.route('/api/history/<user_id>', methods=['DELETE'])
def clear_history(user_id):
    """Очистка истории диалогов пользователя"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Ошибка подключения к БД"}), 500
            
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Message_history WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Ошибка очистки истории: {e}")
        return jsonify({"error": "Ошибка очистки истории"}), 500

def save_to_history(user_id, question, answer, specialization=""):
    """Сохранение диалога в историю"""
    try:
        conn = get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        # Сохраняем вопрос пользователя
        cursor.execute(
            "INSERT INTO Message_history (user_id, role, message, time) VALUES (?, ?, ?, ?)",
            (user_id, "user", question, datetime.now())
        )
        
        # Сохраняем ответ ассистента
        cursor.execute(
            "INSERT INTO Message_history (user_id, role, message, time) VALUES (?, ?, ?, ?)",
            (user_id, "assistant", answer, datetime.now())
        )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Ошибка сохранения в историю: {e}")

async def generate_suggested_questions_async(payload):
    """Асинхронная генерация связанных вопросов через WebSocket"""
    try:
        uri = "ws://127.0.0.1:8000/ws_suggest"
        async with websockets.connect(uri, timeout=10) as websocket:
            # Отправляем payload
            await websocket.send(json.dumps(payload))
            
            # Получаем ответ
            response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
            questions = json.loads(response)
            
            if isinstance(questions, list):
                return questions
            else:
                logger.warning(f"Неожиданный формат ответа: {questions}")
                return []
                
    except Exception as e:
        logger.warning(f"Ошибка генерации связанных вопросов через WebSocket: {e}")
        return []

@app.route('/api/suggest_questions', methods=['POST'])
def suggest_questions():
    """Fallback endpoint для генерации связанных вопросов через HTTP"""
    try:
        data = request.get_json()
        
        user_question = data.get('user_question', '')
        bot_answer = data.get('bot_answer', '')
        specialization = data.get('specialization', 'Не указана')
        
        logger.info(f"HTTP suggest_questions: получен запрос для специализации {specialization}")
        
        # Попробуем подключиться к RAG сервису через WebSocket
        
        async def get_suggestions():
            try:
                uri = "ws://127.0.0.1:8000/ws_suggest"
                async with websockets.connect(uri, timeout=10) as websocket:
                    payload = {
                        "user_question": user_question,
                        "bot_answer": bot_answer,
                        "specialization": specialization
                    }
                    
                    await websocket.send(json.dumps(payload))
                    response = await websocket.recv()
                    questions = json.loads(response)
                    
                    if isinstance(questions, list):
                        return questions
                    else:
                        return []
                        
            except Exception as e:
                logger.error(f"Ошибка при получении вопросов через WebSocket: {e}")
                return []
        
        # Запускаем асинхронную функцию
        try:
            questions = asyncio.run(get_suggestions())
            logger.info(f"HTTP suggest_questions: получены вопросы: {questions}")
            return jsonify(questions)
        except Exception as e:
            logger.error(f"Ошибка в асинхронном вызове: {e}")
            # Возвращаем заглушку с базовыми вопросами
            fallback_questions = [
                "Можете подробнее рассказать об этом?",
                "Какие есть альтернативные подходы?",
                "С какими трудностями можно столкнуться?"
            ]
            return jsonify(fallback_questions)
            
    except Exception as e:
        logger.error(f"Ошибка в suggest_questions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })



@app.route('/api/test', methods=['GET', 'POST'])
def test_endpoint():
    """Тестовый endpoint для проверки связи"""
    logger.info(f"Тест запрос: {request.method} {request.url}")
    if request.method == 'POST':
        data = request.get_json()
        logger.info(f"Тест данные: {data}")
        return jsonify({"message": "POST тест успешен", "received_data": data})
    return jsonify({"message": "GET тест успешен"})

@app.route('/api/feedback', methods=['POST'])
def send_feedback():
    """Отправка обратной связи"""
    try:
        # Логируем входящий запрос
        logger.info(f"Получен запрос обратной связи: {request.method} {request.url}")
        logger.info(f"Content-Type: {request.content_type}")
        
        data = request.get_json()
        logger.info(f"Полученные данные: {data}")
        
        if not data:
            logger.error("Не получены JSON данные")
            return jsonify({"error": "Неверный формат данных"}), 400
        
        feedback = data.get('feedback', '').strip()
        user_id = data.get('user_id', 'guest')
        user_name = data.get('user_name', 'Пользователь')
        username = data.get('username', 'не указан')
        specialization = data.get('specialization', 'Не указана')
        
        # Детальная проверка каждого поля
        logger.info(f"Детальный анализ данных:")
        logger.info(f"  - feedback: '{feedback}' (длина: {len(feedback)})")
        logger.info(f"  - user_id: '{user_id}' (тип: {type(user_id)})")
        logger.info(f"  - user_name: '{user_name}' (тип: {type(user_name)})")
        logger.info(f"  - username: '{username}' (тип: {type(username)})")
        logger.info(f"  - specialization: '{specialization}' (тип: {type(specialization)})")
        
        # Проверяем на проблемные символы
        if feedback:
            try:
                # Проверяем, можно ли закодировать в UTF-8
                feedback.encode('utf-8')
                logger.info("Отзыв успешно кодируется в UTF-8")
            except UnicodeEncodeError as e:
                logger.error(f"Проблема с кодировкой отзыва: {e}")
                return jsonify({"error": "Некорректные символы в отзыве"}), 400
        
        if not feedback:
            logger.error("Пустой отзыв")
            return jsonify({"error": "Отзыв не может быть пустым"}), 400
            
        # Дополнительные проверки
        if len(feedback) > 10000:
            logger.error(f"Слишком длинный отзыв: {len(feedback)} символов")
            return jsonify({"error": "Отзыв слишком длинный (максимум 10000 символов)"}), 400
        
        # Безопасно формируем текст сообщения
        try:
            # Экранируем специальные символы Markdown
            safe_user_name = str(user_name).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            safe_username = str(username).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            safe_specialization = str(specialization).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            safe_feedback = str(feedback).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            
            feedback_text = (
                f"📨 *Новый отзыв от пользователя (WebApp):*\n"
                f"👤 *Имя:* {safe_user_name}\n"
                f"📍 *Username:* @{safe_username}\n"
                f"🆔 *User ID:* {user_id}\n"
                f"🎯 *Специализация:* {safe_specialization}\n"
                f"📝 *Отзыв:* {safe_feedback}"
            )
            
            logger.info(f"Сформированный текст сообщения (первые 200 символов): {feedback_text[:200]}...")
            
        except Exception as e:
            logger.error(f"Ошибка формирования текста сообщения: {e}")
            return jsonify({"error": "Ошибка обработки данных"}), 400
        
        # Отправляем через Telegram бот (используем те же переменные окружения)
        FEEDBACK_BOT_TOKEN = os.getenv("FEEDBACK_BOT_TOKEN")
        FEEDBACK_CHAT_ID = os.getenv("FEEDBACK_CHAT_ID")
        
        logger.info(f"Переменные окружения: BOT_TOKEN={'установлен' if FEEDBACK_BOT_TOKEN else 'не установлен'}, CHAT_ID={'установлен' if FEEDBACK_CHAT_ID else 'не установлен'}")
        
        if FEEDBACK_BOT_TOKEN and FEEDBACK_CHAT_ID:
            try:
                telegram_api_url = f"https://api.telegram.org/bot{FEEDBACK_BOT_TOKEN}/sendMessage"
                
                telegram_data = {
                    "chat_id": FEEDBACK_CHAT_ID,
                    "text": feedback_text,
                    "parse_mode": "Markdown"
                }
                
                logger.info(f"Отправляем запрос в Telegram API: {telegram_api_url}")
                response = requests.post(telegram_api_url, json=telegram_data, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"Обратная связь отправлена успешно от пользователя {user_id}")
                    return jsonify({"success": True, "message": "Отзыв отправлен успешно"})
                else:
                    logger.error(f"Ошибка отправки в Telegram: {response.status_code} - {response.text}")
                    return jsonify({"error": f"Ошибка отправки отзыва: {response.status_code}"}), 500
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка сетевого запроса к Telegram API: {e}")
                return jsonify({"error": "Ошибка подключения к сервису обратной связи"}), 500
        else:
            missing = []
            if not FEEDBACK_BOT_TOKEN:
                missing.append("FEEDBACK_BOT_TOKEN")
            if not FEEDBACK_CHAT_ID:
                missing.append("FEEDBACK_CHAT_ID")
            logger.error(f"Не настроены переменные окружения: {', '.join(missing)}")
            return jsonify({"error": "Сервис обратной связи временно недоступен"}), 500
        
    except Exception as e:
        logger.error(f"Ошибка обработки обратной связи: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Метод не найден"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Внутренняя ошибка сервера"}), 500

if __name__ == '__main__':
    # Для продакшена отключаем debug
    app.run(debug=False, host='0.0.0.0', port=5000) 
