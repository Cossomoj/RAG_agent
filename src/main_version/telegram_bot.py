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

# Токен Telegram-бота
bot = telebot.TeleBot(secret_key)
# Словарь для хранения данных пользователя
user_data = {}

def init_db():
    # Подключаемся к базе данных (или создаем ее, если она не существует)
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Создаем таблицу Users
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT NULL,
            user_fullname TEXT DEFAULT NULL,
            reminder BOOl DEFAULT TRUE,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            Role TEXT DEFAULT NULL,
            Specialization TEXT DEFAULT NULL,
            is_onboarding BOOLEAN DEFAULT FALSE NOT NULL
        )
        ''')

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
    
    # Создаем клавиатуру для выбора роли
    keyboard = types.InlineKeyboardMarkup()
    roles = [
        ("PO/PM", "role_for_db_po"),
        ("Лид компетенции", "role_for_db_lead"),
        ("Специалист", "role_for_db_spec"),
        ("Стажер", "role_for_db_intern")
    ]
    
    for role_name, callback_data in roles:
        keyboard.add(types.InlineKeyboardButton(text=role_name, callback_data=callback_data))
    # Добавляем кнопку "В начало"
    keyboard.add(types.InlineKeyboardButton(text="В начало", callback_data="start"))
    
    bot.send_message(chat_id, "Выберите вашу роль:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("role_for_db_"))
def handle_role_selection(call):
    chat_id = call.message.chat.id
    selected_role = call.data.replace("role_for_db_", "")
    
    # Сохраняем роль в базу данных
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    if selected_role == "po":
        # Если выбран PO/PM, автоматически устанавливаем специализацию
        cursor.execute('''
            UPDATE Users 
            SET Role = ?, Specialization = ?, is_onboarding = TRUE 
            WHERE user_id = ?
        ''', ("PO/PM", "PO/PM", chat_id))
        conn.commit()
        conn.close()
        
        # Показываем сообщение об успешном завершении онбординга
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="Отлично! Ваша роль: PO/PM\nСпециализация установлена автоматически."
        )
        # Вызываем меню
        handle_role(call)
        
    else:
        # Сохраняем роль
        role_mapping = {
            "lead": "Лид компетенции",
            "spec": "Специалист",
            "intern": "Стажер"
        }
        
        cursor.execute('''
            UPDATE Users 
            SET Role = ? 
            WHERE user_id = ?
        ''', (role_mapping[selected_role], chat_id))
        conn.commit()
        conn.close()
        
        # Создаем клавиатуру для выбора специализации
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
    
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="Теперь выберите вашу специализацию:",
            reply_markup=keyboard
        )

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

    # Получаем роль и специализацию из базы данных
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT Role, Specialization FROM Users WHERE user_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        role, specialization = result
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]["role"] = role 
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
    
    # Получаем текущую роль и специализацию из базы данных
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT Role, Specialization FROM Users WHERE user_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    
    role = result[0] if result and result[0] else "Не задана"
    specialization = result[1] if result and result[1] else "Не задана"
    
    # Создаем клавиатуру с кнопками
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text="Изменить роль", callback_data="onboarding"),
        types.InlineKeyboardButton(text="В начало", callback_data="start")
    )
    
    # Отправляем сообщение с текущими данными и кнопками
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"Ваша текущая роль: {role}\nВаша специализация: {specialization}\n\n"
             f"Для изменения ранее выбранной роли / специализации:\n"
             f"Выберите 'Изменить роль'",
            
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
                    except:
                        print(f"Невозможно разобрать формат времени: {reminder_datetime}")
                        continue
            
            # Сравниваем текущее время с временем напоминания
            if current_datetime == reminder_formatted:
                cursor.execute("DELETE FROM Reminder WHERE id_rem=?", (reminder['id_rem'],))
                conn.commit()
                chat_id = reminder['user_id']
                wanted_simbols = [".", ":"]
                context_str = reminder['reminder_text']
                if(not context_str):
                    context_str = "История сообщений пустая"
                question_id = 666
                role = 'Аналитик'   
                specialization = 'Специалист'
                count_for_pro_activity = 102
                question = 'without'
                
                try:
                    async with websockets.connect(WEBSOCKET_URL) as websocket:
                        await websocket.send(question) # Отправляем вопрос
                        await websocket.send(role)
                        await websocket.send(specialization)
                        await websocket.send(str(question_id))
                        await websocket.send(context_str)
                        await websocket.send(str(count_for_pro_activity))
                        try:
                            full_answer = ""
                            while True:
                                answer_part = await websocket.recv()  # Получаем ответ частями
                                if answer_part:
                                    for char in answer_part:
                                        if (char in wanted_simbols):
                                            answer_part += "\n"
                                    
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
            if current_day == 0 and current_time == "19:40":
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
                    wanted_simbols = [".", ":"]
                    
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
                    role = 'Аналитик'   
                    specialization = 'Специалист'
                    count_for_pro_activity = 101
                    question = 'without'
                    
                    try:
                        logger.debug(f"Подключение к WebSocket для пользователя {chat_id}")
                        async with websockets.connect(WEBSOCKET_URL) as websocket:
                            await websocket.send(question)
                            await websocket.send(role)
                            await websocket.send(specialization)
                            await websocket.send(str(question_id))
                            await websocket.send(context_str)
                            await websocket.send(str(count_for_pro_activity))
                            
                            full_answer = ""
                            try:
                                while True:
                                    answer_part = await websocket.recv()
                                    if answer_part:
                                        for char in answer_part:
                                            if (char in wanted_simbols):
                                                answer_part += "\n"
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

# Обработчик нажатия кнопки Выбор роли
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "menu_qr")
def handle_role(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    
    # Получаем роль и специализацию из базы данных
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT Role, Specialization FROM Users WHERE user_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result[0] or not result[1]:
        # Если роль или специализация не установлены, запускаем онбординг
        redirect_to_onboarding(call.message)
        return
    
    role = result[0]
    specialization = result[1]
    
    # Сохраняем данные в user_data для использования в других функциях
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]["role"] = role
    user_data[chat_id]["specialization"] = specialization
    
    # Показываем соответствующие вопросы в зависимости от роли и специализации
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if role == "PO/PM":
        questions = [
            types.InlineKeyboardButton(text="Что я могу ожидать от специалиста", callback_data="po_question_1"),
            types.InlineKeyboardButton(text="Что я могу ожидать от лида компетенции", callback_data="po_question_2"),
            types.InlineKeyboardButton(text="Что ожидается от меня", callback_data="po_question_3"),
            types.InlineKeyboardButton(text="Прочее", callback_data="intern_questions_group"),
            types.InlineKeyboardButton(text="Что еще ты умеешь?", callback_data="question_777"),
            types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom"),
            types.InlineKeyboardButton(text="В начало", callback_data="start")
        ]
    elif role == "Лид компетенции":
        if specialization == "Аналитик":
            questions = [
                types.InlineKeyboardButton(text="Что я могу ожидать от специалиста ", callback_data="question_4"),
                types.InlineKeyboardButton(text="Что я могу ожидать от своего PO/PM ", callback_data="question_5"),
                types.InlineKeyboardButton(text="Что ожидается от меня", callback_data="questions_group_1"),
                types.InlineKeyboardButton(text="Прочее", callback_data="questions_group_2"),
                types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom"),
                types.InlineKeyboardButton(text="В начало", callback_data="start")
            ]
        else:
            questions = [
                types.InlineKeyboardButton(text="Что я могу ожидать от специалиста ", callback_data="question_18"),
                types.InlineKeyboardButton(text="Что я могу ожидать от своего PO/PM ", callback_data="question_19"),
                types.InlineKeyboardButton(text="Что ожидается от меня", callback_data="question_20"),
                types.InlineKeyboardButton(text="Прочее", callback_data="questions_group_2"),
                types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom"),
                types.InlineKeyboardButton(text="В начало", callback_data="start")
            ]
    elif role == "Стажер":
        questions = [
            types.InlineKeyboardButton(text="Что я могу ожидать от PO/PM", callback_data="question_1"),
            types.InlineKeyboardButton(text="Что я могу ожидать от своего лида", callback_data="question_2"),
            types.InlineKeyboardButton(text="Рекомендации для стажеров", callback_data="question_21"),
            types.InlineKeyboardButton(text="Посмотреть матрицу компетенций", callback_data="question_3"),
            types.InlineKeyboardButton(text="Прочее", callback_data="intern_questions_group"),
            types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom"),
            types.InlineKeyboardButton(text="В начало", callback_data="start")
        ]
    else:  # Специалист
        questions = [
            types.InlineKeyboardButton(text="Что я могу ожидать от своего PO/PM", callback_data="question_1"),
            types.InlineKeyboardButton(text="Что я могу ожидать от своего Лида", callback_data="question_2"),
            types.InlineKeyboardButton(text="Посмотреть матрицу компетенций", callback_data="question_3"),
            types.InlineKeyboardButton(text="Прочее", callback_data="intern_questions_group"),
            types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom"),
            types.InlineKeyboardButton(text="В начало", callback_data="start")
        ]
    
    markup.add(*questions)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(f"Вы выбрали роль: {role}\nСпециализация: {specialization}\n\n"
              f"Чтобы задать вопрос:\n"
              f"• Выберите из списка готовых вопросов или 'Прочее' с дополнительными темами\n"
              f"• Или нажмите 'Ввести свой вопрос' для свободного вопроса"),
        reply_markup=markup
    )

def clear_dialog_context(chat_id):
    if chat_id in dialogue_context:
        dialogue_context[chat_id] = []
    if chat_id in count_questions_users:
        count_questions_users[chat_id] = 0

# Обработчик выбора роли
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "menu_r")
def choose_menu(call):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    roles = [
        types.InlineKeyboardButton(text="Аналитик", callback_data="specsql_analyst"),
        types.InlineKeyboardButton(text="Тестировщик", callback_data="specsql_tester"),
        types.InlineKeyboardButton(text="WEB", callback_data="specsql_web"),
        types.InlineKeyboardButton(text="Java", callback_data="specsql_java"),
        types.InlineKeyboardButton(text="Python", callback_data="specsql_python"),
        types.InlineKeyboardButton(text="В начало", callback_data="start"),
    ]
    markup.add(*roles)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите роль:", reply_markup=markup)

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
    cursor.execute("UPDATE Users SET role = ? WHERE user_id = ?", (specialization, user_id))
    conn.commit()
    bot.answer_callback_query(call.id, f"Специализация '{specialization}' успешно сохранена!")
    cursor.execute("SELECT user_id, role FROM Users WHERE user_id = ?", (user_id,))
    users= cursor.fetchone()

    if users:
        # user_data — это кортеж, например: (123456789, "Аналитик")
        print(f"User ID: {users[0]}, Role: {users[1]}")
    conn.close()


    # Возврат в меню
    handle_start(call)



# Обработчик выбора роли
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("role_"))
def choose_role(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    role_mapping = {
        "role_PM": "PO/PM",
        "role_lead": "Лид компетенций",
        "role_employee": "Специалист"
    }
    selected_role = role_mapping.get(call.data)
    user_data[call.message.chat.id] = {"role": selected_role, "specialization": None}
    if(user_data[call.message.chat.id]["role"] == "PO/PM"):
        user_data[call.message.chat.id]["specialization"] = "PO/PM"

    bot.clear_step_handler_by_chat_id(call.message.chat.id)

    if selected_role in ["Лид компетенций", "Специалист"]:
        markup = types.InlineKeyboardMarkup(row_width=1)
        specializations = [
            types.InlineKeyboardButton(text="Аналитик", callback_data="spec_analyst"),
            types.InlineKeyboardButton(text="Тестировщик", callback_data="spec_tester"),
            types.InlineKeyboardButton(text="WEB", callback_data="spec_web"),
            types.InlineKeyboardButton(text="Java", callback_data="spec_java"),
            types.InlineKeyboardButton(text="Python", callback_data="spec_python"),
            types.InlineKeyboardButton(text="В начало", callback_data="start"),

        ]
        markup.add(*specializations)
        
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали роль: {selected_role}\nТеперь выберите специализацию:", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        quesions = [
            types.InlineKeyboardButton(text="Что я могу ожидать от специалиста", callback_data="po_question_1"),
            types.InlineKeyboardButton(text="Что я могу ожидать от лида компетенции", callback_data="po_question_2"),
            types.InlineKeyboardButton(text="Что ожидается от меня", callback_data="po_question_3"),
            types.InlineKeyboardButton(text="Что еще ты умеешь?", callback_data="question_777"),
            types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom"),
            types.InlineKeyboardButton(text="В начало", callback_data="start")

        ]
        markup.add(*quesions)
        bot.edit_message_text(chat_id = call.message.chat.id, message_id=call.message.message_id, text=(
        "Вы находитесь в разделе напоминания\n\n"
        "Выберите:\n"
        "•'Запланировать сообщение на тему' - для создания единоразового сообщения\n"
        "•'Регулярные сообщения' - для настройки регулярных сообщений\n"
        "•'Мои уведомления' - для просмотра существующих уведомлений"
    ), reply_markup=markup)

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
            types.InlineKeyboardButton(text="Поиск кандидатов на работу", callback_data="group_1_question_1"),
            types.InlineKeyboardButton(text="Проведение собеседований", callback_data="group_1_question_2"),
            types.InlineKeyboardButton(text="Работа со стажерами/джунами", callback_data="group_1_question_3"),
            types.InlineKeyboardButton(text="Проведение 1-2-1", callback_data="group_1_question_4"),
            types.InlineKeyboardButton(text="Проведение встреч компетенции", callback_data="group_1_question_5"),
            types.InlineKeyboardButton(text="В начало", callback_data="start")
        ]
        markup.add(*questions)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали категорию: \nТеперь выберите вопрос:", reply_markup=markup)
    elif switcher == 1:
        questions = [
            types.InlineKeyboardButton(text="Построение структуры компетенции", callback_data="group_2_question_1"),
            types.InlineKeyboardButton(text="Создание ИПР", callback_data="group_2_question_2"),
            types.InlineKeyboardButton(text="Как провести онбординг", callback_data="group_2_question_3"),
            types.InlineKeyboardButton(text="Оптимизация процессов разработки", callback_data="group_2_question_4"),
            types.InlineKeyboardButton(text="Советы по тайм-менеджменту", callback_data="group_2_question_5"),
            types.InlineKeyboardButton(text="В начало", callback_data="start")
        ]
        markup.add(*questions)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали категорию: \nТеперь выберите вопрос:", reply_markup=markup)
    
@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("group_1"))
def handle_predefined_question_group_1(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    role = ""
    specialization = ""
    question_id = 777
    
    if call.message.chat.id not in user_data:
        user_data[call.message.chat.id] = {"role": "Специалист", "specialization": "Аналитик"}

    role = user_data[call.message.chat.id]['role']
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

    if (question_id in cache_dict):
            handling_cached_requests(question_id, call.message, question, specialization)
    elif (question_id in cache_by_specialization):
        if(specialization in cache_by_specialization[question_id]):
            handling_cached_requests(question_id, call.message, question, specialization)
        else:
            asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))
    else:
        asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))


@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("group_2"))
def handle_predefined_question_group_2(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    role = ""
    specialization = ""
    question_id = 777
    
    if call.message.chat.id not in user_data:
        user_data[call.message.chat.id] = {"role": "Специалист", "specialization": "Аналитик"}

    role = user_data[call.message.chat.id]['role']
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

    if (question_id in cache_dict):
            handling_cached_requests(question_id, call.message, question, specialization)
    elif (question_id in cache_by_specialization):
        if(specialization in cache_by_specialization[question_id]):
            handling_cached_requests(question_id, call.message, question, specialization)
        else:
            asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))
    else:
        asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data.startswith("po_question"))
def handle_predefined_question_group_2(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    role = ""
    specialization = ""
    question_id = 777
    
    if call.message.chat.id not in user_data:
        user_data[call.message.chat.id] = {"role": "PO/PM", "specialization": "PO/PM"}

    role = user_data[call.message.chat.id]['role']
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

    if (question_id in cache_dict):
            handling_cached_requests(question_id, call.message, question, specialization)
    elif (question_id in cache_by_specialization):
        if(specialization in cache_by_specialization[question_id]):
            handling_cached_requests(question_id, call.message, question, specialization)
        else:
            asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))
    else:
        asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))



@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data in ["question_1", "question_2", "question_3", "question_4", "question_5", "question_18", "question_19", "question_20", "question_21"])
def handle_predefined_question(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    role = ""
    specialization = ""
    question_id = 777
    
    if call.message.chat.id not in user_data:
        user_data[call.message.chat.id] = {"role": "Специалист", "specialization": "Аналитик"}

    role = user_data[call.message.chat.id]['role']
    specialization = user_data[call.message.chat.id]['specialization']
    
    
    if call.data == "question_1":
        question = "Что я могу ожидать от своего PO/PM?"
        question_id = 1
    elif call.data == "question_2":
        question = "Что я могу ожидать от своего Лида?"
        question_id = 2
    elif(call.data == "question_3"):
        question = "Посмотерть матрицу компетенций"
        question_id = 3
    elif call.data == "question_4":
        question = "Что я могу ожидать от специалиста "
        question_id = 4
    elif call.data == "question_5":
        question = "Что я могу ожидать от своего PO/PM "
        question_id = 5
    if call.data == "question_18":
        question = "Что я могу ожидать от специалиста ?"
        question_id = 18
    elif call.data == "question_19":
        question = "Что я могу ожидать от своего PO/PM "
        question_id = 19
    elif(call.data == "question_20"):
        question = "Что ожидается от меня?"
        question_id = 20
    elif(call.data == "question_21"):
        question = "Рекомендации для стажеров"
        question_id = 21
    

    if (question_id in cache_dict):
            handling_cached_requests(question_id, call.message, question, specialization)
    elif (question_id in cache_by_specialization):
        if(specialization in cache_by_specialization[question_id]):
            handling_cached_requests(question_id, call.message, question, specialization)
        else:
            asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))
    else:
        asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "question_777")
def hadl_print_in_development(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    question = types.InlineKeyboardButton(text="В начало", callback_data="start")
    markup.add(question)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Мы активно работаем над этой функцией, ждите в ближайшем будующем!\nВаша команда разработки <3", reply_markup=markup)

@require_onboarding
@bot.callback_query_handler(func=lambda call: call.data == "question_custom")
def ask_custom_question(call):
    bot.send_message(call.message.chat.id, "Введите ваш вопрос:")
    bot.register_next_step_handler(call.message, process_custom_question)


def process_custom_question(message):   
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {"role": "Специалист", "specialization": "Аналитик"}

    role = user_data[message.chat.id]['role']
    specialization = user_data[message.chat.id]['specialization']
    if(not specialization):
        specialization = "Аналитик"

    question_id = 777
    question = message.text
    asyncio.run(websocket_question_from_user(question, message, role, specialization, question_id))

def handling_cached_requests(question_id, message, question, specialization):
    print("Кешированное сообщение")

    if (question_id not in [1, 2, 3, 4, 5, 18, 19, 20]):
        arr = cache_dict[question_id]
    else:
        arr = cache_by_specialization[question_id][specialization]
    full_ans_for_context = ""

    chat_id = message.chat.id
    if chat_id not in dialogue_context:
        dialogue_context[chat_id] = []
    dialogue_context[chat_id].append({"role": "user", "content": question})
    if chat_id not in count_questions_users:
        count_questions_users[chat_id] = 0
    count_questions_users[chat_id] += 1
    save_message_in_db(chat_id, "user", question)

    # Отправляем каждую часть с задержкой
    for i in arr:
        message_2 = bot.send_message(chat_id=message.chat.id, text=i)
        full_ans_for_context += i
        time.sleep(1)
    
    dialogue_context[chat_id].append({"role": "assistant", "content": full_ans_for_context})
    save_message_in_db(chat_id, "assistant", full_ans_for_context)
    markup = types.InlineKeyboardMarkup()
    button = [types.InlineKeyboardButton(text="Ввести вопрос", callback_data="question_custom"),
                    types.InlineKeyboardButton(text="В начало", callback_data="start")
                ]
    markup.add(*button)
    bot.send_message(chat_id=message_2.chat.id, text = "Пожалуйста, выберите дальнейшее действие", reply_markup=markup)

async def websocket_question_from_user(question, message, role, specialization, question_id):
    print(question)
    wanted_simbols = [".", ":"]

    chat_id = message.chat.id
    print(chat_id)
    if chat_id not in dialogue_context:
        dialogue_context[chat_id] = []
    dialogue_context[chat_id].append({"role": "user", "content": question})
    save_message_in_db(chat_id, "user", question)
    context_str = json.dumps(dialogue_context[chat_id], ensure_ascii=False, indent=4)
    if chat_id not in count_questions_users:
        count_questions_users[chat_id] = 0
    count_questions_users[chat_id] += 1

    async with websockets.connect(WEBSOCKET_URL) as websocket:
        await websocket.send(question) # Отправляем вопрос
        await websocket.send(role)
        await websocket.send(specialization)
        await websocket.send(str(question_id))
        await websocket.send(context_str)
        await websocket.send(str(count_questions_users[chat_id]))

        try:
            message_2 = bot.send_message(message.chat.id, "Ожидайте ответа...")
            full_answer = ""
            last_send_time = time.time()
            answer_for_cache = []
            answer_for_countinue_dialog = ""
            while True:
                answer_part = await websocket.recv()  # Получаем ответ частями
                if answer_part:
                    for char in answer_part:
                        if (char in wanted_simbols):
                            answer_part += "\n"

                    full_answer += answer_part
                    if time.time() - last_send_time >= 1:
                        try:
                            message_2 = bot.send_message(chat_id=message_2.chat.id, text=full_answer, parse_mode="Markdown")
                            answer_for_cache.append(full_answer)
                            answer_for_countinue_dialog += full_answer
                            full_answer = ""
                            last_send_time = time.time()
                        except telebot.apihelper.ApiTelegramException as e:
                            if e.error_code == 429:
                                retry_after = int(e.result.headers.get('Retry-After', 1))
                                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                                time.sleep(retry_after)
                                message_2 = bot.send_message(chat_id=message_2.chat.id, text=full_answer, parse_mode="Markdown")
                                answer_for_countinue_dialog += full_answer
                                answer_for_cache.append(full_answer)
                                last_send_time = time.time()
                                full_answer = ""
                else:
                    print("Получено пустое сообщение от WebSocket.")
            
        except websockets.exceptions.ConnectionClosed:
            if (full_answer != ""):
                message_2 = bot.send_message(chat_id=message_2.chat.id, text=full_answer)
                answer_for_cache.append(full_answer)
                answer_for_countinue_dialog += full_answer
            print("")
            if(question_id != 777):
                if(question_id not in [1, 2, 3, 4, 5, 18, 19, 20]):
                    cache_dict[question_id] = answer_for_cache
                else:
                    if question_id not in cache_by_specialization:
                        cache_by_specialization[question_id] = {}
                    cache_by_specialization[question_id][specialization] = answer_for_cache
            
        dialogue_context[chat_id].append({"role": "assistant", "content": answer_for_countinue_dialog})
        save_message_in_db(chat_id, "assistant", answer_for_countinue_dialog)
        markup = types.InlineKeyboardMarkup()
        if(count_questions_users[chat_id] < 6):
            button = [types.InlineKeyboardButton(text="Ввести вопрос", callback_data="question_custom"),
                    types.InlineKeyboardButton(text="В начало", callback_data="start")
                ]
        else:
            button = [types.InlineKeyboardButton(text="В начало", callback_data="start")]

        markup.add(*button)
        bot.send_message(chat_id=message_2.chat.id, text = "Пожалуйста, выберите дальнейшее действие", reply_markup=markup)

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
        types.InlineKeyboardButton(text="Лучшие практики", callback_data="intern_group_question_1"),
        types.InlineKeyboardButton(text="Что такое SDLC", callback_data="intern_group_question_2"),
        types.InlineKeyboardButton(text="Советы по тайм-менеджменту", callback_data="intern_group_question_3"),
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
@bot.callback_query_handler(func=lambda call: call.data.startswith("intern_group_question_"))
def handle_intern_group_questions(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    role = ""
    specialization = ""
    question_id = 777
    
    if call.message.chat.id not in user_data:
        user_data[call.message.chat.id] = {"role": "Стажер", "specialization": "Аналитик"}

    role = user_data[call.message.chat.id]['role']
    specialization = user_data[call.message.chat.id]['specialization']
    
    if call.data == "intern_group_question_1":
        question = "Лучшие практики для стажеров"
        question_id = 22
    elif call.data == "intern_group_question_2":
        question = "Что такое SDLC"
        question_id = 23
    elif call.data == "intern_group_question_3":
        question = "Советы по тайм-менеджменту для стажеров"
        question_id = 24

    if (question_id in cache_dict):
        handling_cached_requests(question_id, call.message, question, specialization)
    elif (question_id in cache_by_specialization):
        if(specialization in cache_by_specialization[question_id]):
            handling_cached_requests(question_id, call.message, question, specialization)
        else:
            asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))
    else:
        asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))

# Простой HTTP сервер для API очистки кеша
class CacheAPIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/clear-cache':
            try:
                result = clear_all_cache()
                response = {'success': True, 'message': 'Кеш успешно очищен'}
                self.send_response(200)
            except Exception as e:
                response = {'success': False, 'error': str(e)}
                self.send_response(500)
            
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def start_cache_api_server():
    server = HTTPServer(('localhost', 8007), CacheAPIHandler)
    logger.info("Cache API сервер запущен на порту 8007")
    server.serve_forever()

# Запускаем API сервер в отдельном потоке
api_thread = threading.Thread(target=start_cache_api_server, daemon=True)
api_thread.start()

bot.polling(none_stop=False)
