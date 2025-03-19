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
from datetime import datetime, UTC 
import threading
import pytz
from sqlalchemy import create_engine # для базы данных
from sqlalchemy.orm import sessionmaker # для базы данных
load_dotenv()

WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"
moscow_tz = pytz.timezone('Europe/Moscow')

# для базы данных
DATABASE_URL = "sqlite:////app/src/main_version/DATABASE_URL"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# конец

dialogue_context = {}
count_questions_users = {}

secret_key = os.getenv("TELEGRAM_API_KEY")
cache_dict = {3 : ["Уровень Junior\nСофты:\n1. Желание учиться которое подтверждается делом.(Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком.(Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Многозадачность - в термин (многозадачность) вкладывается НЕ возможность в каждый момент времени думать сразу о нескольких задачах, а возможность переключаться между задачами/проектами (от 2х - оптимально, до 5ти - максимально) без сильной потери эффективности (что какая-то потеря эффективности будет - факт).",
                    "Харды:\n1. Знание json нотации.\n2. Знание Postman и Curl (любого инструмента отправки http запросов).\n3. Умение использовать User Story и Use Case.\n4. Понимание клиент-серверного взаимодействия.\n5. Владение  любым инструментом разметки макетов (пэинт/фотошоп/автокад/...).",
                    "Уровень Junior+ Middle-\nСофты:\n1. Желание учиться которое  подтверждается делом (Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком (Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Многозадачность (определение см. выше)",
                    "Харды:\n1. Знание json нотации.\n2. Знание Postman и Curl. (любого инструмента отправки http запросов).\n3. Умение использовать User Story и Use Case.\n4. Понимание клиент-серверного взаимодействия.\n5. Владение  любым инструментом разметки макетов (пэинт/фотошоп/автокад/...).\n6. Построение сиквенс диаграмм в UML нотации.\n7. Умение работать со сваггером/openAPI cхемами.",
                    "Уровень Middle+\nСофты:\n1. Желание учиться которое подтверждается делом.(Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком.(Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Умениедоносить своимысли до коллег.\n5. Умение объяснить заказчику возможные варианты реализации.",
                    "6. Многозадачность\n7. Умение выявить у себя недостаток знаний в определенном домене и закрыть его при необходимости\nХарды:\n1. Знание json и xml нотации.\n2. Знание Postman и Curl. Любого инструмента отправки http запросов.\n3. Умение использовать User Story и Use Case.\n4. Понимание клиент-серверного взаимодействия.\n5. Владение любым инструментом разметки макетов (пэинт/фотошоп/автокад/...).",
                    "6. Построение сиквенс диаграмм в UML нотации.\n7. Умение работать со сваггером/openAPI cхемами.\n8. Понимание синхронного и асинхронног взаимодействия на уровне, не просто знания протоколов, а для чего они реально нужны, когда применять одно, когда другое.\n9. Опыт работы с очередями (Rabbit, Kafka).\n10. Понимание плюсов и минусов микросервисов и монолита.",
                    "11. Понимание стейтлесс и стэйтфул сервисов.\n12. Понимание подхода API first.\n13. Опыт работы с Charles. (перехват и анализ клиент-серверных запросов).\n14. Опыт работы с реляционными и нереляционными базами, понимание разницы между ними, умение писать простые запросы.\n15. Умение программировать (скрипты, REST api методы) на скриптовом языке (python, js).\n16. Понимание принципов работы LLM.",
                    "Уровень Senior\nСофты:\n1. Желание учиться которое подтверждается делом.(Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком.(Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Умениедоносить своимысли до коллег.\n5. Умение объяснить заказчику возможные варианты реализации.",
                    "6. Многозадачность\n7. Умение выявить у себя недостаток знаний в определенном домене и закрыть его при необходимости.\n8. Понимание как работа влияет на проект в целом: что нужно сделать в первом приоритете, что можно поставить на паузу, чего можно не делать вообще.\n9. Умение сглаживать напряжение внутри команды, умение объяснить команде, что могут быть задачи интересные, но не полезные для проекта",
                    "Харды:\n1. Знание json и xml нотации.\n2. Знание Postman и Curl. Любого инструмента отправки http запросов.\n3. Умение использовать User Story и Use Case.\n4. Понимание клиент-серверного взаимодействия.\n5. Владение любым инструментом разметки макетов (пэинт/фотошоп/автокад/...).\n6. Построение сиквенс диаграмм в UML нотации.\n7. Умение работать со сваггером/openAPI cхемами.",
                    "8. Понимание синхронного и асинхронног взаимодействия на уровне, не просто знания протоколов, а для чего они реально нужны, когда применять одно, когда другое.\n9. Опыт работы с очередями (Rabbit, Kafka).\n10. Понимание плюсов и минусов микросервисов и монолита.\n11. Понимание стейтлесс и стэйтфул сервисов.\n12. Понимание подхода API first.",
                    "13. Опыт работы с Charles. (перехват и анализ клиент-серверных запросов).\n14. Опыт работы с реляционными и нереляционными базами, понимание разницы между ними, умение писать простые запросы.\n15. Умение программировать (скрипты, REST api методы) на скриптовом языке (python, js).\n16. Понимание принципов работы LLM.",
                    "17. Умение построить (возможно с командой) и понимать архитектуру проекта, понимать, что можно легко доработать, а что потребует серьезного изменения скоупа проекта.\n18. Понимание взаимодействия микросервисов между собой (ресты, очереди, service mesh).\n19. Понимание работы docker и kubernetes",
                    "Уровень Lead\nСофты:\n1. Желание учиться которое подтверждается делом.(Что изучено за последний год? Как это применяется?).\n2. Проактивная работа с заказчиком.(Инициатива по вопросам/запросу ОС должна поступать от специалиста).\n3. Умение принимать ОС.\n4. Умениедоносить своимысли до коллег.\n5. Умение объяснить заказчику возможные варианты реализации.",
                    "6. Многозадачность\n7. Умение выявить у себя недостаток знаний в определенном домене и закрыть его при необходимости.\n8. Понимание как работа влияет на проект в целом: что нужно сделать в первом приоритете, что можно поставить на паузу, чего можно не делать вообще.\n9. Умение сглаживать напряжение внутри команды, умение объяснить команде, что могут быть задачи интересные, но не полезные для проекта",
                    "10. Наставничество над коллегами из своей компетенции с понятным результатом - приобретением ими желаемых скиллов.\n11. Умение давать (ученикам) нетравматичную ОС.\n12. Умение проведения встреч one-2-one.\nХарды: Харды Senior и Lead не отличаются"]}

