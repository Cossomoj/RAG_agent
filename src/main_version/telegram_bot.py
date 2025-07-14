import telebot
from dotenv import load_dotenv
from telebot import types
import asyncio
import websockets
import requests
import json
import time
import os
import sqlite3
import schedule
from datetime import datetime, UTC, timedelta
import threading
import pytz
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
from questions_loader import questions_loader

load_dotenv()

# Настройка логирования
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = "/app/src/main_version/AI_agent.db"

WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"
moscow_tz = pytz.timezone('Europe/Moscow')

dialogue_context = {}
count_questions_users = {}

secret_key = os.getenv("TELEGRAM_API_KEY")
FEEDBACK_BOT_TOKEN = os.getenv("FEEDBACK_BOT_TOKEN")
FEEDBACK_CHAT_ID = os.getenv("FEEDBACK_CHAT_ID")

feedback_bot = telebot.TeleBot(FEEDBACK_BOT_TOKEN)
# cache_dict = {3 : ["Уровень Junior\nСофты:\n1. Желание учиться которое подтверждается делом.(Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком.(Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Многозадачность - в термин (многозадачность) вкладывается НЕ возможность в каждый момент времени думать сразу о нескольких задачах, а возможность переключаться между задачами/проектами (от 2х - оптимально, до 5ти - максимально) без сильной потери эффективности (что какая-то потеря эффективности будет - факт).",
#                     "Харды:\n1. Знание json нотации.\n2. Знание Postman и Curl (любого инструмента отправки http запросов).\n3. Умение использовать User Story и Use Case.\n4. Понимание клиент-серверного взаимодействия.\n5. Владение  любым инструментом разметки макетов (пэинт/фотошоп/автокад/...).",
#                     "Уровень Junior+ Middle-\nСофты:\n1. Желание учиться которое  подтверждается делом (Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком (Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Многозадачность (определение см. выше)",
#                     "Харды:\n1. Знание json нотации.\n2. Знание Postman и Curl. (любого инструмента отправки http запросов).\n3. Умение использовать User Story и Use Case.\n4. Понимание клиент-серверного взаимодействия.\n5. Владение  любым инструментом разметки макетов (пэинт/фотошоп/автокад/...).\n6. Построение сиквенс диаграмм в UML нотации.\n7. Умение работать со сваггером/openAPI cхемами.",
#                     "Уровень Middle+\nСофты:\n1. Желание учиться которое подтверждается делом.(Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком.(Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Умениедоносить своимысли до коллег.\n5. Умение объяснить заказчику возможные варианты реализации.",
#                     "6. Многозадачность\n7. Умение выявить у себя недостаток знаний в определенном домене и закрыть его при необходимости\nХарды:\n1. Знание json и xml нотации.\n2. Знание Postman и Curl. Любого инструмента отправки http запросов.\n3. Умение использовать User Story и Use Case.\n4. Понимание клиент-серверного взаимодействия.\n5. Владение любым инструментом разметки макетов (пэинт/фотошоп/автокад/...).",
#                     "6. Построение сиквенс диаграмм в UML нотации.\n7. Умение работать со сваггером/openAPI cхемами.\n8. Понимание синхронного и асинхронног взаимодействия на уровне, не просто знания протоколов, а для чего они реально нужны, когда применять одно, когда другое.\n9. Опыт работы с очередями (Rabbit, Kafka).\n10. Понимание плюсов и минусов микросервисов и монолита.",
#                     "11. Понимание стейтлесс и стэйтфул сервисов.\n12. Понимание подхода API first.\n13. Опыт работы с Charles. (перехват и анализ клиент-серверных запросов).\n14. Опыт работы с реляционными и нереляционными базами, понимание разницы между ними, умение писать простые запросы.\n15. Умение программировать (скрипты, REST api методы) на скриптовом языке (python, js).\n16. Понимание принципов работы LLM.",
#                     "Уровень Senior\nСофты:\n1. Желание учиться которое подтверждается делом.(Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком.(Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Умениедоносить своимысли до коллег.\n5. Умение объяснить заказчику возможные варианты реализации.",
#                     "6. Многозадачность\n7. Умение выявить у себя недостаток знаний в определенном домене и закрыть его при необходимости.\n8. Понимание как работа влияет на проект в целом: что нужно сделать в первом приоритете, что можно поставить на паузу, чего можно не делать вообще.\n9. Умение сглаживать напряжение внутри команды, умение объяснить команде, что могут быть задачи интересные, но не полезные для проекта",
#                     "Харды:\n1. Знание json и xml нотации.\n2. Знание Postman и Curl. Любого инструмента отправки http запросов.\n3. Умение использовать User Story и Use Case.\n4. Понимание клиент-серверного взаимодействия.\n5. Владение любым инструментом разметки макетов (пэинт/фотошоп/автокад/...).\n6. Построение сиквенс диаграмм в UML нотации.\n7. Умение работать со сваггером/openAPI cхемами.",
#                     "8. Понимание синхронного и асинхронног взаимодействия на уровне, не просто знания протоколов, а для чего они реально нужны, когда применять одно, когда другое.\n9. Опыт работы с очередями (Rabbit, Kafka).\n10. Понимание плюсов и минусов микросервисов и монолита.\n11. Понимание стейтлесс и стэйтфул сервисов.\n12. Понимание подхода API first.",
#                     "13. Опыт работы с Charles. (перехват и анализ клиент-серверных запросов).\n14. Опыт работы с реляционными и нереляционными базами, понимание разницы между ними, умение писать простые запросы.\n15. Умение программировать (скрипты, REST api методы) на скриптовом языке (python, js).\n16. Понимание принципов работы LLM.",
#                     "17. Умение построить (возможно с командой) и понимать архитектуру проекта, понимать, что можно легко доработать, а что потребует серьезного изменения скоупа проекта.\n18. Понимание взаимодействия микросервисов между собой (ресты, очереди, service mesh).\n19. Понимание работы docker и kubernetes",
#                     "Уровень Lead\nСофты:\n1. Желание учиться которое подтверждается делом.(Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком.(Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Умениедоносить своимысли до коллег.\n5. Умение объяснить заказчику возможные варианты реализации.",
#                     "6. Многозадачность\n7. Умение выявить у себя недостаток знаний в определенном домене и закрыть его при необходимости.\n8. Понимание как работа влияет на проект в целом: что нужно сделать в первом приоритете, что можно поставить на паузу, чего можно не делать вообще.\n9. Умение сглаживать напряжение внутри команды, умение объяснить команде, что могут быть задачи интересные, но не полезные для проекта",
#                     "10. Наставничество над коллегами из своей компетенции с понятным результатом - приобретением ими желаемых скиллов.\n11. Умение давать (ученикам) нетравматичную ОС.\n12. Умение проведения встреч one-2-one.\nХарды: Харды Senior и Lead не отличаются"]}
cache_dict = {}
cache_by_specialization = {}

def get_cache_type_for_question(question_id):
    """
    Определяет тип кеша для вопроса.
    
    НОВАЯ ЛОГИКА: ВСЕ вопросы из библиотеки кешируются по специализации пользователя,
    так как RAG система учитывает специализацию при генерации ответов.
    
    Returns:
        'by_specialization' - для всех вопросов из библиотеки
        'no_cache' - для системных вопросов (777, 888) которые не кешируются
    """
    try:
        # Системные вопросы не кешируются
        if question_id in [777, 888]:
            return 'no_cache'
        
        # Проверяем, что вопрос существует в БД
        conn = sqlite3.connect(DATABASE_URL)
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

def clear_all_cache():
    """
    Функция для полной очистки всех кешей.
    
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
        
        logger.info(f"🧹 ВСЕ КЕШИ ОЧИЩЕНЫ: cache_dict({cache_dict_count}) + {spec_count} специализаций({total_questions} вопросов)")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке кешей: {e}")
        return False

def clear_cache_for_specialization(specialization):
    """
    Функция для очистки кеша конкретной специализации.
    
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
            logger.info(f"🧹 Очищен кэш для специализации '{specialization}': удалено {cleared_count} вопросов")
        else:
            logger.info(f"✅ Кэш для специализации '{specialization}' уже пуст")
        
        return cleared_count
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке кэша для специализации '{specialization}': {e}")
        return 0

def clear_cache_on_specialization_change(old_specialization, new_specialization):
    """
    Функция для очистки кеша при смене специализации пользователя.
    
    НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
    Теперь очистка стала максимально простой - удаляем старую специализацию.
    
    Args:
        old_specialization: Предыдущая специализация пользователя
        new_specialization: Новая специализация пользователя
        
    Returns:
        dict: Статистика очистки
    """
    global cache_by_specialization, cache_dict
    
    try:
        logger.info(f"🔄 СМЕНА СПЕЦИАЛИЗАЦИИ с '{old_specialization}' на '{new_specialization}'")
        
        # Логируем состояние кэша ДО очистки
        old_spec_count = len(cache_by_specialization.get(old_specialization, {}))
        cache_dict_count_before = len(cache_dict)
        
        logger.info(f"   ДО очистки: специализация '{old_specialization}' имеет {old_spec_count} вопросов в кэше")
        logger.info(f"   ДО очистки: cache_dict имеет {cache_dict_count_before} записей")
        
        # Очищаем кеш для старой специализации (теперь это очень просто!)
        cleared_by_spec = clear_cache_for_specialization(old_specialization) if old_specialization else 0
        
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Принудительно очищаем весь cache_dict
        if cache_dict:
            cache_dict_count = len(cache_dict)
            cache_dict.clear()
            logger.warning(f"   🧹 ПРИНУДИТЕЛЬНО очищен cache_dict: удалено {cache_dict_count} записей")
        else:
            cache_dict_count = 0
            logger.info(f"   ✅ cache_dict уже пуст")
        
        # Логируем состояние кэша ПОСЛЕ очистки
        total_specs = len(cache_by_specialization)
        new_spec_count = len(cache_by_specialization.get(new_specialization, {}))
        
        logger.info(f"   ПОСЛЕ очистки: всего специализаций в кэше: {total_specs}")
        logger.info(f"   ПОСЛЕ очистки: новая специализация '{new_specialization}' имеет {new_spec_count} вопросов")
        logger.info(f"   ПОСЛЕ очистки: cache_dict имеет {len(cache_dict)} записей")
        
        result = {
            'by_specialization_count': cleared_by_spec,
            'cache_dict_count': cache_dict_count
        }
        
        logger.info(f"✅ СМЕНА СПЕЦИАЛИЗАЦИИ ЗАВЕРШЕНА: очищено {cleared_by_spec} вопросов + {cache_dict_count} из cache_dict")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при смене специализации: {e}")
        return {'by_specialization_count': 0, 'cache_dict_count': 0}

def send_message_to_all_users(message_text):
    """
    Функция для отправки сообщения всем пользователям.
    """
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Получаем всех пользователей
        cursor.execute("SELECT user_id FROM Users")
        users = cursor.fetchall()
        conn.close()
        
        success_count = 0
        fail_count = 0
        
        # Отправляем сообщение каждому пользователю
        for user in users:
            try:
                bot.send_message(user[0], message_text)
                success_count += 1
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {user[0]}: {e}")
                fail_count += 1
        
        logger.info(f"Отправка сообщений завершена. Успешно: {success_count}, Ошибок: {fail_count}")
        return {
            'success': True,
            'message': f'Сообщение отправлено {success_count} пользователям. Ошибок: {fail_count}'
        }
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщений всем пользователям: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# Токен Telegram-бота
bot = telebot.TeleBot(secret_key)
# Словарь для хранения данных пользователя
user_data = {}
suggested_questions_storage = {}

# Тестовый обработчик убран - основные обработчики теперь должны работать

