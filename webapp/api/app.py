from flask import Flask, request, jsonify
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
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавляем путь к основному проекту
sys.path.append('/var/www/html/src/main_version')

app = Flask(__name__)
CORS(app)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
DATABASE_URL = "/home/user1/sqlite_data_rag/AI_agent.db"
WEBSOCKET_URL = "ws://213.171.25.85:8000/ws"

# Кеш для ответов (аналогично Telegram боту)
cache_dict = {}
cache_by_specialization = {}

# Роли и специализации (синхронизированы с телеграм ботом)
ROLES = [
    {"value": "PO/PM", "label": "PO/PM"},
    {"value": "Лид компетенции", "label": "Лид компетенции"},
    {"value": "Специалист", "label": "Специалист"},
    {"value": "Стажер", "label": "Стажер"}
]

SPECIALIZATIONS = [
    {"value": "Аналитик", "label": "Аналитик"},
    {"value": "Тестировщик", "label": "Тестировщик"},
    {"value": "WEB", "label": "WEB"},
    {"value": "Java", "label": "Java"},
    {"value": "Python", "label": "Python"}
]

# Предопределенные вопросы для библиотеки (синхронизированы с телеграм ботом)
QUESTIONS_BY_ROLE = {
    "PO/PM": [
        {
            "id": "15",
            "title": "Что я могу ожидать от специалиста",
            "category": "Взаимодействие",
            "preview": "Ожидания от работы со специалистами команды",
            "text": "Что я могу ожидать от специалиста"
        },
        {
            "id": "16", 
            "title": "Что я могу ожидать от лида компетенции",
            "category": "Взаимодействие",
            "preview": "Ожидания от работы с лидами компетенций",
            "text": "Что я могу ожидать от лида компетенции"
        },
        {
            "id": "17",
            "title": "Что ожидается от меня",
            "category": "Обязанности",
            "preview": "Обязанности и ожидания от роли PO/PM",
            "text": "Что ожидается от меня"
        },
        {
            "id": "777",
            "title": "Что еще ты умеешь?",
            "category": "Дополнительно",
            "preview": "Дополнительные возможности и функции системы",
            "text": "Что еще ты умеешь?"
        }
    ],
    "Лид компетенции": {
        "Аналитик": [
            {
                "id": "4",
                "title": "Что я могу ожидать от специалиста",
                "category": "Взаимодействие",
                "preview": "Ожидания от работы со специалистами",
                "text": "Что я могу ожидать от специалиста"
            },
            {
                "id": "5",
                "title": "Что я могу ожидать от своего PO/PM",
                "category": "Взаимодействие",
                "preview": "Ожидания от работы с PO/PM",
                "text": "Что я могу ожидать от своего PO/PM"
            },
            {
                "id": "6",
                "title": "Поиск кандидатов на работу",
                "category": "Обязанности",
                "preview": "Что ожидается от лида при поиске кандидатов",
                "text": "Что ожидается от лида компетенции аналитики при поиске кандидатов на работу?"
            },
            {
                "id": "7",
                "title": "Проведение собеседований",
                "category": "Обязанности",
                "preview": "Что ожидается от лида при собеседованиях",
                "text": "Что ожидается от лида компетенции аналитики при проведении собеседований?"
            },
            {
                "id": "8",
                "title": "Работа со стажерами/джунами",
                "category": "Обязанности",
                "preview": "Что ожидается от лида при работе со стажерами",
                "text": "Что ожидается от лида компетенции аналитики при работе со стажерами и джунами?"
            },
            {
                "id": "9",
                "title": "Проведение 1-2-1",
                "category": "Обязанности",
                "preview": "Что ожидается от лида при проведении 1-2-1",
                "text": "Что ожидается от лида компетенции при проведение 1-2-1?"
            },
            {
                "id": "10",
                "title": "Проведение встреч компетенции",
                "category": "Обязанности",
                "preview": "Что ожидается от лида при встречах компетенции",
                "text": "Что ожидается от лида компетенции при проведение встречи компетенции?"
            },
            {
                "id": "11",
                "title": "Построение структуры компетенции",
                "category": "Дополнительно",
                "preview": "Построение структуры компетенции",
                "text": "Что ожидается от лида компетенции при построение структуры компетенции?"
            },
            {
                "id": "12",
                "title": "Создание ИПР",
                "category": "Дополнительно",
                "preview": "Создание индивидуального плана развития",
                "text": "Что ожидается от лида компетенции при создании ИПР?"
            },
            {
                "id": "13",
                "title": "Как провести онбординг",
                "category": "Дополнительно",
                "preview": "Онбординг нового сотрудника",
                "text": "Как лид компетенции аналитики должен проводить онбординг нового сотрудника?"
            },
            {
                "id": "14",
                "title": "Оптимизация процессов разработки",
                "category": "Дополнительно",
                "preview": "Оптимизация процессов разработки",
                "text": "Как лид компетенции аналитики должен оптимизировать процессы разработки?"
            }
        ],
        "default": [
            {
                "id": "18",
                "title": "Что я могу ожидать от специалиста",
                "category": "Взаимодействие",
                "preview": "Ожидания от работы со специалистами",
                "text": "Что я могу ожидать от специалиста"
            },
            {
                "id": "19", 
                "title": "Что я могу ожидать от своего PO/PM",
                "category": "Взаимодействие",
                "preview": "Ожидания от работы с PO/PM",
                "text": "Что я могу ожидать от своего PO/PM"
            },
            {
                "id": "20",
                "title": "Что ожидается от меня",
                "category": "Обязанности",
                "preview": "Обязанности лида компетенции",
                "text": "Что ожидается от меня"
            },
            {
                "id": "11",
                "title": "Построение структуры компетенции",
                "category": "Дополнительно",
                "preview": "Построение структуры компетенции",
                "text": "Что ожидается от лида компетенции при построение структуры компетенции?"
            },
            {
                "id": "12",
                "title": "Создание ИПР",
                "category": "Дополнительно",
                "preview": "Создание индивидуального плана развития",
                "text": "Что ожидается от лида компетенции при создании ИПР?"
            },
            {
                "id": "13",
                "title": "Как провести онбординг",
                "category": "Дополнительно",
                "preview": "Онбординг нового сотрудника",
                "text": "Как лид компетенции аналитики должен проводить онбординг нового сотрудника?"
            },
            {
                "id": "14",
                "title": "Оптимизация процессов разработки",
                "category": "Дополнительно",
                "preview": "Оптимизация процессов разработки",
                "text": "Как лид компетенции аналитики должен оптимизировать процессы разработки?"
            },
            {
                "id": "24",
                "title": "Советы по тайм-менеджменту",
                "category": "Дополнительно",
                "preview": "Советы по тайм-менеджменту",
                "text": "Советы по тайм-менеджменту для стажеров"
            }
        ]
    },
    "Стажер": [
        {
            "id": "1",
            "title": "Что я могу ожидать от PO/PM",
            "category": "Взаимодействие",
            "preview": "Ожидания от работы с PO/PM",
            "text": "Что я могу ожидать от PO/PM"
        },
        {
            "id": "2",
            "title": "Что я могу ожидать от своего лида",
            "category": "Взаимодействие",
            "preview": "Ожидания от работы с лидом команды",
            "text": "Что я могу ожидать от своего лида"
        },
        {
            "id": "21",
            "title": "Рекомендации для стажеров",
            "category": "Развитие",
            "preview": "Полезные советы для стажеров",
            "text": "Рекомендации для стажеров"
        },
        {
            "id": "3",
            "title": "Посмотреть матрицу компетенций",
            "category": "Развитие",
            "preview": "Матрица навыков и компетенций",
            "text": "Посмотреть матрицу компетенций"
        },
        {
            "id": "22",
            "title": "Лучшие практики",
            "category": "Прочее",
            "preview": "Лучшие практики для стажеров",
            "text": "Лучшие практики для стажеров"
        },
        {
            "id": "23",
            "title": "Что такое SDLC",
            "category": "Прочее",
            "preview": "Жизненный цикл разработки программного обеспечения",
            "text": "Что такое SDLC"
        },
        {
            "id": "24",
            "title": "Советы по тайм-менеджменту",
            "category": "Прочее",
            "preview": "Советы по тайм-менеджменту для стажеров",
            "text": "Советы по тайм-менеджменту для стажеров"
        }
    ],
    "Специалист": [
        {
            "id": "1", 
            "title": "Что я могу ожидать от своего PO/PM",
            "category": "Взаимодействие",
            "preview": "Ожидания от работы с PO/PM",
            "text": "Что я могу ожидать от своего PO/PM"
        },
        {
            "id": "2",
            "title": "Что я могу ожидать от своего Лида",
            "category": "Взаимодействие",
            "preview": "Ожидания от работы с лидом команды",
            "text": "Что я могу ожидать от своего Лида"
        },
        {
            "id": "3",
            "title": "Посмотреть матрицу компетенций",
            "category": "Развитие",
            "preview": "Матрица навыков и компетенций",
            "text": "Посмотреть матрицу компетенций"
        },
        {
            "id": "22",
            "title": "Лучшие практики",
            "category": "Прочее",
            "preview": "Лучшие практики для специалистов",
            "text": "Лучшие практики для стажеров"
        },
        {
            "id": "23",
            "title": "Что такое SDLC",
            "category": "Прочее",
            "preview": "Жизненный цикл разработки программного обеспечения",
            "text": "Что такое SDLC"
        },
        {
            "id": "24",
            "title": "Советы по тайм-менеджменту",
            "category": "Прочее",
            "preview": "Советы по тайм-менеджменту для специалистов",
            "text": "Советы по тайм-менеджменту для стажеров"
        }
    ]
}