# Токен Telegram-бота
bot = telebot.TeleBot(secret_key)
# Словарь для хранения данных пользователя
user_data = {}

# Функция для дообогащения промпта

#conn = sqlite3.connect('DATABASE_URL')
#cursor = conn.cursor()
#cursor.execute('''
#DROP TABLE Reminder
#''')
#conn.commit()
#conn.close()
#print("2\n")
# Создание таблицы, если она не существует

def init_db():
    # Подключаемся к базе данных (или создаем ее, если она не существует)
    conn = sqlite3.connect('DATABASE_URL')
    cursor = conn.cursor()

    try:
        # Создаем таблицу Users
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            role TEXT DEFAULT NULL
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
    except Exception as e:
        # В случае ошибки откатываем изменения
        conn.rollback()
        print(f"Ошибка при создании таблиц: {e}")
    finally:
        # Закрываем соединение с базой данных
        conn.close()

# Вызов функции для инициализации базы данных
init_db()

def save_message_in_db(chat_id, role, message):
    try:
        conn = sqlite3.connect('DATABASE_URL')
        cursor = conn.cursor()
        time = datetime.now() 
        cursor.execute('''
        INSERT INTO Message_history (user_id, role, message, time)
        VALUES (?, ?, ?, ?)
        ''', (chat_id, role, message, time))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        # Обработка ошибок базы данных
        print( f"Ошибка при сохранении сообщения в историю: {e}")

def take_history_dialog_from_db(chat_id):
    conn = sqlite3.connect('DATABASE_URL') 
    cursor = conn.cursor()

    # Запрос для получения истории сообщений в одну строку по user_id
    user_id = chat_id 
    query = '''
    SELECT 
        GROUP_CONCAT(role || ': ' || message || ' (' || time || ')', '; ') AS full_history
    FROM Message_history
    WHERE user_id = ?
    GROUP BY user_id;
    
    '''

    # Выполнение запроса
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()

    conn.close()
    return result

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    conn = sqlite3.connect('DATABASE_URL')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()


    if existing_user:
        print(f"Пользователь с ID {user_id} уже существует в базе данных.")
    else:
        # Вставляем user_id в таблицу
        cursor.execute("INSERT INTO Users (user_id) VALUES(?)", (user_id,))
        conn.commit()
        print(f"Пользователь с ID {user_id} успешно добавлен в базу данных.")
    # Выводим всех пользователей для проверки
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    print("Текущие пользователи в базе данных:")
    for user in users:
        print(user[0], user[1])  # user[0], так как fetchall() возвращает кортежи
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Начать", callback_data="start")
    markup.add(button)
    bot.send_message(message.chat.id, "Добро пожаловать! Нажмите кнопку ниже, чтобы начать:", reply_markup=markup)
    conn.close()
    

