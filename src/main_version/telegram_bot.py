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
    Определяет тип кеша для вопроса на основе поля specialization в БД.
    
    Returns:
        'by_specialization' - если specialization IS NULL (универсальный вопрос)
        'general' - если specialization IS NOT NULL (специфичный вопрос)
        'no_cache' - если вопрос не найден или не должен кешироваться
    """
    try:
        # Специальные ID которые не кешируются
        if question_id in [777, 888]:
            return 'no_cache'
        
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT specialization FROM Questions WHERE question_id = ?", (question_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            # Если вопрос не найден в БД, используем общий кеш
            logger.warning(f"Question ID {question_id} не найден в БД, используем общий кеш")
            return 'general'
        
        specialization = result[0]
        
        if specialization is None:
            # Универсальный вопрос - кешируем по специализации пользователя
            return 'by_specialization'
        else:
            # Специфичный вопрос - используем общий кеш
            return 'general'
            
    except Exception as e:
        logger.error(f"Ошибка при определении типа кеша для question_id {question_id}: {e}")
        return 'general'  # Fallback к общему кешу

def clear_all_cache():
    """
    Функция для полной очистки всех кешей.
    Очищает cache_dict и cache_by_specialization.
    """
    global cache_dict, cache_by_specialization
    
    try:
        # Очищаем основной кеш
        cache_dict.clear()
        
        # Очищаем кеш по специализациям
        cache_by_specialization.clear()
        
        logger.info("Все кеши успешно очищены")
        return True
    except Exception as e:
        logger.error(f"Ошибка при очистке кешей: {e}")
        return False

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
                    reminder BOOl DEFAULT TRUE,
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
    
    # Сохраняем специализацию и отмечаем онбординг как завершенный
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Users 
        SET Specialization = ?, is_onboarding = TRUE 
        WHERE user_id = ?
    ''', (spec_mapping[selected_spec], chat_id))
    conn.commit()
    conn.close()
    
    # Показываем сообщение об успешном завершении онбординга
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Отлично! Ваша специализация: {spec_mapping[selected_spec]}"
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
        print(f"Ошибка при получении напоминаний: {e}")
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
    username = message.from_user.username or "не указан"
    user_fullname = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    
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
        f"2️⃣ При первом входе выберите одну из ролей:\n"
        f"• PO/PM   • Лид компетенции   • Специалист   • Стажёр\n"
        f"3️⃣ Далее выберите специализацию:\n"
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
        types.InlineKeyboardButton(text="Задать вопрос", callback_data="menu_qr"),
        types.InlineKeyboardButton(text="🚀 Мини-приложение", web_app=types.WebAppInfo(url="https://restocorp.ru")),
        types.InlineKeyboardButton(text="Личный кабинет", callback_data="personal_account"),
        types.InlineKeyboardButton(text="GigaMentor", callback_data="giga_mentor")
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
        print(date_part)
        print(time_part)
        print(reminder_text)
        
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
                        print(f"Невозможно разобрать формат времени: {reminder_datetime}")
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
                        try:
                            full_answer = ""
                            while True:
                                answer_part = await websocket.recv()  # Получаем ответ частями
                                if answer_part:
                                    full_answer += answer_part
                                else:
                                    print("Получено пустое сообщение от WebSocket.")
                            
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
                                print(f"Сообщение отправлено пользователю {chat_id}")
                            except telebot.apihelper.ApiException as e:
                                # Если пользователь заблокировал бота, вы получите исключение
                                if "Forbidden: bot was blocked by the user" in str(e):
                                    print(f"Пользователь {chat_id} заблокировал бота.")
                                else:
                                    # Обработка других возможных ошибок
                                    print(f"Ошибка при отправке сообщения: {e}")
                except Exception as e:
                    print(f"Ошибка при обработке напоминания: {e}")
        
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

# Асинхронная функция для проверки и отправки напоминаний
async def check_for_daily_msg():
    logger.info("Запуск функции check_for_daily_msg")
    while True:
        try:
            # Получаем текущую дату и время в московском часовом поясе
            now = datetime.now(moscow_tz)
            current_day = now.weekday()  # 0 - понедельник, 4 - пятница
            current_time = now.strftime("%H:%M")
            
            # Логируем текущее состояние для отладки
            logger.debug(f"Текущий день недели: {current_day}, время: {current_time}")
            
            # Проверяем, пятница ли сейчас (4) и время 19:00
            if current_day == 4 and current_time == "19:00":
                logger.info("Наступило время для отправки еженедельных сообщений")
                conn = sqlite3.connect(DATABASE_URL)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Выбираем всех пользователей
                cursor.execute("SELECT * FROM Users WHERE reminder = TRUE;")
                users_results = cursor.fetchall()
                conn.close()
                
                logger.info(f"Найдено {len(users_results)} пользователей с включенными напоминаниями")

                # Отправляем сообщение каждому пользователю
                for user in users_results:
                    chat_id = user['user_id']
                    
                    logger.info(f"Обработка пользователя {chat_id}")
                    
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
                    specialization = 'Аналитик'
                    count_for_pro_activity = 101
                    question = 'without'
                    
                    try:
                        logger.debug(f"Подключение к WebSocket для пользователя {chat_id}")
                        async with websockets.connect(WEBSOCKET_URL) as websocket:
                            await websocket.send(question)         # 1. question
                            await websocket.send("")               # 2. role (пустая строка)
                            await websocket.send(specialization)   # 3. specialization
                            await websocket.send(str(question_id)) # 4. question_id
                            await websocket.send(context_str)      # 5. context
                            await websocket.send(str(count_for_pro_activity)) # 6. count
                            
                            full_answer = ""
                            try:
                                while True:
                                    answer_part = await websocket.recv()
                                    if answer_part:
                                        full_answer += answer_part
                                    else:
                                        logger.warning(f"Получено пустое сообщение от WebSocket для пользователя {chat_id}")
                            except websockets.exceptions.ConnectionClosed:
                                logger.info(f"WebSocket соединение закрыто для пользователя {chat_id}")
                                # Создаем клавиатуру
                                if full_answer is None or full_answer == "":
                                    full_answer = "История сообщений пустая"
                                    logger.warning(f"Пустой ответ от AI для пользователя {chat_id}")
                                    
                                markup = types.InlineKeyboardMarkup(row_width=1)
                                buttons = [
                                    types.InlineKeyboardButton(text="В начало", callback_data="start"),
                                    types.InlineKeyboardButton(text="Задать вопрос", callback_data="question_custom"),
                                ]
                                markup.add(*buttons)
                                
                                try:
                                    # Отправляем сообщение
                                    bot.send_message(chat_id=chat_id, text=full_answer, reply_markup=markup)
                                    logger.info(f"Еженедельное сообщение успешно отправлено пользователю {chat_id}")
                                except telebot.apihelper.ApiException as e:
                                    if "Forbidden: bot was blocked by the user" in str(e):
                                        logger.warning(f"Пользователь {chat_id} заблокировал бота")
                                    else:
                                        logger.error(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")
                    except Exception as e:
                        logger.error(f"Ошибка при обработке пользователя {chat_id}: {e}")
                
                # После отправки всем пользователям ждем до следующего дня, 
                # чтобы не отправить сообщения дважды (спим 23 часа)
                logger.info("Все еженедельные сообщения отправлены, ожидание до следующей проверки (23 часа)")
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
    specialization = specialization_mapping.get(data)
    
    # Обновляем Specialization
    cursor.execute("UPDATE Users SET Specialization = ? WHERE user_id = ?", (specialization, user_id))
    conn.commit()
    
    # Синхронизируем user_data с БД (только специализация)
    cursor.execute("SELECT Specialization FROM Users WHERE user_id = ?", (user_id,))
    user_db_data = cursor.fetchone()
    if user_db_data:
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]["specialization"] = user_db_data[0]
    
    bot.answer_callback_query(call.id, f"Специализация '{specialization}' успешно сохранена!")
    cursor.execute("SELECT user_id, Specialization FROM Users WHERE user_id = ?", (user_id,))
    users = cursor.fetchone()

    if users:
        print(f"User ID: {users[0]}, Specialization: {users[1]}")
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
    
    if cache_type == 'general' and question_id in cache_dict:
        asyncio.run(handling_cached_requests(question_id, call.message, question, specialization))
    elif cache_type == 'by_specialization' and question_id in cache_by_specialization:
        if specialization in cache_by_specialization[question_id]:
            asyncio.run(handling_cached_requests(question_id, call.message, question, specialization))
        else:
            asyncio.run(websocket_question_from_user(question, call.message, None, specialization, question_id))
    else:
        asyncio.run(websocket_question_from_user(question, call.message, None, specialization, question_id))


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
    
    if cache_type == 'general' and question_id in cache_dict:
        asyncio.run(handling_cached_requests(question_id, call.message, question, specialization))
    elif cache_type == 'by_specialization' and question_id in cache_by_specialization:
        if specialization in cache_by_specialization[question_id]:
            asyncio.run(handling_cached_requests(question_id, call.message, question, specialization))
        else:
            asyncio.run(websocket_question_from_user(question, call.message, None, specialization, question_id))
    else:
        asyncio.run(websocket_question_from_user(question, call.message, None, specialization, question_id))

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
    
    if cache_type == 'general' and question_id in cache_dict:
        asyncio.run(handling_cached_requests(question_id, call.message, question, specialization))
    elif cache_type == 'by_specialization' and question_id in cache_by_specialization:
        if specialization in cache_by_specialization[question_id]:
            asyncio.run(handling_cached_requests(question_id, call.message, question, specialization))
        else:
            asyncio.run(websocket_question_from_user(question, call.message, None, specialization, question_id))
    else:
        asyncio.run(websocket_question_from_user(question, call.message, None, specialization, question_id))



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
        print(f"!!! СОЗДАНИЕ КНОПОК: total_count = {total_count} !!!")
        if total_count > 10:
            print("!!! ДОБАВЛЯЕМ КНОПКУ 'Показать все' !!!")
            buttons.append(types.InlineKeyboardButton(text="📄 Показать все", callback_data="history_full"))
        
        print("!!! ДОБАВЛЯЕМ КНОПКУ 'Очистить историю' !!!")
        buttons.append(types.InlineKeyboardButton(text="🗑 Очистить историю", callback_data="history_clear"))
        buttons.append(types.InlineKeyboardButton(text="◀️ Назад в меню", callback_data="personal_account"))
        
        print(f"!!! ВСЕГО КНОПОК СОЗДАНО: {len(buttons)} !!!")
        for i, btn in enumerate(buttons):
            print(f"!!! КНОПКА {i}: text='{btn.text}', callback_data='{btn.callback_data}' !!!")
        
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
    asyncio.run(websocket_question_from_user(question, message, specialization, question_id, show_suggested_questions=True))

async def handling_cached_requests(question_id, message, question, specialization):
    print("Кешированное сообщение")

    cache_type = get_cache_type_for_question(question_id)
    
    if cache_type == 'general':
        arr = cache_dict[question_id]
    elif cache_type == 'by_specialization':
        arr = cache_by_specialization[question_id][specialization]
    else:
        logger.error(f"Попытка получить кеш для некешируемого question_id {question_id}")
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
    truncated_answer = (full_ans_for_context[:2000] + '...') if len(full_ans_for_context) > 2000 else full_ans_for_context
    
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
    print(f"websocket_question_from_user: question='{question}', question_id={question_id}")

    chat_id = message.chat.id
    print(f"websocket_question_from_user: chat_id={chat_id}")
    
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
                
                if cache_type == 'general':
                    cache_dict[question_id] = answer_for_cache
                    logger.info(f"Ответ сохранен в общий кеш для question_id={question_id}")
                elif cache_type == 'by_specialization':
                    if question_id not in cache_by_specialization:
                        cache_by_specialization[question_id] = {}
                    cache_by_specialization[question_id][specialization] = answer_for_cache
                    logger.info(f"Ответ сохранен в кеш по специализации для question_id={question_id}, specialization={specialization}")
                # cache_type == 'no_cache' - не кешируем (777, 888)
                
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
            truncated_answer = (answer_for_countinue_dialog[:2000] + '...') if len(answer_for_countinue_dialog) > 2000 else answer_for_countinue_dialog

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
print(f"Текущий часовой пояс: {current_timezone}")     
current_timenow = datetime.now(moscow_tz).strftime("%H:%M")
print(f"Текущий часовой пояс:{current_timenow}")

@require_onboarding
def handle_feedback(message):
    user_feedback = message.text
    chat_id = message.chat.id
    username = message.from_user.username or "не указан"
    user_fullname = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()

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
        print(f"Ошибка при отправке отзыва: {e}")

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
        asyncio.run(websocket_question_from_user(question, call.message, specialization, 777, show_suggested_questions=True))
        
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
    asyncio.run(websocket_question_from_user(question, message, specialization, question_id, show_suggested_questions=True))

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
        if len(history_text) > 4000:
            history_text = history_text[:3900] + "\n\n... (история обрезана из-за ограничений Telegram)"
        
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
    print("!!! HISTORY_CLEAR HANDLER CALLED !!!")
    chat_id = call.message.chat.id
    logger.info(f"Обработчик history_clear вызван для пользователя {chat_id}")
    print(f"!!! chat_id: {chat_id}, call.data: {call.data} !!!")
    
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
    
    if cache_type == 'general' and question_id in cache_dict:
        logger.info(f"[{chat_id}] Найден ответ в общем кеше для question_id={question_id}")
        asyncio.run(handling_cached_requests(question_id, call.message, question_text, specialization))
        return
    elif cache_type == 'by_specialization' and question_id in cache_by_specialization:
        if specialization in cache_by_specialization[question_id]:
            logger.info(f"[{chat_id}] Найден ответ в кеше по специализации для question_id={question_id}, specialization={specialization}")
            asyncio.run(handling_cached_requests(question_id, call.message, question_text, specialization))
            return
        else:
            logger.info(f"[{chat_id}] В кеше по специализации нет данных для question_id={question_id}, specialization={specialization}")
    elif cache_type == 'no_cache':
        logger.info(f"[{chat_id}] question_id={question_id} не кешируется, отправляем в RAG")
    else:
        logger.info(f"[{chat_id}] Кеш не найден для question_id={question_id}, отправляем в RAG")
    
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
# Новый блок запуска (должен располагаться **после** определения
# функции start_cache_api_server, чтобы избежать NameError)
# ================================================================

if False and __name__ == "__main__":
    # Запускаем вспомогательный HTTP-сервер кеша (порт 8007) в отдельном демоническом потоке
    api_thread = threading.Thread(target=start_cache_api_server, daemon=True)
    api_thread.start()

    # Запускаем Telegram-бот
    bot.polling(none_stop=False)

# -----------------------------------------------------------------------------
# HTTP-сервер для работы с кешем (порт 8007)
# -----------------------------------------------------------------------------

class CacheAPIHandler(BaseHTTPRequestHandler):
    """Обрабатывает POST /clear-cache для сброса кеша и /send-message для рассылки."""

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
        elif self.path == "/send-message":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                data = json.loads(body.decode("utf-8"))
                text = data.get("message", "")
                if not text:
                    self._send_json(400, {"success": False, "error": "Пустое сообщение"})
                    return
                result = send_message_to_all_users(text)
                self._send_json(200 if result["success"] else 500, result)
            except Exception as e:
                logger.error(f"Ошибка /send-message: {e}")
                self._send_json(500, {"success": False, "error": str(e)})
        elif self.path == "/reload-questions":
            try:
                questions_loader.reload_questions()
                self._send_json(200, {"success": True, "message": "Кеш вопросов успешно перезагружен"})
            except Exception as e:
                logger.error(f"Ошибка /reload-questions: {e}")
                self._send_json(500, {"success": False, "error": str(e)})
        else:
            self._send_json(404, {"success": False, "error": "Not found"})

    def do_OPTIONS(self):
        # CORS pre-flight
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def start_cache_api_server():
    """Запускает вспомогательный HTTP-сервер для управления кешем на 8007."""
    logger.info("Запускаем Cache-API сервер на http://0.0.0.0:8007 …")
    HTTPServer(("0.0.0.0", 8007), CacheAPIHandler).serve_forever()

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

class ControlAPIHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        if self.path == '/reload-questions':
            try:
                logger.info("Получен API-запрос на перезагрузку кеша вопросов...")
                questions_loader.reload_questions()
                logger.info("Кеш вопросов успешно обновлен по API-запросу.")
                self._send_json(200, {'success': True, 'message': 'Кеш вопросов успешно перезагружен'})
            except Exception as e:
                logger.error(f"Ошибка при перезагрузке кеша по API: {e}", exc_info=True)
                self._send_json(500, {'success': False, 'error': str(e)})
        elif self.path == '/send-message':
            try:
                data = json.loads(post_data)
                message_text = data.get('message')
                if not message_text:
                    self._send_json(400, {'success': False, 'error': 'No message provided'})
                    return
                
                # Запускаем отправку в отдельном потоке, чтобы не блокировать ответ
                threading.Thread(target=send_message_to_all_users, args=(message_text,)).start()
                
                self._send_json(200, {'success': True, 'message': 'Отправка сообщений запущена в фоновом режиме'})
            except json.JSONDecodeError:
                self._send_json(400, {'success': False, 'error': 'Invalid JSON'})
            except Exception as e:
                logger.error(f"Ошибка в API /send-message: {e}", exc_info=True)
                self._send_json(500, {'success': False, 'error': str(e)})
        else:
            self._send_json(404, {'success': False, 'error': 'Endpoint not found'})
    
    def do_OPTIONS(self):
        # CORS pre-flight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def start_control_api_server():
    """Запускает HTTP-сервер для управления ботом"""
    try:
        server_address = ('127.0.0.1', 8007)
        httpd = HTTPServer(server_address, ControlAPIHandler)
        logger.info(f"Запуск управляющего API-сервера на http://{server_address[0]}:{server_address[1]}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Не удалось запустить управляющий API-сервер: {e}", exc_info=True)

if __name__ == '__main__':
    logger.info("Запуск AI-ассистента...")
    
    # Запускаем управляющий API-сервер в отдельном потоке
    api_thread = threading.Thread(target=start_control_api_server, daemon=True)
    api_thread.start()
    
    # Запускаем бота
    logger.info("Запуск бесконечного опроса (polling)...")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        logger.critical(f"Критическая ошибка в главном цикле бота: {e}", exc_info=True)
        # В реальной системе здесь может быть логика для перезапуска