def get_db_connection():
    """Получение соединения с базой данных"""
    try:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return None

def clear_all_cache():
    """Функция для полной очистки всех кешей (аналогично Telegram боту)"""
    global cache_dict, cache_by_specialization
    
    try:
        cache_dict.clear()
        cache_by_specialization.clear()
        logger.info("Все кеши успешно очищены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке кешей: {e}")
        return False

async def handle_cached_request(question_id, question, user_id, role, specialization):
    """Обработка кешированного запроса (аналогично Telegram боту)"""
    try:
        if question_id in cache_dict:
            # Используем общий кеш
            cached_answer = cache_dict[question_id]
            logger.info(f"Найден ответ в общем кеше для question_id={question_id}")
        elif question_id in cache_by_specialization and specialization in cache_by_specialization[question_id]:
            # Используем кеш по специализации
            cached_answer = cache_by_specialization[question_id][specialization]
            logger.info(f"Найден ответ в кеше по специализации для question_id={question_id}, specialization={specialization}")
        else:
            return None
        
        # Сохраняем в историю
        save_to_history(user_id, question, cached_answer, role, specialization)
        
        return {
            "answer": cached_answer,
            "suggested_questions": [],
            "cached": True
        }
        
    except Exception as e:
        logger.error(f"Ошибка при работе с кешем: {e}")
        return None