# Обработчик нажатия кнопки Start
@bot.callback_query_handler(func=lambda call: call.data == "start")
def handle_start(message_or_call):
    # Определяем chat_id в зависимости от типа объекта (message или call)
    if isinstance(message_or_call, telebot.types.Message):
        chat_id = message_or_call.chat.id
    else:
        chat_id = message_or_call.message.chat.id
    
    # Отменяем текущий обработчик следующего шага
    bot.clear_step_handler_by_chat_id(chat_id)  # Передаем chat_id (число), а не объект
    
    # Создаем клавиатуру с кнопками
    markup = types.InlineKeyboardMarkup(row_width=1)
    roles = [
        types.InlineKeyboardButton(text="Задать вопрос по роли", callback_data="menu_qr"),
        types.InlineKeyboardButton(text="Выбрать роль", callback_data="menu_r"),
        types.InlineKeyboardButton(text="Поставьте напоминание", callback_data="menu_rem")
    ]
    markup.add(*roles)
    
    # Отправляем новое сообщение с главным меню
    bot.send_message(chat_id, "Главное меню:", reply_markup=markup)

# Обработчик нажатия кнопки "Поставьте напоминание"
@bot.callback_query_handler(func=lambda call: call.data == "menu_rem")
def handle_reminder(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    back_button = types.InlineKeyboardButton(text="В начало", callback_data="start")
    markup.add(back_button)
    msg = bot.send_message(call.message.chat.id, "Введите время напоминания в формате HH:MM и текст напоминания через пробел.\nНапример: 14:30 Рассказать про uc", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda message: process_reminder_input(message, call))

# Обработчик ввода времени и текста напоминания
def process_reminder_input(message, call):
    try:
        # Разделяем ввод на время и текст
        time_str, reminder_text = message.text.split(maxsplit=1)
        
        # Проверяем формат времени
        datetime.strptime(time_str, "%H:%M")  # Если время не в формате HH:MM, выбросится исключение
        
        # Сохраняем напоминание в базу данных
        conn = sqlite3.connect('DATABASE_URL')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Reminder (user_id, reminder_text, reminder_time) VALUES (?, ?, ?)",
            (message.chat.id, reminder_text, time_str)  # По умолчанию напоминание одноразовое
        )
        conn.commit()
        conn.close()
        
        # Отправляем сообщение об успешном создании напоминания
        bot.send_message(message.chat.id, f"Напоминание установлено на {time_str}: {reminder_text}")
        handle_start(call)
        
    except ValueError:
        # Обработка ошибки неверного формата времени
        bot.send_message(message.chat.id, "Неверный формат времени. Используйте HH:MM.")
        handle_start(call)
    except sqlite3.Error as e:
        # Обработка ошибок базы данных
        bot.send_message(message.chat.id, f"Ошибка при сохранении напоминания: {e}")

# Асинхронная функция для проверки и отправки напоминаний
async def check():
    while True:
        conn = sqlite3.connect('DATABASE_URL')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Получаем текущее время в формате HH:MM
        current_time = datetime.now().strftime("%H:%M")
        time_for_send_messages = "10:00"
        
        # Выбираем все напоминания
        cursor.execute("SELECT * FROM Users;")
        reminders_results = cursor.fetchall()
        if(current_time == time_for_send_messages):
            for reminder in reminders_results:

                chat_id = reminder['user_id']
                wanted_simbols = [".", ":"]
                context_str = take_history_dialog_from_db(chat_id)
                question_id = 666
                role = 'Аналитик'
                specialization = 'Специалист'
                count_for_pro_activity = 101
                question = 'without'
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
                        bot.send_message(chat_id=chat_id, text = full_answer)
                    
        
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