def init_db():
    # Подключаемся к базе данных (или создаем ее, если она не существует)
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Создаем таблицу Users (убрано поле Role)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT NULL,
            user_fullname TEXT DEFAULT NULL,
            reminder BOOl DEFAULT TRUE,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            Specialization TEXT DEFAULT NULL,
            is_onboarding BOOLEAN DEFAULT FALSE NOT NULL
        )
        ''')
        
        # Миграция: удаляем поле Role если оно существует
        try:
            cursor.execute("PRAGMA table_info(Users)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'Role' in columns:
                # Создаем новую таблицу без поля Role
                cursor.execute('''
                CREATE TABLE Users_new (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT DEFAULT NULL,
                    user_fullname TEXT DEFAULT NULL,
                    reminder BOOLEAN DEFAULT TRUE,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    Specialization TEXT DEFAULT NULL,
                    is_onboarding BOOLEAN DEFAULT FALSE NOT NULL
                )
                ''')
                
                # Копируем данные (без поля Role)
                cursor.execute('''
                INSERT INTO Users_new (user_id, username, user_fullname, reminder, create_time, Specialization, is_onboarding)
                SELECT user_id, username, user_fullname, reminder, create_time, Specialization, is_onboarding FROM Users
                ''')
                
                # Удаляем старую таблицу и переименовываем новую
                cursor.execute("DROP TABLE Users")
                cursor.execute("ALTER TABLE Users_new RENAME TO Users")
                logger.info("Поле Role успешно удалено из таблицы Users")
        except sqlite3.Error as e:
            logger.warning(f"Ошибка миграции таблицы Users: {e}")

        # Создаем таблицу Reminder
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Reminder (
        id_rem INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER,
        reminder_text TEXT DEFAULT NULL,
        reminder_time TEXT DEFAULT NULL,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
        ''')

        # Создаем таблицу Message_history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Message_history (
        user_id INTEGER, 
        role TEXT CHECK(role IN ('user', 'assistant')),
        message TEXT NOT NULL,
        time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
        ''')

        # Фиксируем изменения в базе данных
        conn.commit()
        logger.info("База данных инициализирована успешно")
    except Exception as e:
        # В случае ошибки откатываем изменения
        conn.rollback()
        logger.error(f"Ошибка при создании таблиц: {e}")
    finally:
        # Закрываем соединение с базой данных
        conn.close()

# Вызов функции для инициализации базы данных
init_db()

def cleanup_user_data():
    """
    Функция для очистки некорректных данных пользователей в БД.
    Заменяет "не указан" и пустые строки на NULL.
    """
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Заменяем "не указан" на NULL для username
        cursor.execute('UPDATE Users SET username = NULL WHERE username = "не указан"')
        username_updated = cursor.rowcount
        
        # Заменяем пустые строки на NULL для username
        cursor.execute('UPDATE Users SET username = NULL WHERE username = ""')
        username_updated += cursor.rowcount
        
        # Заменяем пустые строки на NULL для user_fullname
        cursor.execute('UPDATE Users SET user_fullname = NULL WHERE user_fullname = ""')
        fullname_updated = cursor.rowcount
        
        # Заменяем пробельные строки на NULL для user_fullname
        cursor.execute('UPDATE Users SET user_fullname = NULL WHERE TRIM(user_fullname) = ""')
        fullname_updated += cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"🧹 Очистка данных пользователей завершена: username обновлено {username_updated} записей, user_fullname обновлено {fullname_updated} записей")
        return username_updated + fullname_updated
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке данных пользователей: {e}")
        return 0

# Запускаем очистку при старте бота
cleanup_user_data()

def require_onboarding(func):
    """
    Декоратор для проверки онбординга перед выполнением функции
    """
    def wrapper(message, *args, **kwargs):
        if isinstance(message, types.CallbackQuery):
            chat_id = message.message.chat.id
        else:
            chat_id = message.chat.id
            
        if not check_onboarding(chat_id):
            redirect_to_onboarding(message)
            return
        return func(message, *args, **kwargs)
    return wrapper

@bot.message_handler(commands=['onboarding'])
def start_onboarding(message):
    chat_id = message.chat.id
    
    # Создаем клавиатуру для выбора специализации напрямую
    keyboard = types.InlineKeyboardMarkup()
    specializations = [
        ("Аналитик", "spec_for_db_analyst"),
        ("Тестировщик", "spec_for_db_qa"),
        ("WEB", "spec_for_db_web"),
        ("Java", "spec_for_db_java"),
        ("Python", "spec_for_db_python")
    ]
    
    for spec_name, callback_data in specializations:
        keyboard.add(types.InlineKeyboardButton(text=spec_name, callback_data=callback_data))
    # Добавляем кнопку "В начало"
    keyboard.add(types.InlineKeyboardButton(text="В начало", callback_data="start"))
    
    bot.send_message(chat_id, "Выберите вашу специализацию:", reply_markup=keyboard)

# Обработчик выбора роли удален, так как роль больше не используется

@bot.callback_query_handler(func=lambda call: call.data.startswith("spec_for_db_"))
def handle_specialization_selection(call):
    chat_id = call.message.chat.id
    selected_spec = call.data.replace("spec_for_db_", "")
    
    # Маппинг специализаций
    spec_mapping = {
        "analyst": "Аналитик",
        "qa": "Тестировщик",
        "web": "WEB",
        "java": "Java",
        "python": "Python"
    }
    
    new_specialization = spec_mapping[selected_spec]
    
    # Получаем текущую специализацию для очистки кеша
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (chat_id,))
    current_user = cursor.fetchone()
    old_specialization = current_user[0] if current_user else None
    
    # Сохраняем специализацию и отмечаем онбординг как завершенный
    cursor.execute('''
        UPDATE Users 
        SET Specialization = ?, is_onboarding = TRUE 
        WHERE user_id = ?
    ''', (new_specialization, chat_id))
    conn.commit()
    
    # ВАРИАНТ 2: НЕ ОЧИЩАЕМ КЕШ ПРИ СМЕНЕ СПЕЦИАЛИЗАЦИИ
    # Кеш накапливается для всех специализаций и используется автоматически
    # Если нужно вернуть очистку кеша - раскомментируйте код ниже
    
    # # Очищаем кеш для старой специализации, если она отличается от новой
    # if old_specialization and old_specialization != new_specialization:
    #     cache_stats = clear_cache_on_specialization_change(old_specialization, new_specialization)
    #     logger.info(f"Пользователь {chat_id} сменил специализацию с '{old_specialization}' на '{new_specialization}'. "
    #                f"Кеш очищен: {cache_stats['by_specialization_count']} записей для старой специализации.")
    
    conn.close()
    
    # Показываем сообщение об успешном завершении онбординга
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Отлично! Ваша специализация: {new_specialization}"
    )

    # Получаем только специализацию из базы данных
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        specialization = result[0]
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]["specialization"] = specialization
    
    # Вызываем меню
    handle_start(call)

def get_future_reminders(user_id):
    """
    Получает все напоминания пользователя, запланированные на будущие даты.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        list: Список кортежей с информацией о напоминаниях
    """
    try:
        # Получаем текущую дату и время в формате для сравнения
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Подключаемся к базе данных
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row  # Чтобы получить доступ к колонкам по имени
        cursor = conn.cursor()
        
        # Выполняем запрос
        cursor.execute("""
            SELECT id_rem, reminder_text, reminder_time 
            FROM Reminder 
            WHERE user_id = ? AND reminder_time > ?
            ORDER BY reminder_time ASC
        """, (user_id, current_datetime))
        
        # Получаем результаты
        reminders = cursor.fetchall()
        
        # Преобразуем результаты в список словарей для удобства работы
        result = []
        for reminder in reminders:
            result.append({
                'id': reminder['id_rem'],
                'text': reminder['reminder_text'],
                'time': reminder['reminder_time']
            })
        
        return result
    
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении напоминаний: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Функция для обновления статуса напоминания в базе данных
def update_reminder_status(user_id, status):
    conn = sqlite3.connect(DATABASE_URL)  # Замените на имя вашей базы данных
    cursor = conn.cursor()
    cursor.execute('UPDATE Users SET reminder = ? WHERE user_id = ?', (status, user_id))
    conn.commit()
    conn.close()

# Функция для получения текущего статуса напоминания из базы данных
def get_reminder_status(user_id):
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT reminder FROM Users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    # Если пользователь не найден, возвращаем False (напоминания выключены)
    if result is None:
        return False
        
    return result[0]

def save_message_in_db(chat_id, role, message):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        time = datetime.now() 
        cursor.execute('''
        INSERT INTO Message_history (user_id, role, message, time)
        VALUES (?, ?, ?, ?)
        ''', (chat_id, role, message, time))
        conn.commit()
        conn.close()
        logger.debug(f"Сообщение сохранено в БД для пользователя {chat_id}")
    except sqlite3.Error as e:
        # Обработка ошибок базы данных
        logger.error(f"Ошибка при сохранении сообщения в историю для пользователя {chat_id}: {e}")

def take_history_dialog_from_db(chat_id):
    try:
        conn = sqlite3.connect(DATABASE_URL) 
        cursor = conn.cursor()

        # Запрос для получения 6 последних сообщений пользователя
        query = '''
        WITH last_messages AS (
            SELECT 
                role, 
                message, 
                time 
            FROM Message_history
            WHERE user_id = ?
            ORDER BY time DESC
            LIMIT 6
        )
        SELECT 
            GROUP_CONCAT(role || ': ' || message || ' (' || time || ')', '; ') AS full_history
        FROM last_messages
        ORDER BY time ASC;
        '''

        # Выполнение запроса
        cursor.execute(query, (chat_id,))
        result = cursor.fetchone()
        
        # Проверяем результат и преобразуем в строку
        if result is None or result[0] is None:
            logger.info(f"История сообщений пустая для пользователя {chat_id}")
            return "История сообщений пустая"
        
        # fetchone() возвращает кортеж, берем первый элемент
        logger.debug(f"Получена история диалога для пользователя {chat_id}")
        return str(result[0])
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории диалога для пользователя {chat_id}: {e}")
        return "История сообщений недоступна"
    finally:
        if conn:
            conn.close()

def check_onboarding(user_id):
    """
    Проверяет, прошел ли пользователь онбординг
    """
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT is_onboarding FROM Users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else False
    except Exception as e:
        logger.error(f"Ошибка при проверке онбординга для пользователя {user_id}: {e}")
        return False

def redirect_to_onboarding(message):
    """
    Перенаправляет пользователя на онбординг
    """
    # Получаем chat_id в зависимости от типа сообщения
    if isinstance(message, types.CallbackQuery):
        chat_id = message.message.chat.id
    else:
        chat_id = message.chat.id
        
    bot.send_message(
        chat_id,
        "Для использования бота необходимо пройти онбординг. Используйте команду /onboarding"
    )

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    
    # ИСПРАВЛЕНО: Правильная обработка данных пользователя из Telegram
    username = message.from_user.username if message.from_user.username else None
    
    # Формируем полное имя и сохраняем NULL если пустое
    user_fullname = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    user_fullname = user_fullname if user_fullname else None
    
    logger.info(f"👤 Пользователь {user_id}: username='{username}', fullname='{user_fullname}'")
    
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Проверяем существование пользователя
    cursor.execute("SELECT user_id FROM Users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        logger.info(f"Пользователь с ID {user_id} уже существует в базе данных")
        # Обновляем данные пользователя на случай, если они изменились
        cursor.execute("""
            UPDATE Users 
            SET username = ?, user_fullname = ?
            WHERE user_id = ?
        """, (username, user_fullname, user_id))
    else:
        # Вставляем нового пользователя со всеми полями
        cursor.execute("""
            INSERT INTO Users 
            (user_id, username, user_fullname, reminder, is_onboarding) 
            VALUES(?, ?, ?, ?, ?)
        """, (user_id, username, user_fullname, True, False))
        
        logger.info(f"Пользователь с ID {user_id} успешно добавлен в базу данных")
    
    conn.commit()
    conn.close()

    # Проверяем статус онбординга
    if not check_onboarding(user_id):
        redirect_to_onboarding(message)
        return

    # Создаем кнопку для начала работы
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Начать", callback_data="start")
    markup.add(button)
    
    bot.send_message(
        message.chat.id, 
        f"Добро пожаловать в GigaMentor, {user_fullname}! 🤖\n\n"
        f"Я - ваш персональный ИИ-ассистент. Для взаимодействия со мной:\n\n"
        f"1️⃣ Нажмите кнопку 'Начать'\n"
        f"2️⃣ Далее выберите специализацию:\n"
        f"• Аналитик   • Тестировщик   • Web-разработчик   • Java-разработчик   • Python-разработчик",
        reply_markup=markup
    )

# Обработчик нажатия кнопки Start
@bot.callback_query_handler(func=lambda call: call.data == "start")
def handle_start(call):
    chat_id = call.message.chat.id
    
    # Проверяем статус онбординга
    if not check_onboarding(chat_id):
        redirect_to_onboarding(call.message)
        return

    # Отменяем текущий обработчик следующего шага
    bot.clear_step_handler_by_chat_id(chat_id)
    
    # Создаем клавиатуру с кнопками
    markup = types.InlineKeyboardMarkup(row_width=1)
    roles = [
        types.InlineKeyboardButton(text="🚀 Мини-приложение", web_app=types.WebAppInfo(url="https://restocorp.ru"))
    ]
    markup.add(*roles)
    
    # Отправляем новое сообщение с главным меню 
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Меню", reply_markup=markup)

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "giga_mentor")
def handle_giga_mentor(call):
    chat_id = call.message.chat.id
    if not check_onboarding(chat_id):
        redirect_to_onboarding(call.message)
        return

    # Отменяем текущий обработчик следующего шага
    bot.clear_step_handler_by_chat_id(chat_id)
    
    # Создаем клавиатуру с кнопками
    markup = types.InlineKeyboardMarkup(row_width=1)
    roles = [
        types.InlineKeyboardButton(text="Как пользоваться", callback_data="whatido"),
        types.InlineKeyboardButton(text="Обратная связь", callback_data="feedback"),
        types.InlineKeyboardButton(text="Команда", callback_data="team"),
        types.InlineKeyboardButton(text="В начало", callback_data="start")
    ]
    markup.add(*roles)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=(
        "'Как пользоваться' - для просмотра краткой инструкции по использованию\n"
        "'Обратная связь' - для отправки обратной связи\n"
        "'Команда' - для просмотра контактов команды разработки"
    ), reply_markup=markup)

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "restart_onboarding")
def handle_restart_onboarding(call):
    chat_id = call.message.chat.id
    
    # Получаем текущую специализацию из базы данных
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    
    specialization = result[0] if result and result[0] else "Не задана"
    
    # Создаем клавиатуру с кнопками
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text="Изменить специализацию", callback_data="onboarding"),
        types.InlineKeyboardButton(text="В начало", callback_data="start")
    )
    
    # Отправляем сообщение с текущими данными и кнопками
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Ваша специализация: {specialization}\n\n"
             f"Для изменения специализации:\n"
             f"Выберите 'Изменить специализацию'",
            
        reply_markup=markup
    )
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "onboarding")
def handle_pop_up_onboarding(call):
    start_onboarding(call.message)


@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "personal_account")
def handle_personal_account(call):
    chat_id = call.message.chat.id
    # Проверяем статус онбординга
    if not check_onboarding(chat_id):
        redirect_to_onboarding(call.message)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    roles = [
        types.InlineKeyboardButton(text="Проактивный режим", callback_data="menu_rem"),
        types.InlineKeyboardButton(text="История сообщений", callback_data="question_777"),
        types.InlineKeyboardButton(text="Пройти онбординг заново", callback_data="restart_onboarding"),
        types.InlineKeyboardButton(text="В начало", callback_data="start")
    ]
    markup.add(*roles)
    
    # Отправляем сообщение с кнопками
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text="Личный кабинет\nВыберите действие:",
        reply_markup=markup
    )

# Обработчик нажатия кнопки "Поставьте напоминание"
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "menu_rem")
def handle_reminder(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back_button = ([types.InlineKeyboardButton(text="Запланировать сообщение на тему", callback_data="rem_by_user"),
                   types.InlineKeyboardButton(text="Регулярные сообщения", callback_data="on_reminder"),
                   types.InlineKeyboardButton(text="Мои уведомления", callback_data="my_reminders"),
                   types.InlineKeyboardButton(text="В начало", callback_data="start")])
    markup.add(*back_button)
    bot.edit_message_text(chat_id = call.message.chat.id, message_id=call.message.message_id, text="Вы находитесь в разделе напоминания\nВыберите дальнейшие действия:", reply_markup=markup)


@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("whatido"))
def handle_other(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            "🚀 *Я умею:*\n"
            "✅ *Помогать по ролям:* бизнес-заказчику, лиду компетенции, линейному сотруднику.\n"
            "✅ *Специализируюсь на аналитике*, а также роли тестировщик, web, Java, Python.\n"
            "✅ *Отвечать на вопросы* из списка или в свободной форме.\n"
            "✅ *Объяснять роли в команде* и развивать профессиональные навыки.\n"
            "✅ *Рассылка полезных материалов и персональные советы* на основе ваших диалогов.\n"
            "Спрашивайте — помогу разобраться! 😊"
        ),
        parse_mode="Markdown"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="В начало", callback_data="start"))
    bot.send_message(call.message.chat.id, "Вы можете продолжить работу, вернувшись в начало:", reply_markup=markup)


@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("feedback"))
def handle_other_buttons(call):
    if call.data == "feedback":
        bot.send_message(call.message.chat.id, "📝 *Оставить ОС*\n\nНапишите, о чем хотите оставить ОС — начнём! 🌟",
                         parse_mode="Markdown")
        bot.register_next_step_handler(call.message, handle_feedback)

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "team")
def handle_team(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="В начало", callback_data="start"))
    bot.edit_message_text(
        chat_id = call.message.chat.id,
        message_id=call.message.message_id,
        text = "@dradns \n@betonnnnnnnn \n@latexala \n@alexr_home \n@leanorac \n@kathlynw \n@grahamchik \n@biryukovaoly \n@Mplusk \nПриглашаем работать над ИИ-агентом вместе с нами! Напиши @biryukovaoly, чтобы присоединиться.",
        reply_markup=markup)


@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "my_reminders")
def handle_print_reminders(call):
    user_id = call.from_user.id
    current_status = get_reminder_status(user_id)
    future_reminders = get_future_reminders(user_id)
    if future_reminders:
        reminder_text = "Ваши предстоящие напоминания:\n\n"
        for reminder in future_reminders:
            reminder_text += f"📅 {reminder['time']}\n📝 {reminder['text']}\n\n"
    else:
        reminder_text = "У вас нет предстоящих напоминаний."

    markup = types.InlineKeyboardMarkup(row_width=1)
    back_button = ([types.InlineKeyboardButton(text="В начало", callback_data="start")])
    markup.add(*back_button)
    bot.edit_message_text(chat_id = call.message.chat.id, message_id=call.message.message_id, text=f"➕ Запланированные сообщения, настроенные вами:\n{reminder_text}\n⏰ Регулярные сообщения от ИИ-агента:\n📅 Каждую пятницу в 19:00 вы будете получатьсообщение с анализом вашей истории диалога\n{'✅ Вкл' if current_status else '❌ Выкл'}", parse_mode="Markdown", reply_markup=markup)

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "on_reminder")
def handle_on_reminder(call):
    user_id = call.from_user.id
    # Получаем текущий статус уведомлений
    current_status = get_reminder_status(user_id)
    status_text = f"Текущий статус уведомлений: {'✅ Вкл' if current_status else '❌ Выкл'}"

    # Создаем клавиатуру с кнопками "Вкл", "Выкл" и "Назад"
    markup = types.InlineKeyboardMarkup(row_width=1)
    other_buttons = [
        types.InlineKeyboardButton(text="Вкл", callback_data="rem_on"),
        types.InlineKeyboardButton(text="Выкл", callback_data="rem_of"),
        types.InlineKeyboardButton(text="В начало", callback_data="start")
    ]
    markup.add(*other_buttons)

    # Редактируем сообщение с новым текстом и клавиатурой
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"Вы находитесь в разделе управления уведомлениями.\n{status_text}\nВыберите действие:",
        reply_markup=markup
    )

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data in ["rem_on", "rem_of"])
def handle_reminder_toggle(call):
    user_id = call.from_user.id
    if call.data == "rem_on":
        update_reminder_status(user_id, True)
        status_text = "✅ Уведомления включены."
    else:
        update_reminder_status(user_id, False)
        status_text = "❌ Уведомления выключены."

    # Получаем обновленный статус уведомлений
    current_status = get_reminder_status(user_id)
    status_text += f"\nТекущий статус: {'✅ Вкл' if current_status else '❌ Выкл'}"

    # Создаем клавиатуру с кнопками "Вкл", "Выкл" и "Назад"
    markup = types.InlineKeyboardMarkup(row_width=1)
    other_buttons = [
        types.InlineKeyboardButton(text="Вкл", callback_data="rem_on"),
        types.InlineKeyboardButton(text="Выкл", callback_data="rem_of"),
        types.InlineKeyboardButton(text="В начало", callback_data="start")
    ]
    markup.add(*other_buttons)

    # Редактируем сообщение с новым текстом и клавиатурой
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=status_text,
        reply_markup=markup
    )

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "rem_by_user")
def handle_reminder_by_user(call):
    msg = bot.send_message(call.message.chat.id, "Введите дату сообщения в формате ГГГГ-ММ-ДД время сообщения в формате HH:MM и тему сообщения через пробел.\nНапример:\n 2025-03-29 14:30 Рассказать про UC")
    bot.register_next_step_handler(msg, lambda message: process_reminder_input(message))

def process_reminder_input(message):
    conn = None
    try:
        text = message.text.strip()
        
        # Находим первые два блока (дата и время) и остальное (текст напоминания)
        parts = text.split(maxsplit=2)
        
        if len(parts) < 3:
            raise ValueError("Недостаточно данных. Нужны дата, время и текст напоминания")
            
        date_part, time_part, reminder_text = parts
        
        # Объединяем дату и время для парсинга
        datetime_str = f"{date_part} {time_part}"
        
        # Парсим дату и время
        dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        
        # Корректировка часового пояса (вычитаем 3 часа)
        dt_obj = dt_obj - timedelta(hours=3)
        
        # Форматируем для БД
        db_time = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
        
        # Подключаемся к БД с активацией внешних ключей
        conn = sqlite3.connect(DATABASE_URL)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Проверяем существование пользователя
        cursor.execute("SELECT 1 FROM Users WHERE user_id = ?", (message.chat.id,))
        if not cursor.fetchone():
            raise ValueError("Пользователь не существует")
        
        # Сохраняем напоминание
        cursor.execute(
            """INSERT INTO Reminder 
            (user_id, reminder_text, reminder_time) 
            VALUES (?, ?, ?)""",
            (message.chat.id, reminder_text, db_time)
        )
        
        conn.commit()
        markup = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton(text="В начало", callback_data="start")
        ]
        markup.add(*buttons)
        # Форматируем для ответа
        user_time = dt_obj.strftime("%Y-%m-%d %H:%M")
        bot.send_message(
            message.chat.id,
            f"✅ Напоминание сохранено:\n"
            f"📅 {user_time}\n"
            f"📝 {reminder_text}",
            reply_markup=markup
        )
        
    except ValueError as ve:
        error_msg = f"Ошибка ввода: {ve}\n\nПример правильного формата:\n2024-12-31 23:59 Ваш текст"
        bot.send_message(message.chat.id, error_msg, reply_markup=markup)
    except sqlite3.IntegrityError:
        bot.send_message(message.chat.id, "⛔ Ошибка: Пользователь не найден в системе", reply_markup=markup)
    except sqlite3.Error as e:
        bot.send_message(message.chat.id, f"⛔ Ошибка базы данных: {str(e)}", reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f"⛔ Непредвиденная ошибка: {str(e)}", reply_markup=markup)
    finally:
        if conn:
            conn.close()

async def check():
    while True:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Получаем текущее время в формате ГГГГ-ММ-ДД ЧЧ:ММ
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Выбираем все напоминания
        cursor.execute("SELECT * FROM Reminder;")
        reminders_results = cursor.fetchall()
        
        for reminder in reminders_results:
            # Извлекаем дату и время из строки напоминания в базе
            reminder_datetime = reminder['reminder_time']
            # Если формат в БД отличается, преобразуем к нужному формату
            if isinstance(reminder_datetime, str):
                # Если в reminder_time полная дата и время
                try:
                    reminder_dt = datetime.strptime(reminder_datetime, "%Y-%m-%d %H:%M:%S")
                    reminder_formatted = reminder_dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    # Если там только время
                    try:
                        reminder_formatted = f"{datetime.now().strftime('%Y-%m-%d')} {reminder_datetime}"
                    except Exception as e:
                        logger.error(f"Ошибка при парсинге формата времени '{reminder_datetime}': {e}")
                        continue
            
            # Сравниваем текущее время с временем напоминания
            if current_datetime == reminder_formatted:
                cursor.execute("DELETE FROM Reminder WHERE id_rem=?", (reminder['id_rem'],))
                conn.commit()
                chat_id = reminder['user_id']
                context_str = reminder['reminder_text']
                if(not context_str):
                    context_str = "История сообщений пустая"
                question_id = 777
                specialization = 'Аналитик'
                count_for_pro_activity = 102
                question = 'without'
                
                try:
                    async with websockets.connect(WEBSOCKET_URL) as websocket:
                        await websocket.send(question)         # 1. question
                        await websocket.send("")               # 2. role (пустая строка)
                        await websocket.send(specialization)   # 3. specialization
                        await websocket.send(str(question_id)) # 4. question_id
                        await websocket.send(context_str)      # 5. context
                        await websocket.send(str(count_for_pro_activity)) # 6. count
                        
                        # Получаем специализацию пользователя и определяем vector_store
                        _, user_specialization = get_user_profile_from_db(chat_id)
                        if not user_specialization:
                            user_specialization = 'Аналитик'
                        user_vector_store = get_vector_store_for_specialization(user_specialization)
                        
                        await websocket.send(user_vector_store)  # 7. vector_store
                        try:
                            full_answer = ""
                            while True:
                                answer_part = await websocket.recv()  # Получаем ответ частями
                                if answer_part:
                                    full_answer += answer_part
                                else:
                                    logger.warning("Получено пустое сообщение от WebSocket.")
                            
                        except websockets.exceptions.ConnectionClosed:
                            markup = types.InlineKeyboardMarkup(row_width=1)
                            question = [
                                types.InlineKeyboardButton(text="В начало", callback_data="start"),
                                types.InlineKeyboardButton(text="Задать вопрос", callback_data="question_custom"),
                            ]
                            markup.add(*question)
                            try:
                                # Пытаемся отправить сообщение
                                bot.send_message(chat_id=chat_id, text=full_answer, reply_markup=markup)
                                logger.info(f"Сообщение отправлено пользователю {chat_id}")
                            except telebot.apihelper.ApiException as e:
                                # Если пользователь заблокировал бота, вы получите исключение
                                if "Forbidden: bot was blocked by the user" in str(e):
                                    logger.warning(f"Пользователь {chat_id} заблокировал бота.")
                                else:
                                    # Обработка других возможных ошибок
                                    logger.error(f"Ошибка при отправке сообщения: {e}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке напоминания: {e}")
        
        conn.close()
        await asyncio.sleep(60)  # Проверяем каждую минуту


# Функция для запуска асинхронной задачи
async def start():
    current_sec = int(datetime.now().strftime("%S"))
    delay = 60 - current_sec
    if delay == 60:
        delay = 0
    
    await asyncio.sleep(delay)
    await check()

# Запуск асинхронной задачи в отдельном потоке
def run_async_task():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start())

# Запуск планировщика в отдельном потоке
threading.Thread(target=run_async_task, daemon=True).start()

def get_reminder_schedule_from_db():
    """Получение настроек расписания регулярных сообщений из базы данных"""
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Создаем таблицу системных настроек если её нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SystemSettings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Добавляем настройки по умолчанию если их нет
        default_settings = [
            ('reminder_schedule_day', '4', 'День недели для отправки регулярных сообщений (0=понедельник, 4=пятница)'),
            ('reminder_schedule_time', '19:00', 'Время отправки регулярных сообщений (в формате HH:MM)'),
            ('reminder_timezone', 'Europe/Moscow', 'Часовой пояс для расписания')
        ]
        
        for key, value, description in default_settings:
            cursor.execute("""
                INSERT OR IGNORE INTO SystemSettings (setting_key, setting_value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))
        
        # Получаем настройки
        cursor.execute("SELECT setting_key, setting_value FROM SystemSettings WHERE setting_key IN (?, ?, ?)", 
                      ('reminder_schedule_day', 'reminder_schedule_time', 'reminder_timezone'))
        
        settings = {}
        for row in cursor.fetchall():
            settings[row[0]] = row[1]
        
        conn.commit()
        conn.close()
        
        # Формируем результат
        schedule = {
            'day': int(settings.get('reminder_schedule_day', '4')),
            'time': settings.get('reminder_schedule_time', '19:00'),
            'timezone': settings.get('reminder_timezone', 'Europe/Moscow')
        }
        
        logger.info(f"Загружены настройки расписания из БД: {schedule}")
        return schedule
        
    except Exception as e:
        logger.error(f"Ошибка при получении настроек расписания из БД: {e}")
        # Возвращаем настройки по умолчанию
        return {
            'day': 4,  # Пятница
            'time': '19:00',
            'timezone': 'Europe/Moscow'
        }

# Асинхронная функция для проверки и отправки напоминаний
async def check_for_daily_msg():
    logger.info("Запуск функции check_for_daily_msg")
    while True:
        try:
            # Получаем настройки расписания из базы данных
            schedule = get_reminder_schedule_from_db()
            
            # Получаем текущую дату и время в указанном часовом поясе
            timezone = pytz.timezone(schedule['timezone'])
            now = datetime.now(timezone)
            current_day = now.weekday()  # 0 - понедельник, 6 - воскресенье
            current_time = now.strftime("%H:%M")
            
            # Логируем текущее состояние для отладки
            logger.debug(f"Настройки расписания: {schedule}")
            logger.debug(f"Текущий день недели: {current_day}, время: {current_time} ({schedule['timezone']})")
            
            # Проверяем соответствие настроенному расписанию
            if current_day == schedule['day'] and current_time == schedule['time']:
                days_names = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
                logger.info(f"Наступило время для отправки регулярных сообщений: {days_names[schedule['day']]} в {schedule['time']} ({schedule['timezone']})")
                conn = sqlite3.connect(DATABASE_URL)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Выбираем всех пользователей
                cursor.execute("SELECT * FROM Users WHERE reminder = TRUE;")
                users_results = cursor.fetchall()
                conn.close()
                
                logger.info(f"Найдено {len(users_results)} пользователей с включенными напоминаниями")

                # Счетчики для статистики
                successful_sends = 0
                failed_sends = 0

                # Отправляем сообщение каждому пользователю
                for user in users_results:
                    chat_id = user['user_id']
                    
                    logger.info(f"Обработка пользователя {chat_id}")
                    
                    try:
                        # Получаем историю диалога пользователя
                        context_str = take_history_dialog_from_db(chat_id)
                        logger.debug(f"Тип context_str для пользователя {chat_id}: {type(context_str)}")
                        
                        if context_str is None:
                            context_str = "История сообщений пустая"
                            logger.warning(f"История сообщений пуста для пользователя {chat_id}")
                        elif not isinstance(context_str, str):
                            context_str = str(context_str)  # преобразуем в строку
                            logger.warning(f"Преобразован тип context_str в строку для пользователя {chat_id}")
                        
                        question_id = 777  # Изменено с 666 на 777 для корректной обработки
                        
                        # Получаем реальную специализацию пользователя из базы данных
                        _, specialization = get_user_profile_from_db(chat_id)
                        if not specialization:
                            specialization = 'Аналитик'  # Значение по умолчанию
                        
                        # Определяем vector_store на основе специализации
                        vector_store = get_vector_store_for_specialization(specialization)
                        
                        count_for_pro_activity = 101
                        question = 'without'
                        
                        logger.debug(f"Подключение к WebSocket для пользователя {chat_id}")
                        
                        # Добавляем тайм-аут для WebSocket соединения (30 секунд)
                        try:
                            async with websockets.connect(WEBSOCKET_URL) as websocket:
                                # Отправляем данные с тайм-аутом
                                await asyncio.wait_for(websocket.send(question), timeout=10.0)
                                await asyncio.wait_for(websocket.send(""), timeout=10.0)
                                await asyncio.wait_for(websocket.send(specialization), timeout=10.0)
                                await asyncio.wait_for(websocket.send(str(question_id)), timeout=10.0)
                                await asyncio.wait_for(websocket.send(context_str), timeout=10.0)
                                await asyncio.wait_for(websocket.send(str(count_for_pro_activity)), timeout=10.0)
                                await asyncio.wait_for(websocket.send(vector_store), timeout=10.0)  # 7-й параметр vector_store
                                
                                full_answer = ""
                                timeout_count = 0
                                max_timeout_count = 3
                                
                                try:
                                    while timeout_count < max_timeout_count:
                                        try:
                                            # Получаем ответ с тайм-аутом (10 секунд)
                                            answer_part = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                                            if answer_part:
                                                full_answer += answer_part
                                                timeout_count = 0  # Сбрасываем счетчик при получении данных
                                            else:
                                                logger.warning(f"Получено пустое сообщение от WebSocket для пользователя {chat_id}")
                                                timeout_count += 1
                                        except asyncio.TimeoutError:
                                            logger.warning(f"Тайм-аут при получении данных от WebSocket для пользователя {chat_id}, попытка {timeout_count + 1}")
                                            timeout_count += 1
                                            if timeout_count >= max_timeout_count:
                                                logger.error(f"Превышено максимальное количество тайм-аутов для пользователя {chat_id}")
                                                break
                                except websockets.exceptions.ConnectionClosed:
                                    logger.info(f"WebSocket соединение закрыто для пользователя {chat_id}")
                                
                                # Проверяем, получили ли мы ответ
                                if full_answer is None or full_answer == "":
                                    full_answer = "История сообщений пустая. Попробуйте позже."
                                    logger.warning(f"Пустой ответ от AI для пользователя {chat_id}")
                                
                                # Создаем клавиатуру
                                markup = types.InlineKeyboardMarkup(row_width=1)
                                buttons = [
                                    types.InlineKeyboardButton(text="В начало", callback_data="start"),
                                    types.InlineKeyboardButton(text="Задать вопрос", callback_data="question_custom"),
                                ]
                                markup.add(*buttons)
                                
                                try:
                                    # Отправляем сообщение
                                    bot.send_message(chat_id=chat_id, text=full_answer, reply_markup=markup)
                                    logger.info(f"Регулярное сообщение успешно отправлено пользователю {chat_id}")
                                    successful_sends += 1
                                except telebot.apihelper.ApiException as e:
                                    if "Forbidden: bot was blocked by the user" in str(e):
                                        logger.warning(f"Пользователь {chat_id} заблокировал бота")
                                    else:
                                        logger.error(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")
                                    failed_sends += 1
                                    
                        except asyncio.TimeoutError:
                            logger.error(f"Тайм-аут WebSocket соединения для пользователя {chat_id}")
                            failed_sends += 1
                        except Exception as websocket_error:
                            logger.error(f"Ошибка WebSocket для пользователя {chat_id}: {websocket_error}")
                            failed_sends += 1
                            
                    except Exception as e:
                        logger.error(f"Общая ошибка при обработке пользователя {chat_id}: {e}")
                        failed_sends += 1
                
                # Логируем статистику
                logger.info(f"Отправка регулярных сообщений завершена. Успешно: {successful_sends}, Ошибки: {failed_sends}")
                
                # После отправки всем пользователям ждем до следующего дня, 
                # чтобы не отправить сообщения дважды (спим 23 часа)
                logger.info("Все регулярные сообщения обработаны, ожидание до следующей проверки (23 часа)")
                await asyncio.sleep(23 * 60 * 60)  # 23 часа
                
            # Проверяем время каждую минуту
            await asyncio.sleep(60)
        
        except Exception as e:
            logger.error(f"Общая ошибка в check_for_daily_msg: {e}", exc_info=True)
            await asyncio.sleep(60)

async def start_for_hack():
    current_sec = int(datetime.now().strftime("%S"))
    delay = 60 - current_sec
    if delay == 60:
        delay = 0
    
    await asyncio.sleep(delay)
    await check_for_daily_msg()

# Запуск асинхронной задачи в отдельном потоке
def run_async_task_for_hack():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_for_hack())

# Запуск планировщика в отдельном потоке
threading.Thread(target=run_async_task_for_hack, daemon=True).start()

# Обработчик нажатия кнопки Выбор вопросов
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "menu_qr")
def handle_questions(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    
    # Получаем специализацию из базы данных
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result[0]:
        # Если специализация не установлена, запускаем онбординг
        redirect_to_onboarding(call.message)
        return
    
    specialization = result[0]
    
    # Сохраняем данные в user_data для использования в других функциях
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]["specialization"] = specialization
    
    # Показываем соответствующие вопросы в зависимости от специализации
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Получаем вопросы из БД через questions_loader (без роли)
    questions_list = questions_loader.get_questions_by_specialization(specialization)
    
    questions = []
    for q in questions_list:
        # Создаем кнопку для каждого вопроса
        questions.append(
            types.InlineKeyboardButton(
                text=q['question_text'], 
                callback_data=q['callback_data']
            )
        )
    
    # Добавляем системные кнопки, которые есть всегда
    if role != "PO/PM":  # Для всех, кроме PO/PM
        questions.append(types.InlineKeyboardButton(text="Что еще ты умеешь?", callback_data="question_777"))
    
    questions.append(types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom"))
    questions.append(types.InlineKeyboardButton(text="В начало", callback_data="start"))
    
    markup.add(*questions)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(f"Вы выбрали роль: {role}\nСпециализация: {specialization}\n\n"
              f"Чтобы задать вопрос:\n"
              f"• Выберите из списка готовых вопросов\n"
              f"• Или нажмите 'Ввести свой вопрос' для свободного вопроса"),
        reply_markup=markup
    )

def clear_dialog_context(chat_id):
    if chat_id in dialogue_context:
        dialogue_context[chat_id] = []
    if chat_id in count_questions_users:
        count_questions_users[chat_id] = 0

# Обработчик выбора специализации
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "menu_r")
def choose_menu(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    specializations = [
        types.InlineKeyboardButton(text="Аналитик", callback_data="specsql_analyst"),
        types.InlineKeyboardButton(text="Тестировщик", callback_data="specsql_tester"),
        types.InlineKeyboardButton(text="WEB", callback_data="specsql_web"),
        types.InlineKeyboardButton(text="Java", callback_data="specsql_java"),
        types.InlineKeyboardButton(text="Python", callback_data="specsql_python"),
        types.InlineKeyboardButton(text="В начало", callback_data="start"),
    ]
    markup.add(*specializations)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите специализацию:", reply_markup=markup)

 # Обработка выбора специализации
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("specsql_"))
def handle_role_specialization(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    user_id = call.message.chat.id
    data = call.data
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    specialization_mapping = {
        "specsql_analyst": "Аналитик",
        "specsql_tester": "Тестировщик",
        "specsql_web": "WEB",
        "specsql_java": "Java",
        "specsql_python": "Python"
    }
    new_specialization = specialization_mapping.get(data)
    
    # Получаем текущую специализацию для очистки кеша
    cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (user_id,))
    current_user = cursor.fetchone()
    old_specialization = current_user[0] if current_user else None
    
    # Обновляем Specialization и устанавливаем is_onboarding = TRUE
    cursor.execute("UPDATE Users SET Specialization = ?, is_onboarding = TRUE WHERE user_id = ?", (new_specialization, user_id))
    conn.commit()
    
    # Обновляем is_onboarding в пустой строке
    cursor.execute("UPDATE Users SET is_onboarding = FALSE WHERE user_id = ?", (user_id,))
    conn.commit()
    
    # ВАРИАНТ 2: НЕ ОЧИЩАЕМ КЕШ ПРИ СМЕНЕ СПЕЦИАЛИЗАЦИИ
    # Кеш накапливается для всех специализаций и используется автоматически
    # Если нужно вернуть очистку кеша - раскомментируйте код ниже
    
    # # Очищаем кеш для старой специализации, если она отличается от новой  
    # if old_specialization and old_specialization != new_specialization:
    #     cache_stats = clear_cache_on_specialization_change(old_specialization, new_specialization)
    #     logger.info(f"Пользователь {chat_id} сменил специализацию с '{old_specialization}' на '{new_specialization}'. "
    #                f"Кеш очищен: {cache_stats['by_specialization_count']} записей для старой специализации.")
    
    conn.close()
    
    # Возврат в главное меню
    
    # Синхронизируем user_data с БД (только специализация)
    cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (user_id,))
    user_db_data = cursor.fetchone()
    if user_db_data:
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["specialization"] = user_db_data[0]
    
    bot.answer_callback_query(call.id, f"Специализация '{new_specialization}' успешно сохранена!")
    cursor.execute("SELECT user_id, Specialization FROM Users WHERE user_id = ?", (user_id,))
    users = cursor.fetchone()

    if users:
        logger.debug(f"User ID: {users[0]}, Specialization: {users[1]}")
    conn.close()

    # Возврат в меню
    handle_start(call)



# Обработчик выбора роли удален, так как роль больше не используется

# Обработчик предопределенных вопросов
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("questions_group"))
def handle_predefined_question_group(call):
    switcher = 0
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    if call.data == "questions_group_2":
        switcher = 1
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    if switcher == 0:
        questions = [
            types.InlineKeyboardButton(text="Поиск кандидатов на работу", callback_data="qid_6"),
            types.InlineKeyboardButton(text="Проведение собеседований", callback_data="qid_7"),
            types.InlineKeyboardButton(text="Работа со стажерами/джунами", callback_data="qid_8"),
            types.InlineKeyboardButton(text="Проведение 1-2-1", callback_data="qid_9"),
            types.InlineKeyboardButton(text="Проведение встреч компетенции", callback_data="qid_10"),
            types.InlineKeyboardButton(text="В начало", callback_data="start")
        ]
        markup.add(*questions)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали категорию: \nТеперь выберите вопрос:", reply_markup=markup)
    elif switcher == 1:
        questions = [
            types.InlineKeyboardButton(text="Построение структуры компетенции", callback_data="qid_11"),
            types.InlineKeyboardButton(text="Создание ИПР", callback_data="qid_12"),
            types.InlineKeyboardButton(text="Как провести онбординг", callback_data="qid_13"),
            types.InlineKeyboardButton(text="Оптимизация процессов разработки", callback_data="qid_14"),
            types.InlineKeyboardButton(text="Советы по тайм-менеджменту", callback_data="qid_24"),
            types.InlineKeyboardButton(text="В начало", callback_data="start")
        ]
        markup.add(*questions)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали категорию: \nТеперь выберите вопрос:", reply_markup=markup)
    
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("group_1"))
def handle_predefined_question_group_1(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    specialization = ""
    question_id = 777
    
    if call.message.chat.id not in user_data:
        user_data[call.message.chat.id] = {"specialization": "Аналитик"}

    specialization = user_data[call.message.chat.id]['specialization']
    
    
    if call.data == "group_1_question_1":
        question = "Поиск кандидатов на рбаоту"
        question_id = 6
    elif call.data == "group_1_question_2":
        question = "Проведение собеседований"
        question_id = 7
    elif call.data == "group_1_question_3":
        question = "Работа со стажерами/джунами"
        question_id = 8
    elif call.data == "group_1_question_4":
        question = "Проведение 1-2-1"
        question_id = 9
    elif call.data == "group_1_question_5":
        question = "Проведение встреч компетенции"
        question_id = 10

    cache_type = get_cache_type_for_question(question_id)
    
    if cache_type == 'by_specialization':
        # НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
        if specialization in cache_by_specialization and question_id in cache_by_specialization[specialization]:
            asyncio.run(handling_cached_requests(question_id, call.message, question, specialization))
        else:
            vector_store = get_vector_store_for_specialization(specialization)
            asyncio.run(websocket_question_from_user(question, call.message, specialization, question_id, vector_store=vector_store))
    elif cache_type == 'no_cache':
        # Системные вопросы не кешируются, всегда генерируем новый ответ
        vector_store = get_vector_store_for_specialization(specialization)
        asyncio.run(websocket_question_from_user(question, call.message, specialization, question_id, vector_store=vector_store))
    else:
        # Fallback для новых вопросов - генерируем ответ
        vector_store = get_vector_store_for_specialization(specialization)
        asyncio.run(websocket_question_from_user(question, call.message, specialization, question_id, vector_store=vector_store))


@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("group_2"))
def handle_predefined_question_group_2(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    specialization = ""
    question_id = 777
    
    if call.message.chat.id not in user_data:
        user_data[call.message.chat.id] = {"specialization": "Аналитик"}

    specialization = user_data[call.message.chat.id]['specialization']
    
    
    if call.data == "group_2_question_1":
        question = "Построение структуры компетенции"
        question_id = 11
    elif call.data == "group_2_question_2":
        question = "Создание ИПР"
        question_id = 12
    elif call.data == "group_2_question_3":
        question = "Как провести онбординг"
        question_id = 13
    elif call.data == "group_2_question_4":
        question = "Оптимизация процессов разработки"
        question_id = 14
    elif call.data == "group_2_question_5":
        question = "Советы по тайм-менеджменту"
        question_id = 24

    cache_type = get_cache_type_for_question(question_id)
    
    if cache_type == 'by_specialization':
        # НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
        if specialization in cache_by_specialization and question_id in cache_by_specialization[specialization]:
            asyncio.run(handling_cached_requests(question_id, call.message, question, specialization))
        else:
            vector_store = get_vector_store_for_specialization(specialization)
            asyncio.run(websocket_question_from_user(question, call.message, specialization, question_id, vector_store=vector_store))
    elif cache_type == 'no_cache':
        # Системные вопросы не кешируются, всегда генерируем новый ответ
        vector_store = get_vector_store_for_specialization(specialization)
        asyncio.run(websocket_question_from_user(question, call.message, specialization, question_id, vector_store=vector_store))
    else:
        # Fallback для новых вопросов - генерируем ответ
        vector_store = get_vector_store_for_specialization(specialization)
        asyncio.run(websocket_question_from_user(question, call.message, specialization, question_id, vector_store=vector_store))

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("po_question"))
def handle_predefined_question_group_2(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    specialization = ""
    question_id = 777
    
    if call.message.chat.id not in user_data:
        user_data[call.message.chat.id] = {"specialization": "PO/PM"}

    user_data[call.message.chat.id]['specialization'] = "PO/PM"
    specialization = user_data[call.message.chat.id]['specialization']
    
    
    if call.data == "po_question_1":
        question = "Что я могу ожидать от специалиста"
        question_id = 15
    elif call.data == "po_question_2":
        question = "Что я могу ожидать от лида компетенции"
        question_id = 16
    elif call.data == "po_question_3":
        question = "Что ожидается от меня"
        question_id = 17

    cache_type = get_cache_type_for_question(question_id)
    
    if cache_type == 'by_specialization':
        # НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
        if specialization in cache_by_specialization and question_id in cache_by_specialization[specialization]:
            asyncio.run(handling_cached_requests(question_id, call.message, question, specialization))
        else:
            vector_store = get_vector_store_for_specialization(specialization)
            asyncio.run(websocket_question_from_user(question, call.message, specialization, question_id, vector_store=vector_store))
    elif cache_type == 'no_cache':
        # Системные вопросы не кешируются, всегда генерируем новый ответ
        vector_store = get_vector_store_for_specialization(specialization)
        asyncio.run(websocket_question_from_user(question, call.message, specialization, question_id, vector_store=vector_store))
    else:
        # Fallback для новых вопросов - генерируем ответ
        vector_store = get_vector_store_for_specialization(specialization)
        asyncio.run(websocket_question_from_user(question, call.message, specialization, question_id, vector_store=vector_store))



@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data in ["question_1", "question_2", "question_3", "question_4", "question_5", "question_18", "question_19", "question_20", "question_21"])
def handle_predefined_question(call):
    """
    Универсальный обработчик для старых «жестко заданных» вопросов.
    Теперь также передаёт настройку vector_store и использует prompt_id.
    """
    chat_id = call.message.chat.id
    callback_data = call.data
    question_id = int(callback_data.split('_')[1])
    logger.info(f"[{chat_id}] handle_predefined_question for {callback_data}")

    # Получаем профиль пользователя
    role, specialization = get_user_profile_from_db(chat_id)
    if not specialization:
        bot.send_message(chat_id, "Не удалось получить ваш профиль. Пожалуйста, пройдите онбординг заново через /start.")
        logger.warning(f"[{chat_id}] Профиль не найден при обработке {callback_data}")
        return

    # Получаем текст вопроса, vector_store и prompt_id
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT question_text, vector_store, prompt_id FROM Questions WHERE question_id = ?", (question_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            bot.send_message(chat_id, "Извините, этот вопрос больше не актуален.")
            logger.warning(f"[{chat_id}] Вопрос ID={question_id} не найден в Questions.")
            return
            
        question_text, vector_store_setting, prompt_id = row
        if not vector_store_setting:
            vector_store_setting = 'auto'
        
        # Если prompt_id задан, он имеет приоритет над question_id
        rag_id = prompt_id if prompt_id is not None else question_id
        
    except Exception as e:
        logger.error(f"[{chat_id}] DB error while fetching question {question_id}: {e}")
        bot.send_message(chat_id, "Произошла ошибка при обработке запроса. Попробуйте позже.")
        return

    logger.info(f"[{chat_id}] Handling question. RAG_ID={rag_id}, VS='{vector_store_setting}', Spec='{specialization}'")

    # Сообщение «Формирую ответ»
    typing_msg = bot.send_message(chat_id, "Формирую ответ... ⏳", parse_mode='Markdown')

    # Запуск асинхронного запроса в RAG
    asyncio.run(websocket_question_from_user(
        question=question_text,
        message=typing_msg,
        specialization=specialization,
        question_id=rag_id, # ИСПРАВЛЕНО: передаем правильный ID
        show_suggested_questions=True,
        vector_store=vector_store_setting
    ))

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "question_777")
def handle_message_history(call):
    chat_id = call.message.chat.id
    
    try:
        # Получаем последние 10 сообщений из базы данных
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        query = '''
        SELECT role, message, time 
        FROM Message_history
        WHERE user_id = ?
        ORDER BY time DESC
        LIMIT 10
        '''
        
        cursor.execute(query, (chat_id,))
        messages = cursor.fetchall()
        conn.close()
        
        if not messages:
            # Если истории нет
            markup = types.InlineKeyboardMarkup(row_width=1)
            back_button = types.InlineKeyboardButton(text="◀️ Назад в меню", callback_data="personal_account")
            markup.add(back_button)
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="📭 История сообщений пуста\n\nВы еще не задавали вопросы боту.",
                reply_markup=markup
            )
            return
        
        # Формируем красивое отображение истории
        history_text = "📚 **История ваших сообщений**\n"
        history_text += f"Показаны последние {len(messages)} сообщений:\n\n"
        
        # Переворачиваем список, чтобы показать от старых к новым
        messages = list(reversed(messages))
        
        for i, (role, message, timestamp) in enumerate(messages, 1):
            # Форматируем время (убираем секунды для краткости)
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%d.%m %H:%M")
            except Exception as e:
                logger.warning(f"Ошибка при форматировании timestamp '{timestamp}': {e}")
                formatted_time = timestamp[:16]  # Fallback
            
            # Определяем эмодзи и префикс в зависимости от роли
            if role == "user":
                emoji = "👤"
                prefix = "Вы"
            else:
                emoji = "🤖"
                prefix = "Бот"
            
            # Обрезаем длинные сообщения
            display_message = message
            if len(message) > 150:
                display_message = message[:147] + "..."
            
            history_text += f"{emoji} **{prefix}** ({formatted_time}):\n"
            history_text += f"{display_message}\n\n"
        
        # Добавляем кнопки навигации
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # Кнопка "Показать больше" (если есть еще сообщения)
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Message_history WHERE user_id = ?", (chat_id,))
        total_count = cursor.fetchone()[0]
        conn.close()
        
        buttons = []
        if total_count > 10:
            buttons.append(types.InlineKeyboardButton(text="📄 Показать все", callback_data="history_full"))
        
        buttons.append(types.InlineKeyboardButton(text="🗑 Очистить историю", callback_data="history_clear"))
        buttons.append(types.InlineKeyboardButton(text="◀️ Назад в меню", callback_data="personal_account"))
        
        # Добавляем кнопки по 2 в ряд, последнюю отдельно
        if len(buttons) >= 2:
            markup.add(buttons[0], buttons[1])
            if len(buttons) > 2:
                markup.add(buttons[2])
        else:
            markup.add(*buttons)
        
        # Отправляем сообщение с историей
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=history_text,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории сообщений для пользователя {chat_id}: {e}")
        
        # В случае ошибки показываем сообщение об ошибке
        markup = types.InlineKeyboardMarkup(row_width=1)
        back_button = types.InlineKeyboardButton(text="◀️ Назад в меню", callback_data="personal_account")
        markup.add(back_button)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="❌ Произошла ошибка при загрузке истории сообщений.\n\nПопробуйте позже.",
            reply_markup=markup
        )
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "question_custom")
def ask_custom_question(call):
    chat_id = call.message.chat.id
    # ИСПРАВЛЕНО: Очищаем контекст диалога при переходе в "Задать вопрос"
    clear_dialog_context(chat_id)
    bot.send_message(call.message.chat.id, "Введите ваш вопрос:")
    bot.register_next_step_handler(call.message, process_custom_question)


@require_onboarding
def process_custom_question(message):   
    """
    Обрабатывает кастомные вопросы, введенные после нажатия кнопки 'Ввести свой вопрос'
    Эта функция вызывается через register_next_step_handler
    """
    logger.info(f"Обрабатываем кастомный вопрос от пользователя {message.chat.id}")
    
    # Получаем специализацию из базы данных
    _, specialization = get_user_profile_from_db(message.chat.id)
    
    if not specialization:
        bot.send_message(message.chat.id, "Не удалось получить ваш профиль. Пожалуйста, пройдите онбординг заново через /start.")
        logger.warning(f"Не найден профиль для пользователя {message.chat.id} при обработке кастомного вопроса.")
        return

    question_id = 888  # Используем ID=888 для кастомных вопросов с памятью диалога
    question = message.text
    vector_store = get_vector_store_for_specialization(specialization)
    asyncio.run(websocket_question_from_user(question, message, specialization, question_id, show_suggested_questions=True, vector_store=vector_store))

async def handling_cached_requests(question_id, message, question, specialization):
    logger.debug("📦 Используется кешированное сообщение")

    cache_type = get_cache_type_for_question(question_id)
    
    if cache_type == 'by_specialization':
        # НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
        if specialization in cache_by_specialization and question_id in cache_by_specialization[specialization]:
            arr = cache_by_specialization[specialization][question_id]
            logger.info(f"✅ Получен кэшированный ответ для specialization='{specialization}', question_id={question_id}")
        else:
            logger.error(f"❌ Кэш не найден для specialization='{specialization}', question_id={question_id}")
            return
    else:
        logger.error(f"❌ Попытка получить кеш для некешируемого question_id {question_id} (cache_type={cache_type})")
        return
        
    full_ans_for_context = ""

    chat_id = message.chat.id
    if chat_id not in dialogue_context:
        dialogue_context[chat_id] = []
    dialogue_context[chat_id].append({"role": "user", "content": question})
    if chat_id not in count_questions_users:
        count_questions_users[chat_id] = 0
    count_questions_users[chat_id] += 1
    save_message_in_db(chat_id, "user", question)
    #mplusk1
    # Отправляем каждую часть с задержкой
    for i in arr:
        message_2 = bot.send_message(chat_id=message.chat.id, text=i)
        full_ans_for_context += i
        time.sleep(1)
    
    dialogue_context[chat_id].append({"role": "assistant", "content": full_ans_for_context})
    save_message_in_db(chat_id, "assistant", full_ans_for_context)
    
    # Получаем специализацию пользователя из базы данных
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (chat_id,))
    user_info = cursor.fetchone()
    conn.close()
    
    user_specialization = user_info[0] if user_info else specialization
    
    # Обрезаем ответ бота, чтобы избежать ошибок с длиной промпта
    truncated_answer = (full_ans_for_context[:4000] + '...') if len(full_ans_for_context) > 4000 else full_ans_for_context
    
    # Запускаем генерацию подсказанных вопросов
    await generate_and_show_suggested_questions(chat_id, question, truncated_answer, "", user_specialization)
    
    markup = types.InlineKeyboardMarkup()
    button = [types.InlineKeyboardButton(text="Ввести вопрос", callback_data="question_custom"),
                    types.InlineKeyboardButton(text="В начало", callback_data="start")
                ]
    markup.add(*button)
    bot.send_message(chat_id=message_2.chat.id, text = "Пожалуйста, выберите дальнейшее действие", reply_markup=markup)


    #mplusk2
async def websocket_question_from_user(question, message, specialization, question_id, show_suggested_questions=True, vector_store='auto'):
    chat_id = message.chat.id
    
    logger.info(f"websocket_question_from_user вызвана для пользователя {chat_id}, question_id={question_id}, question='{question[:50]}...'")
    
    if chat_id not in dialogue_context:
        dialogue_context[chat_id] = []
        logger.info(f"Инициализирован новый dialogue_context для пользователя {chat_id}")
    else:
        logger.info(f"Используем существующий dialogue_context для пользователя {chat_id}, размер: {len(dialogue_context[chat_id])}")
    
    # Добавляем новый вопрос пользователя в контекст
    dialogue_context[chat_id].append({"role": "user", "content": question})
    save_message_in_db(chat_id, "user", question)
    
    # Ограничиваем контекст до последних 6 пар сообщений (12 сообщений всего: 6 user + 6 assistant)
    if len(dialogue_context[chat_id]) > 12:
        dialogue_context[chat_id] = dialogue_context[chat_id][-12:]
    
    context_str = json.dumps(dialogue_context[chat_id], ensure_ascii=False, indent=4)
    if chat_id not in count_questions_users:
        count_questions_users[chat_id] = 0
    count_questions_users[chat_id] += 1

    try:
        logger.info(f"Подключаемся к RAG сервису: {WEBSOCKET_URL}")
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            logger.info(f"Отправляем данные в RAG сервис: question_id={question_id}")
            await websocket.send(question)                          # 1. question
            await websocket.send("")                                # 2. role (пустая строка)
            await websocket.send(specialization)                    # 3. specialization
            await websocket.send(str(question_id))                  # 4. question_id
            await websocket.send(context_str)                       # 5. context
            await websocket.send(str(count_questions_users[chat_id])) # 6. count
            await websocket.send(vector_store)                      # 7. vector_store
            logger.info(f"Данные отправлены в RAG сервис для пользователя {chat_id}, ожидаем ответ")

            try:
                message_2 = bot.send_message(message.chat.id, "Ожидайте ответа...")
                full_answer = ""
                last_send_time = time.time()
                answer_for_cache = []
                answer_for_countinue_dialog = ""
                empty_message_count = 0
                max_empty_messages = 10  # Максимум пустых сообщений подряд
                
                while True:
                    try:
                        # Добавляем таймаут для recv
                        answer_part = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Таймаут ожидания ответа от RAG сервиса для пользователя {chat_id}")
                        break
                    if answer_part:
                        empty_message_count = 0  # Сбрасываем счетчик пустых сообщений
                        full_answer += answer_part
                        # ИСПРАВЛЕНО: Отправляем ответ каждые 0.5 секунды вместо 1 секунды для более быстрого отображения
                        if time.time() - last_send_time >= 0.5:
                            try:
                                message_2 = bot.send_message(chat_id=message_2.chat.id, text=full_answer, parse_mode="Markdown")
                                answer_for_cache.append(full_answer)
                                answer_for_countinue_dialog += full_answer
                                full_answer = ""
                                last_send_time = time.time()
                                logger.debug(f"Отправлен промежуточный ответ пользователю {chat_id}")
                            except telebot.apihelper.ApiTelegramException as e:
                                # ИСПРАВЛЕНО: Обрабатываем все ошибки Telegram API, не только rate limit
                                if e.error_code == 429:
                                    retry_after = int(e.result.headers.get('Retry-After', 1))
                                    logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                                    time.sleep(retry_after)
                                    message_2 = bot.send_message(chat_id=message_2.chat.id, text=full_answer, parse_mode="Markdown")
                                    answer_for_countinue_dialog += full_answer
                                    answer_for_cache.append(full_answer)
                                    last_send_time = time.time()
                                    full_answer = ""
                                else:
                                    # Для других ошибок (например, неправильный Markdown) пробуем без форматирования
                                    logger.warning(f"Ошибка отправки сообщения с Markdown для пользователя {chat_id}: {e}. Отправляем без форматирования.")
                                    try:
                                        message_2 = bot.send_message(chat_id=message_2.chat.id, text=full_answer)
                                        answer_for_countinue_dialog += full_answer
                                        answer_for_cache.append(full_answer)
                                        last_send_time = time.time()
                                        full_answer = ""
                                    except Exception as inner_e:
                                        logger.error(f"Критическая ошибка отправки сообщения для пользователя {chat_id}: {inner_e}")
                            except Exception as e:
                                logger.error(f"Неожиданная ошибка при отправке сообщения для пользователя {chat_id}: {e}")
                    else:
                        # Пустое сообщение может означать конец потока
                        empty_message_count += 1
                        logger.debug(f"Получено пустое сообщение #{empty_message_count} от WebSocket для пользователя {chat_id}")
                        
                        # Если получили слишком много пустых сообщений подряд - выходим
                        if empty_message_count >= max_empty_messages:
                            logger.info(f"Получено {empty_message_count} пустых сообщений подряд, завершаем обработку для пользователя {chat_id}")
                            break
                            
                        # Основная защита - счетчик пустых сообщений выше
                            
                        # Если не закрыто, делаем небольшую паузу и продолжаем
                        await asyncio.sleep(0.1)
                        continue
                
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"WebSocket соединение закрыто для пользователя {chat_id}")
                # ИСПРАВЛЕНО: Всегда отправляем финальный ответ, даже если он пустой
                if full_answer:
                    try:
                        message_2 = bot.send_message(chat_id=message_2.chat.id, text=full_answer)
                        answer_for_cache.append(full_answer)
                        answer_for_countinue_dialog += full_answer
                        logger.info(f"Отправлен финальный ответ пользователю {chat_id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки финального ответа для пользователя {chat_id}: {e}")
                        # Пробуем отправить хотя бы уведомление об ошибке
                        try:
                            bot.send_message(chat_id, "❌ Произошла ошибка при отображении ответа. Ответ сохранен в истории.")
                        except:
                            pass
                elif not answer_for_countinue_dialog:
                    # Если вообще нет ответа, отправляем сообщение об ошибке
                    try:
                        bot.send_message(chat_id, "❌ Не удалось получить ответ от AI. Попробуйте еще раз.")
                        logger.warning(f"Пустой ответ от RAG для пользователя {chat_id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки сообщения об ошибке для пользователя {chat_id}: {e}")
                
                print("")
                # Кэшируем ответы на основе типа вопроса из БД
                cache_type = get_cache_type_for_question(question_id)
                
                if cache_type == 'by_specialization':
                    # НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
                    if specialization not in cache_by_specialization:
                        cache_by_specialization[specialization] = {}
                    cache_by_specialization[specialization][question_id] = answer_for_cache
                    logger.info(f"💾 Ответ сохранен в кэш: specialization='{specialization}', question_id={question_id}, фрагментов={len(answer_for_cache)}")
                elif cache_type == 'no_cache':
                    logger.info(f"Вопрос question_id={question_id} не кешируется (системный вопрос)")
                else:
                    logger.warning(f"Неизвестный тип кеша '{cache_type}' для question_id={question_id}")
                
            dialogue_context[chat_id].append({"role": "assistant", "content": answer_for_countinue_dialog})
            save_message_in_db(chat_id, "assistant", answer_for_countinue_dialog)
            
            # Снова ограничиваем контекст после добавления ответа ассистента
            if len(dialogue_context[chat_id]) > 12:
                dialogue_context[chat_id] = dialogue_context[chat_id][-12:]
                
            # Для свободного ввода (ID=888) показываем кнопку "Уточнить" и генерируем предложенные вопросы
            if question_id == 888:
                markup = types.InlineKeyboardMarkup()
                button = [
                    types.InlineKeyboardButton(text="Уточнить", callback_data="question_custom"),
                    types.InlineKeyboardButton(text="В начало", callback_data="start")
                ]
                markup.add(*button)
            else:
                # Для других типов вопросов показываем стандартные кнопки
                markup = types.InlineKeyboardMarkup()
                if(count_questions_users[chat_id] < 3):
                    button = [types.InlineKeyboardButton(text="Уточнить", callback_data="question_custom"),
                            types.InlineKeyboardButton(text="В начало", callback_data="start")
                        ]
                else:
                    button = [types.InlineKeyboardButton(text="В начало", callback_data="start")]
                markup.add(*button)
            #mplusk1
            truncated_answer = (answer_for_countinue_dialog[:4000] + '...') if len(answer_for_countinue_dialog) > 4000 else answer_for_countinue_dialog

            # Запускаем генерацию подсказанных вопросов для всех типов вопросов (включая ID=888)
            if show_suggested_questions:
                await generate_and_show_suggested_questions(chat_id, question, truncated_answer, "", specialization)

            # Разные сообщения для разных типов вопросов
            if question_id == 888:
                bot.send_message(chat_id=message_2.chat.id, text = "💬 Вы можете продолжить диалог, просто написав следующий вопрос", reply_markup=markup)
            else:
                bot.send_message(chat_id=message_2.chat.id, text = "Выберите дальнейшее действие", reply_markup=markup)
            
            logger.info(f"websocket_question_from_user завершена для пользователя {chat_id}")

    except Exception as e:
        logger.error(f"Ошибка в websocket_question_from_user для пользователя {chat_id}: {e}")
        bot.send_message(chat_id, f"❌ Произошла ошибка при обработке вопроса: {str(e)}")
        # Все равно создаем кнопку "В начало" для возврата
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="В начало", callback_data="start"))
        bot.send_message(chat_id, "Попробуйте позже или вернитесь в начало", reply_markup=markup)

current_timezone = time.tzname
current_timenow = datetime.now(moscow_tz).strftime("%H:%M")

@require_onboarding
def handle_feedback(message):
    user_feedback = message.text
    chat_id = message.chat.id
    
    # ИСПРАВЛЕНО: Правильная обработка данных для отображения
    username = message.from_user.username or "не указан"  # Здесь можно оставить для отображения
    user_fullname = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    user_fullname = user_fullname if user_fullname else "не указано"  # Для отображения

    feedback_text = (
        f"📨 *Новый отзыв от пользователя:*\n"
        f"👤 *Имя:* {user_fullname}\n"
        f"📍 *Username:* @{username}\n"
        f"📝 *Отзыв:* {user_feedback}"
    )

    try:
        feedback_bot.send_message(FEEDBACK_CHAT_ID, feedback_text, parse_mode="Markdown")
        bot.send_message(chat_id, "Спасибо! Ваш отзыв принят! 🎉")
    except Exception as e:
        bot.send_message(chat_id, "❌ Ошибка при отправке отзыва. Попробуйте позже.")
        logger.error(f"Ошибка при отправке отзыва: {e}")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="В начало", callback_data="start"))
    bot.send_message(chat_id, "Вы можете продолжить работу, вернувшись в начало:", reply_markup=markup)

@require_onboarding
def hadl_print_in_development_2(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    question = types.InlineKeyboardButton(text="В начало", callback_data="start")
    markup.add(question)
    bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text="Мы активно работаем над этой функцией, ждите в ближайшем будующем!\n Ваша команда разработки <3", reply_markup=markup)


@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "intern_questions_group")
def handle_intern_questions_group(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    questions = [
        types.InlineKeyboardButton(text="Лучшие практики", callback_data="qid_22"),
        types.InlineKeyboardButton(text="Что такое SDLC", callback_data="qid_23"),
        types.InlineKeyboardButton(text="Советы по тайм-менеджменту", callback_data="qid_24"),
        types.InlineKeyboardButton(text="В начало", callback_data="start")
    ]
    markup.add(*questions)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Выберите интересующий вас вопрос:",
        reply_markup=markup
    )

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("suggested_question_"))
def handle_suggested_question(call):
    chat_id = call.message.chat.id
    question_index = int(call.data.split("_")[-1])
    
    if chat_id in suggested_questions_storage and question_index < len(suggested_questions_storage[chat_id]):
        question = suggested_questions_storage[chat_id][question_index]
        
        # Очищаем контекст диалога для нового вопроса
        clear_dialog_context(chat_id)
        
        # Получаем специализацию
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (chat_id,))
        user_info = cursor.fetchone()
        conn.close()
        
        specialization = user_info[0] if user_info else "Не указана"
        
        bot.send_message(chat_id, f"Вы выбрали вопрос: {question}")
        
        # Отправляем вопрос на обработку (с предложенными вопросами)
        # ID=777 для выбранных предложенных вопросов
        vector_store = get_vector_store_for_specialization(specialization)
        asyncio.run(websocket_question_from_user(question, call.message, specialization, 777, show_suggested_questions=True, vector_store=vector_store))
        
        # Удаляем предложенные вопросы после выбора
        if chat_id in suggested_questions_storage:
            del suggested_questions_storage[chat_id]
            
        # Убираем кнопки с вопросами
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    else:
        bot.answer_callback_query(call.id, "Не удалось найти вопрос. Пожалуйста, попробуйте снова.")

def get_dialog_history_context(chat_id):
    """
    Получает последние 6 сообщений из базы данных и формирует контекст диалога
    Возвращает сообщения в хронологическом порядке (от старых к новым)
    """
    try:
        conn = sqlite3.connect(DATABASE_URL) 
        cursor = conn.cursor()

        # Запрос для получения последних 6 сообщений
        query = '''
        SELECT role, message, time 
        FROM Message_history
        WHERE user_id = ?
        ORDER BY time DESC
        LIMIT 6
        '''

        cursor.execute(query, (chat_id,))
        messages = cursor.fetchall()
        conn.close()
        
        logger.info(f"Получено {len(messages)} сообщений из БД для пользователя {chat_id}")
        
        # Переворачиваем список, чтобы сообщения шли в хронологическом порядке
        messages = list(reversed(messages))
        
        # Формируем контекст диалога
        dialog_context = []
        for role, message, time in messages:
            dialog_context.append({"role": role, "content": message})
            logger.debug(f"Добавлено в контекст: {role}: {message[:50]}...")
        
        logger.info(f"Сформирован контекст диалога: {len(dialog_context)} сообщений")
        return dialog_context
        
    except Exception as e:
        logger.error(f"Ошибка при получении истории диалога для пользователя {chat_id}: {e}")
        return []

#mplusk2
# Универсальный обработчик для всех текстовых сообщений
@require_onboarding
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_message(message):
    """
    Обрабатывает любое текстовое сообщение как вопрос к RAG системе с учетом истории диалога
    Этот обработчик имеет самый низкий приоритет и срабатывает только если нет других активных обработчиков
    """
    chat_id = message.chat.id
    question = message.text.strip()
    
    # Игнорируем команды (они уже обработаны другими хендлерами)
    if question.startswith('/'):
        return
    
    # Проверяем, есть ли активный step handler для этого пользователя
    try:
        if hasattr(bot, 'next_step_backend') and bot.next_step_backend.handlers.get(chat_id):
            logger.info(f"Пропускаем обработку - есть активный step handler для пользователя {chat_id}")
            return
    except Exception as e:
        logger.warning(f"Ошибка при проверке step handlers: {e}")
    
    logger.info(f"Начинаем обработку свободного текста для пользователя {chat_id}: '{question}'")
    
    # Получаем специализацию пользователя из базы данных
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (chat_id,))
    user_info = cursor.fetchone()
    conn.close()
    
    if user_info:
        specialization = user_info[0]
    else:
        # Если пользователь не найден в БД, используем значения по умолчанию
        specialization = "Не указана"
    
    # Для свободного ввода (ID=888) всегда загружаем свежий контекст из БД (последние 6 сообщений)
    logger.info(f"Загружаем свежий контекст диалога из БД для пользователя {chat_id}")
    history_context = get_dialog_history_context(chat_id)
    dialogue_context[chat_id] = history_context.copy()  # Перезаписываем контекст
    logger.info(f"Загружена история диалога для пользователя {chat_id}: {len(history_context)} сообщений")
    
    logger.info(f"Обрабатываем свободный вопрос от пользователя {chat_id}: {question[:50]}...")
    
    # Отправляем подтверждение получения вопроса
    bot.send_message(chat_id, f"🤖 Обрабатываю ваш вопрос: {question}")
    
    # Отправляем вопрос на обработку в RAG систему (с предложенными вопросами)
    question_id = 888  # ID для свободного ввода текста (отдельный промпт)
    vector_store = get_vector_store_for_specialization(specialization)
    asyncio.run(websocket_question_from_user(question, message, specialization, question_id, show_suggested_questions=True, vector_store=vector_store))

# Обработчик для показа полной истории сообщений
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "history_full")
def handle_full_history(call):
    print("!!! HISTORY_FULL HANDLER CALLED !!!")
    chat_id = call.message.chat.id
    logger.info(f"Обработчик history_full вызван для пользователя {chat_id}")
    print(f"!!! chat_id: {chat_id}, call.data: {call.data} !!!")
    
    try:
        # Получаем ВСЕ сообщения из базы данных
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        query = '''
        SELECT role, message, time 
        FROM Message_history
        WHERE user_id = ?
        ORDER BY time DESC
        LIMIT 50
        '''
        
        cursor.execute(query, (chat_id,))
        messages = cursor.fetchall()
        conn.close()
        
        if not messages:
            bot.answer_callback_query(call.id, "История сообщений пуста")
            return
        
        # Формируем полную историю (более компактно)
        history_text = f"📚 **Полная история сообщений**\n"
        history_text += f"Показано {len(messages)} последних сообщений:\n\n"
        
        # Переворачиваем список, чтобы показать от старых к новым
        messages = list(reversed(messages))
        
        for i, (role, message, timestamp) in enumerate(messages, 1):
            # Форматируем время
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%d.%m %H:%M")
            except Exception as e:
                logger.warning(f"Ошибка при форматировании timestamp '{timestamp}' в полной истории: {e}")
                formatted_time = timestamp[:16]
            
            # Определяем эмодзи
            emoji = "👤" if role == "user" else "🤖"
            
            # Обрезаем сообщения для компактности
            display_message = message
            if len(message) > 100:
                display_message = message[:97] + "..."
            
            history_text += f"{emoji} {formatted_time}: {display_message}\n\n"
        
        # Проверяем длину сообщения (Telegram ограничивает 4096 символов)
        if len(history_text) > 8000:
            history_text = history_text[:7900] + "\n\n... (история обрезана из-за ограничений длины)"
        
        # Кнопки навигации
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton(text="🗑 Очистить историю", callback_data="history_clear"),
            types.InlineKeyboardButton(text="◀️ Назад", callback_data="question_777")
        ]
        markup.add(*buttons)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=history_text,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении полной истории для пользователя {chat_id}: {e}")
        bot.answer_callback_query(call.id, "Ошибка при загрузке истории")

# Обработчик для очистки истории сообщений
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "history_clear")
def handle_clear_history(call):
    chat_id = call.message.chat.id
    logger.info(f"Обработчик history_clear вызван для пользователя {chat_id}")
    
    # Показываем подтверждение
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(text="✅ Да, очистить", callback_data="history_clear_confirm"),
        types.InlineKeyboardButton(text="❌ Отмена", callback_data="question_777")
    ]
    markup.add(*buttons)
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text="⚠️ **Подтверждение очистки истории**\n\nВы уверены, что хотите удалить всю историю сообщений?\n\n*Это действие нельзя отменить.*",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# Обработчик подтверждения очистки истории
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "history_clear_confirm")
def handle_clear_history_confirm(call):
    chat_id = call.message.chat.id
    
    try:
        # Удаляем всю историю пользователя
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Message_history WHERE user_id = ?", (chat_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        # Очищаем также контекст диалога в памяти
        clear_dialog_context(chat_id)
        
        # Показываем результат
        markup = types.InlineKeyboardMarkup(row_width=1)
        back_button = types.InlineKeyboardButton(text="◀️ Назад в меню", callback_data="personal_account")
        markup.add(back_button)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"✅ **История очищена**\n\nУдалено {deleted_count} сообщений.\n\nВаша история сообщений теперь пуста.",
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Пользователь {chat_id} очистил историю сообщений ({deleted_count} записей)")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке истории для пользователя {chat_id}: {e}")
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        back_button = types.InlineKeyboardButton(text="◀️ Назад", callback_data="question_777")
        markup.add(back_button)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="❌ **Ошибка при очистке истории**\n\nПопробуйте позже или обратитесь к администратору.",
            reply_markup=markup,
            parse_mode='Markdown'
        )

def get_user_profile_from_db(chat_id):
    """
    Извлекает специализацию пользователя из базы данных.
    Возвращает (specialization) или (None) если пользователь не найден.
    Первый элемент всегда None, так как роль больше не используется.
    """
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (chat_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return None, result[0]  # Возвращаем (None, specialization) для совместимости
    except Exception as e:
        logger.error(f"Ошибка при получении профиля пользователя {chat_id} из БД: {e}")
    return None, None


def get_vector_store_for_specialization(specialization):
    """Определяет vector_store на основе специализации пользователя"""
    if not specialization:
        return 'ensemble'
    
    spec_lower = specialization.lower()
    
    if 'аналитик' in spec_lower:
        return 'analyst'
    elif 'тестировщик' in spec_lower or 'qa' in spec_lower:
        return 'qa'
    elif 'web' in spec_lower or 'фронтенд' in spec_lower or 'frontend' in spec_lower:
        return 'web'
    elif 'java' in spec_lower:
        return 'java'
    elif 'python' in spec_lower:
        return 'python'
    else:
        return 'ensemble'  # По умолчанию используем ensemble для неизвестных специализаций


@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("qid_") or questions_loader.get_question_by_callback(call.data) is not None)
def handle_predefined_question_universal(call):
    """
    Универсальный обработчик для всех кнопок с вопросами.
    Загружает вопрос из `questions_loader` и обрабатывает его.
    """
    chat_id = call.message.chat.id
    callback_data = call.data
    logger.info(f"[{chat_id}] Received universal callback: {callback_data}")
    
    question_info = questions_loader.get_question_by_callback(callback_data)
    
    if not question_info:
        logger.warning(f"[{chat_id}] Question with callback '{callback_data}' not found.")
        bot.answer_callback_query(call.id, "Извините, этот вопрос больше не актуален.")
        return
        
    question_id = question_info['question_id']
    # Если у вопроса в БД указан prompt_id, используем его для RAG вместо устаревшего question_id
    prompt_id = question_info.get('prompt_id')
    rag_id = prompt_id if prompt_id else question_id
    question_text = question_info['question_text']
    vector_store_setting = question_info.get('vector_store', 'auto')
    
    # ИСПРАВЛЕНО: Распаковываем кортеж, а не используем как словарь
    _, specialization = get_user_profile_from_db(chat_id)
    if not specialization:
        logger.error(f"[{chat_id}] User profile not found, redirecting to onboarding.")
        redirect_to_onboarding(call.message)
        return
    
    logger.info(f"[{chat_id}] Handling question_id={rag_id}, Spec='{specialization}', VS='{vector_store_setting}'")
    
    # ДОБАВЛЕНО: Проверяем кеш перед отправкой в RAG на основе типа вопроса из БД
    cache_type = get_cache_type_for_question(question_id)
    logger.info(f"[{chat_id}] 🔍 ПРОВЕРКА КЭША: question_id={question_id}, cache_type='{cache_type}', specialization='{specialization}'")
    
    if cache_type == 'by_specialization':
        # НОВАЯ АРХИТЕКТУРА: cache_by_specialization[specialization][question_id] = answer
        if specialization in cache_by_specialization and question_id in cache_by_specialization[specialization]:
            cached_questions = list(cache_by_specialization[specialization].keys())
            logger.info(f"[{chat_id}] ✅ НАЙДЕН КЭШ для specialization='{specialization}', question_id={question_id}")
            logger.info(f"[{chat_id}] 📋 В кэше для '{specialization}' всего вопросов: {len(cached_questions)}")
            asyncio.run(handling_cached_requests(question_id, call.message, question_text, specialization))
            return
        else:
            spec_questions = len(cache_by_specialization.get(specialization, {}))
            total_specs = list(cache_by_specialization.keys())
            logger.info(f"[{chat_id}] ❌ КЭШ НЕ НАЙДЕН для specialization='{specialization}', question_id={question_id}")
            logger.info(f"[{chat_id}] 📊 В кэше '{specialization}': {spec_questions} вопросов, всего специализаций: {total_specs}")
    elif cache_type == 'no_cache':
        logger.info(f"[{chat_id}] 🚫 question_id={question_id} НЕ кешируется, отправляем в RAG")
    else:
        logger.info(f"[{chat_id}] 📭 Неопределенный тип кэша '{cache_type}' для question_id={question_id}")
        
    logger.info(f"[{chat_id}] 🚀 Отправляем в RAG для генерации нового ответа")
    
    # Если кеш не найден, отправляем в RAG
    typing_message = bot.send_message(chat_id, "<i>Печатаю...</i>", parse_mode='HTML')
    
    try:
        asyncio.run(websocket_question_from_user(
            question=question_text,
            message=typing_message,
            specialization=specialization,
            question_id=rag_id,
            show_suggested_questions=True,
            vector_store=vector_store_setting
        ))
    except Exception as e:
        logger.error(f"[{chat_id}] Error in universal handler for question_id={rag_id}: {e}")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=typing_message.message_id,
            text="Произошла ошибка при обработке вашего запроса. Попробуйте позже."
        )

# ================================================================
# Примечание: Блок запуска перенесен в конец файла для правильного
# порядка определения функций
# ================================================================

# -----------------------------------------------------------------------------
# HTTP-сервер для работы с кешем (порт 8007)
# -----------------------------------------------------------------------------

class TelegramBotAPIHandler(BaseHTTPRequestHandler):
    """Унифицированный HTTP-обработчик для всех API функций telegram бота (порт 8007)"""

    def _send_json(self, status: int, payload: dict):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_POST(self):
        if self.path == "/clear-cache":
            clear_all_cache()
            self._send_json(200, {"success": True, "message": "Кеш успешно очищен"})
        elif self.path == "/clear-cache-specialization":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                data = json.loads(body.decode("utf-8"))
                specialization = data.get("specialization", "")
                if not specialization:
                    self._send_json(400, {"success": False, "error": "Специализация не указана"})
                    return
                cleared_count = clear_cache_for_specialization(specialization)
                self._send_json(200, {"success": True, "message": f"Кеш для специализации '{specialization}' очищен", "cleared_count": cleared_count})
            except Exception as e:
                logger.error(f"Ошибка /clear-cache-specialization: {e}")
                self._send_json(500, {"success": False, "error": str(e)})
        elif self.path == "/reload-questions":
            try:
                logger.info("Получен API-запрос на перезагрузку кеша вопросов...")
                questions_loader.reload_questions()
                logger.info("Кеш вопросов успешно обновлен по API-запросу.")
                self._send_json(200, {"success": True, "message": "Кеш вопросов успешно перезагружен"})
            except Exception as e:
                logger.error(f"Ошибка при перезагрузке кеша по API: {e}", exc_info=True)
                self._send_json(500, {"success": False, "error": str(e)})
        elif self.path == "/send-message":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                data = json.loads(body.decode("utf-8"))
                message_text = data.get("message")
                if not message_text:
                    self._send_json(400, {"success": False, "error": "Сообщение не указано"})
                    return
                
                # Запускаем отправку в отдельном потоке, чтобы не блокировать ответ
                result = send_message_to_all_users(message_text)
                self._send_json(200 if result["success"] else 500, result)
            except json.JSONDecodeError:
                self._send_json(400, {"success": False, "error": "Некорректный JSON"})
            except Exception as e:
                logger.error(f"Ошибка в API /send-message: {e}", exc_info=True)
                self._send_json(500, {"success": False, "error": str(e)})
        else:
            self._send_json(404, {"success": False, "error": "Эндпоинт не найден. Доступные: /clear-cache, /clear-cache-specialization, /reload-questions, /send-message"})

    def do_OPTIONS(self):
        # CORS pre-flight
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def start_telegram_bot_api_server():
    """Запускает унифицированный HTTP-сервер для всех API функций на 8007."""
    logger.info("Запускаем Telegram Bot API сервер на http://0.0.0.0:8007 …")
    HTTPServer(("0.0.0.0", 8007), TelegramBotAPIHandler).serve_forever()

def __run_main():
    """Запуск вспомогательного HTTP-сервера и Telegram-бота."""
    api_thread = threading.Thread(target=start_cache_api_server, daemon=True)
    api_thread.start()
    bot.polling(none_stop=False)

# -----------------------------------------------------------------------------
# Перемещённый в самый конец файла блок запуска приложения
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    pass  # отключено, будет запущено в конце файла

# -----------------------------------------------------------------------------
# Функция генерации подсказанных вопросов через вспомогательный WebSocket
# -----------------------------------------------------------------------------

async def generate_and_show_suggested_questions(chat_id: int,
                                                user_question: str,
                                                bot_answer: str,
                                                role: str,
                                                specialization: str):
    """Получает список последующих вопросов от вспомогательного сервиса и
    показывает пользователю до трёх вариантов.

    Параметры
    ----------
    chat_id : int
        Telegram-ID пользователя
    user_question : str
        Последний вопрос пользователя
    bot_answer : str
        Полный ответ бота (может быть усечён до 2 000 символов)
    role, specialization : str
        Профиль пользователя для лучшего подбора подсказок
    """

    payload = {
        "user_question": user_question,
        "bot_answer": bot_answer,
        "specialization": specialization,
    }

    try:
        ws_url = "ws://127.0.0.1:8000/ws_suggest"
        logger.debug(f"[suggest] connect {ws_url} …; payload size ≈{len(json.dumps(payload))} B")

        async with websockets.connect(ws_url) as websocket:
            await websocket.send(json.dumps(payload, ensure_ascii=False))
            raw = await websocket.recv()
            suggestions = json.loads(raw)

            if isinstance(suggestions, dict) and suggestions.get("error"):
                logger.warning(f"[suggest] error from service: {suggestions['error']}")
                return

            if not isinstance(suggestions, list) or not suggestions:
                logger.info("[suggest] empty list – nothing to show")
                return

            # Cохраняем полный список, но выводим только первые 3 пункта
            suggested_questions_storage[chat_id] = suggestions

            buttons = [types.InlineKeyboardButton(text=str(i + 1),
                                                 callback_data=f"suggested_question_{i}")
                       for i in range(min(3, len(suggestions)))]

            markup = types.InlineKeyboardMarkup()
            markup.add(*buttons)

            preview_text = "\n".join([f"{i + 1}. {q}" for i, q in enumerate(suggestions[:3])])
            bot.send_message(chat_id,
                             f"💡 Возможно, вас заинтересует:\n{preview_text}",
                             reply_markup=markup)

    except Exception as exc:
        logger.error(f"[suggest] failure: {exc}")

# -----------------------------------------------------------------------------
# Запуск приложения (после определения всех функций)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    __run_main()



if __name__ == '__main__':
    logger.info("Запуск AI-ассистента...")
    
    # Запускаем унифицированный API Server на порту 8007
    logger.info("🚀 Запускаем Telegram Bot API Server на порту 8007...")
    api_thread = threading.Thread(target=start_telegram_bot_api_server, daemon=True)
    api_thread.start()
    logger.info("✅ Telegram Bot API Server запущен успешно")
    
    # Запускаем бота
    logger.info("🤖 Запускаем Telegram бот...")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        logger.critical(f"Критическая ошибка в главном цикле бота: {e}", exc_info=True)
        # В реальной системе здесь может быть логика для перезапуска