def get_question_id_from_text(question_text):
    """Получает question_id на основе текста вопроса из телеграм бота"""
    # ТОЧНОЕ соответствие с телеграм ботом
    question_mapping = {
        # Основные вопросы из телеграм бота
        "Что я могу ожидать от своего PO/PM?": "1",  # question_1
        "Что я могу ожидать от своего Лида?": "2",   # question_2  
        "Посмотерть матрицу компетенций": "3",       # question_3 (с опечаткой как в боте)
        "Что я могу ожидать от специалиста ": "4",   # question_4 (с пробелом как в боте)
        "Что я могу ожидать от своего PO/PM ": "5",  # question_5 (с пробелом как в боте)
        "Что я могу ожидать от специалиста ?": "18", # question_18 (с пробелом и ? как в боте)
        "Что ожидается от меня?": "20",              # question_20
        "Рекомендации для стажеров": "21",           # question_21
        
        # Дополнительные вопросы для стажеров (группа intern_questions_group)
        "Лучшие практики для стажеров": "22",        # intern_group_question_1
        "Что такое SDLC": "23",                      # intern_group_question_2
        "Советы по тайм-менеджменту для стажеров": "24", # intern_group_question_3
        
        # Специальные вопросы
        "Что еще ты умеешь?": "777",                 # question_777
        
        # Альтернативные варианты для веб-приложения (без опечаток)
        "Что я могу ожидать от своего PO/PM": "1",
        "Что я могу ожидать от своего Лида": "2", 
        "Посмотреть матрицу компетенций": "3",
        "Что я могу ожидать от специалиста": "4",
        "Что я могу ожидать от лида компетенции": "2",
        "Что ожидается от меня": "20"
    }
    
    return question_mapping.get(question_text, "888")  # 888 для свободного ввода