# Обработчик нажатия кнопки Выбор роли
@bot.callback_query_handler(func=lambda call: call.data == "menu_qr")
def handle_role(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    roles = [
        types.InlineKeyboardButton(text="PO/PM", callback_data="role_PM"),
        types.InlineKeyboardButton(text="Лид компетенций", callback_data="role_lead"),
        types.InlineKeyboardButton(text="Специалист", callback_data="role_employee")
    ]
    markup.add(*roles)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите вашу роль:", reply_markup=markup)

def clear_dialog_context(chat_id):
    if chat_id in dialogue_context:
        dialogue_context[chat_id] = []
    if chat_id in count_questions_users:
        count_questions_users[chat_id] = 0

# Обработчик выбора роли
@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_r"))
def choose_menu(call):
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
@bot.callback_query_handler(func=lambda call: call.data.startswith( "specsql_"))
def handle_role_specialization(call):
    user_id = call.message.chat.id
    data = call.data
    conn = sqlite3.connect('DATABASE_URL')
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

    if selected_role in ["Лид компетенций", "Специалист"]:
        markup = types.InlineKeyboardMarkup(row_width=2)
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
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали роль: {selected_role}\nТеперь выберите вопрос:", reply_markup=markup)

# Обработчик выбора специализации
@bot.callback_query_handler(func=lambda call: call.data.startswith("spec_"))
def choose_specialization(call):
    chat_id = call.message.chat.id
    clear_dialog_context(chat_id)
    spec_mapping = {
        "spec_analyst": "Аналитик",
        "spec_tester": "Тестировщик",
        "spec_devops": "Девопс",
        "spec_developer": "Разработчик"
    }
    selected_spec = spec_mapping.get(call.data)
    if call.message.chat.id in user_data:
        user_data[call.message.chat.id]["specialization"] = selected_spec
    else:
        user_data[call.message.chat.id] = {"role": "Специалист", "specialization": selected_spec}

    markup = types.InlineKeyboardMarkup(row_width=1)

    if(selected_spec == "Аналитик" and user_data[call.message.chat.id]['role'] == "Специалист"):
        questions = [
            types.InlineKeyboardButton(text="Что я могу ожидать от своего PO/PM", callback_data="question_1"),
            types.InlineKeyboardButton(text="Что я могу ожидать от своего Лида", callback_data="question_2"),
            types.InlineKeyboardButton(text="Посмотреть матрицу компетенций", callback_data="question_3"),
            types.InlineKeyboardButton(text="Что еще ты умеешь?", callback_data="question_777"),
            types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom"),
            types.InlineKeyboardButton(text="Вернуться в начало", callback_data="start")
        ]
        markup.add(*questions)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали специализацию: {selected_spec}\nТеперь выберите вопрос:", reply_markup=markup)
    elif(selected_spec == "Аналитик" and user_data[call.message.chat.id]['role'] == "Лид компетенций"):
        questions = [
            types.InlineKeyboardButton(text="Что я могу ожидать от специалиста компетенции", callback_data="question_4"),
            types.InlineKeyboardButton(text="Что я могу ожидать от своего PO/PM специалиста", callback_data="question_5"),
            types.InlineKeyboardButton(text="Что ожидается от меня", callback_data="questions_group_1"),
            types.InlineKeyboardButton(text="Что еще ты умеешь", callback_data="questions_group_2"),
            types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom"),
            types.InlineKeyboardButton(text="Вернуться в начало", callback_data="start")
        ]
        markup.add(*questions)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали специализацию: {selected_spec}\nТеперь выберите вопрос:", reply_markup=markup)
    else:
        hadl_print_in_development_2(call.message)

# Обработчик предопределенных вопросов
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
            types.InlineKeyboardButton(text="Вернуться в начало", callback_data="start")
        ]
        markup.add(*questions)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали категорию: \nТеперь выберите вопрос:", reply_markup=markup)
    elif switcher == 1:
        questions = [
            types.InlineKeyboardButton(text="Построение структуры компетенции", callback_data="group_2_question_1"),
            types.InlineKeyboardButton(text="Создание ИПР", callback_data="group_2_question_2"),
            types.InlineKeyboardButton(text="Как провести онбординг", callback_data="group_2_question_3"),
            types.InlineKeyboardButton(text="Оптимизация процессов разработки", callback_data="group_2_question_4"),
            types.InlineKeyboardButton(text="Вернуться в начало", callback_data="start")
        ]
        markup.add(*questions)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали категорию: \nТеперь выберите вопрос:", reply_markup=markup)
    
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

    if (question_id not in cache_dict):
        asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))
    else:
        handling_cached_requests(question_id, call.message, question)


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

    if (question_id not in cache_dict):
        asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))
    else:
        handling_cached_requests(question_id, call.message, question)

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

    if (question_id not in cache_dict):
        asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))
    else:
        handling_cached_requests(question_id, call.message, question)