def get_dialog_context(user_id, max_messages=6):
    """Получает контекст диалога из последних сообщений пользователя"""
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
        
        # Формируем контекст в формате: "Пользователь: вопрос\nАссистент: ответ"
        context_parts = []
        # Обрабатываем сообщения в обратном порядке (от старых к новым)
        for msg in reversed(messages):
            if msg["role"] == "user":
                context_parts.append(f"Пользователь: {msg['message']}")
            elif msg["role"] == "assistant":
                context_parts.append(f"Ассистент: {msg['message']}")
        
        # Ограничиваем длину контекста (максимум 1500 символов)
        context_text = "\n".join(context_parts)
        if len(context_text) > 1500:
            context_text = context_text[:1500] + "..."
        
        return context_text if context_text else "[]"
        
    except Exception as e:
        logger.error(f"Ошибка получения контекста диалога: {e}")
        return "[]"

async def send_websocket_question(question, user_id, role="", specialization="", question_id=None):
    """Отправка вопроса через WebSocket к RAG-агенту"""
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Определяем question_id на основе текста вопроса, если не передан
            if question_id is None:
                question_id = get_question_id_from_text(question)
            
            # Получаем контекст диалога для свободного ввода (id=888)
            context = "[]"
            if int(question_id) == 888:
                context = get_dialog_context(user_id, max_messages=6)
                logger.info(f"Контекст диалога для пользователя {user_id}: {context[:100]}...")
            
            logger.info(f"Отправляем вопрос: '{question}' с question_id: {question_id}, role: '{role}', specialization: '{specialization}'")
            
            # Отправляем данные в том же порядке, что ожидает RAG-сервис
            await websocket.send(question)          # 1. question
            await websocket.send(role)              # 2. role  
            await websocket.send(specialization)    # 3. specialization
            await websocket.send(str(question_id))  # 4. question_id
            await websocket.send(context)           # 5. context (теперь с реальным контекстом для id=888)
            await websocket.send("1")               # 6. count (1 для первого вопроса)
            
            # Получаем потоковый ответ
            full_answer = ""
            empty_count = 0
            max_empty = 10  # Максимум пустых chunks подряд
            
            try:
                while True:
                    chunk = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    if chunk:
                        empty_count = 0  # Сбрасываем счетчик пустых chunks
                        full_answer += chunk
                    else:
                        empty_count += 1
                        if empty_count >= max_empty:
                            break  # Слишком много пустых chunks подряд
            except asyncio.TimeoutError:
                logger.warning("Таймаут ожидания ответа от RAG сервиса")
            except websockets.exceptions.ConnectionClosed:
                pass  # WebSocket закрылся - это нормально
            
            logger.info(f"Получен ответ от RAG сервиса: '{full_answer[:100]}...' (длина: {len(full_answer)})")
            
            # Кешируем ответ (аналогично Telegram боту)
            if question_id and int(question_id) not in [777, 888, 999]:
                answer_for_cache = full_answer.strip()
                question_id_int = int(question_id)
                
                # Определяем тип кеширования на основе question_id
                if question_id_int in [1, 2, 3, 4, 5, 18, 19, 20, 21]:
                    # Кешируем по специализации
                    if question_id_int not in cache_by_specialization:
                        cache_by_specialization[question_id_int] = {}
                    cache_by_specialization[question_id_int][specialization] = answer_for_cache
                    logger.info(f"Ответ закеширован по специализации: question_id={question_id_int}, specialization={specialization}")
                else:
                    # Общий кеш
                    cache_dict[question_id_int] = answer_for_cache
                    logger.info(f"Ответ закеширован в общем кеше: question_id={question_id_int}")
            
            return {
                "answer": full_answer.strip(),
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
    """Обработка вопроса пользователя"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        user_id = data.get('user_id', 'guest')
        role = data.get('role', '')
        specialization = data.get('specialization', '')
        question_id = data.get('question_id', None)  # Добавляем поддержку question_id
        
        if not question:
            return jsonify({"error": "Вопрос не может быть пустым"}), 400
        
        # Отправляем вопрос через WebSocket с учетом question_id
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            send_websocket_question(question, user_id, role, specialization, question_id)
        )
        loop.close()
        
        # Сохраняем в историю
        save_to_history(user_id, question, result.get('answer', ''), role, specialization)
        
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
        role = data.get('role', '')
        specialization = data.get('specialization', '')
        question_id = data.get('question_id', None)
        
        if not question:
            return jsonify({"error": "Вопрос не может быть пустым"}), 400
        
        if not question_id:
            return jsonify({"error": "Для библиотечных вопросов обязателен question_id"}), 400
        
        question_id_int = int(question_id)
        
        # Проверяем кеш сначала (аналогично Telegram боту)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        cached_result = loop.run_until_complete(
            handle_cached_request(question_id_int, question, user_id, role, specialization)
        )
        
        if cached_result:
            logger.info(f"Возвращаем кешированный ответ для question_id={question_id_int}")
            loop.close()
            return jsonify(cached_result)
        
        # Если в кеше нет, отправляем запрос к RAG сервису
        logger.info(f"Кеш не найден, отправляем запрос к RAG сервису для question_id={question_id_int}")
        result = loop.run_until_complete(
            send_websocket_question(question, user_id, role, specialization, question_id)
        )
        loop.close()
        
        # Сохраняем в историю
        save_to_history(user_id, question, result.get('answer', ''), role, specialization)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка обработки библиотечного вопроса: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """Получение готовых вопросов для библиотеки"""
    try:
        role = request.args.get('role', '')
        specialization = request.args.get('specialization', '')
        
        if not role:
            # Возвращаем все вопросы для всех ролей
            all_questions = []
            for role_name, questions in QUESTIONS_BY_ROLE.items():
                if isinstance(questions, dict) and role_name == "Лид компетенции":
                    # Для лида компетенции выбираем подходящую специализацию
                    if specialization == "Аналитик" and "Аналитик" in questions:
                        all_questions.extend(questions["Аналитик"])
                    else:
                        all_questions.extend(questions["default"])
                elif isinstance(questions, list):
                    all_questions.extend(questions)
            return jsonify(all_questions)
        
        # Получаем вопросы для конкретной роли
        if role in QUESTIONS_BY_ROLE:
            questions = QUESTIONS_BY_ROLE[role]
            
            if isinstance(questions, dict) and role == "Лид компетенции":
                # Для лида компетенции выбираем подходящую специализацию
                if specialization == "Аналитик" and "Аналитик" in questions:
                    return jsonify(questions["Аналитик"])
                else:
                    return jsonify(questions["default"])
            
            return jsonify(questions)
        
        return jsonify([])
        
    except Exception as e:
        logger.error(f"Ошибка получения вопросов: {e}")
        return jsonify({"error": "Ошибка получения вопросов"}), 500

@app.route('/api/roles', methods=['GET'])
def get_roles():
    """Получение списка ролей"""
    try:
        return jsonify(ROLES)
    except Exception as e:
        logger.error(f"Ошибка получения ролей: {e}")
        return jsonify({"error": "Ошибка получения ролей"}), 500

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
    """Получение профиля пользователя"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Ошибка подключения к БД"}), 500
            
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Role, Specialization FROM Users WHERE user_id = ?",
            (user_id,)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                "role": user["Role"] or "",
                "specialization": user["Specialization"] or ""
            })
        else:
            return jsonify({
                "role": "",
                "specialization": ""
            })
            
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {e}")
        return jsonify({"error": "Ошибка получения профиля"}), 500

@app.route('/api/profile/<user_id>', methods=['POST'])
def save_profile(user_id):
    """Сохранение профиля пользователя"""
    try:
        data = request.get_json()
        role = data.get('role', '')
        specialization = data.get('specialization', '')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Ошибка подключения к БД"}), 500
            
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT user_id FROM Users WHERE user_id = ?", (user_id,))
        user_exists = cursor.fetchone()
        
        if user_exists:
            # Обновляем существующего пользователя
            cursor.execute(
                "UPDATE Users SET Role = ?, Specialization = ? WHERE user_id = ?",
                (role, specialization, user_id)
            )
        else:
            # Создаем нового пользователя
            cursor.execute(
                "INSERT INTO Users (user_id, Role, Specialization, is_onboarding) VALUES (?, ?, ?, ?)",
                (user_id, role, specialization, True)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Ошибка сохранения профиля: {e}")
        return jsonify({"error": "Ошибка сохранения профиля"}), 500

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

def save_to_history(user_id, question, answer, role="", specialization=""):
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

@app.route('/api/suggest_questions', methods=['POST'])
def suggest_questions():
    """Fallback endpoint для генерации связанных вопросов через HTTP"""
    try:
        data = request.get_json()
        
        user_question = data.get('user_question', '')
        bot_answer = data.get('bot_answer', '')
        role = data.get('role', 'Пользователь')
        specialization = data.get('specialization', 'Не указана')
        
        logger.info(f"HTTP suggest_questions: получен запрос для роли {role}, специализации {specialization}")
        
        # Попробуем подключиться к RAG сервису через WebSocket
        import asyncio
        import websockets
        import json
        
        async def get_suggestions():
            try:
                uri = "ws://127.0.0.1:8000/ws_suggest"
                async with websockets.connect(uri, timeout=10) as websocket:
                    payload = {
                        "user_question": user_question,
                        "bot_answer": bot_answer,
                        "role": role,
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
        role = data.get('role', 'Не указана')
        specialization = data.get('specialization', 'Не указана')
        
        # Детальная проверка каждого поля
        logger.info(f"Детальный анализ данных:")
        logger.info(f"  - feedback: '{feedback}' (длина: {len(feedback)})")
        logger.info(f"  - user_id: '{user_id}' (тип: {type(user_id)})")
        logger.info(f"  - user_name: '{user_name}' (тип: {type(user_name)})")
        logger.info(f"  - username: '{username}' (тип: {type(username)})")
        logger.info(f"  - role: '{role}' (тип: {type(role)})")
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
            safe_role = str(role).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            safe_specialization = str(specialization).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            safe_feedback = str(feedback).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            
            feedback_text = (
                f"📨 *Новый отзыв от пользователя (WebApp):*\n"
                f"👤 *Имя:* {safe_user_name}\n"
                f"📍 *Username:* @{safe_username}\n"
                f"🆔 *User ID:* {user_id}\n"
                f"👔 *Роль:* {safe_role}\n"
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