@bot.callback_query_handler(func=lambda call: call.data in ["question_1", "question_2", "question_3", "question_4", "question_5"])
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
    elif call.data == "question_3":
        question = "Посмотреть матрицу компетенций"
        question_id = 3
    elif call.data == "question_4":
        question = "Что я могу ожидать от специалиста компетенции"
        question_id = 4
    elif call.data == "question_5":
        question = "Что я могу ожидать от своего PO/PM специалиста"
        question_id = 5
    
    
    if (question_id not in cache_dict):
        asyncio.run(websocket_question_from_user(question, call.message, role, specialization, question_id))
    else:
        handling_cached_requests(question_id, call.message, question)

@bot.callback_query_handler(func=lambda call: call.data == "question_777")
def hadl_print_in_development(call):
    bot.send_message(call.message.chat.id, "В разработке")
    send_welcome(call.message)

def hadl_print_in_development_2(message):
    bot.send_message(message.chat.id, "В разработке")
    send_welcome(message)

# Обработчик пользовательского вопроса
@bot.callback_query_handler(func=lambda call: call.data == "question_custom")
def ask_custom_question(call):
    bot.send_message(call.message.chat.id, "Введите ваш вопрос:")
    bot.register_next_step_handler(call.message, process_custom_question)


def process_custom_question(message):   
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {"role": "Специалист", "specialization": "Аналитик"}

    role = user_data[message.chat.id]['role']
    specialization = user_data[message.chat.id]['specialization']

    question_id = 777
    question = message.text
    asyncio.run(websocket_question_from_user(question, message, role, specialization, question_id))

def handling_cached_requests(question_id, message, question):
    print("Кешированное сообщение")

    arr = cache_dict[question_id]
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
    button = [types.InlineKeyboardButton(text="Ввести уточняющее сообщение", callback_data="question_custom"),
                    types.InlineKeyboardButton(text="Вернуться в начало", callback_data="start")
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
                            message_2 = bot.send_message(chat_id=message_2.chat.id, text=full_answer)
                            answer_for_cache.append(full_answer)
                            answer_for_countinue_dialog += full_answer
                            full_answer = ""
                            last_send_time = time.time()
                        except telebot.apihelper.ApiTelegramException as e:
                            if e.error_code == 429:
                                retry_after = int(e.result.headers.get('Retry-After', 1))
                                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                                time.sleep(retry_after)
                                message_2 = bot.send_message(chat_id=message_2.chat.id, text=full_answer)
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
                cache_dict[question_id] = answer_for_cache
            
        dialogue_context[chat_id].append({"role": "assistant", "content": answer_for_countinue_dialog})
        save_message_in_db(chat_id, "assistant", answer_for_countinue_dialog)
        markup = types.InlineKeyboardMarkup()
        if(count_questions_users[chat_id] < 6):
            button = [types.InlineKeyboardButton(text="Ввести уточняющее сообщение", callback_data="question_custom"),
                    types.InlineKeyboardButton(text="Вернуться в начало", callback_data="start")
                ]
        else:
            button = [types.InlineKeyboardButton(text="Вернуться в начало", callback_data="start")]

        markup.add(*button)
        bot.send_message(chat_id=message_2.chat.id, text = "Пожалуйста, выберите дальнейшее действие", reply_markup=markup)


async def websocket_proactiv_bot(chat_id):
    wanted_simbols = [".", ":"]

    context_str = take_history_dialog_from_db(chat_id)
    question_id = 666
    role = 'Аналитик'
    specialization = 'Специалист'
    count_for_pro_activity = 101
    question = 'without'
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
            bot.send_message(chat_id=chat_id, text = full_answer)

current_timezone = time.tzname
print(f"Текущий часовой пояс: {current_timezone}")     
current_timenow = datetime.now(moscow_tz).strftime("%H:%M")
print(f"Текущий часовой пояс:{current_timenow}")
# Запуск планировщика в отдельном потоке
threading.Thread(target=run_async_task, daemon=True).start()
bot.polling(none_stop=False)


