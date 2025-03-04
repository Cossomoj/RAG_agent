import telebot
from dotenv import load_dotenv
from telebot import types
import asyncio
import websockets
import requests
import json
import time
import os
load_dotenv()

WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"

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

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Начать", callback_data="start")
    markup.add(button)
    bot.send_message(message.chat.id, "Добро пожаловать! Нажмите кнопку ниже, чтобы начать:", reply_markup=markup)

# Обработчик нажатия кнопки Start
@bot.callback_query_handler(func=lambda call: call.data == "start")
def handle_start(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    roles = [
        types.InlineKeyboardButton(text="PO/PM", callback_data="role_PM"),
        types.InlineKeyboardButton(text="Лид компетенций", callback_data="role_lead"),
        types.InlineKeyboardButton(text="Специалист", callback_data="role_employee")
    ]
    markup.add(*roles)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите вашу роль:", reply_markup=markup)

# Обработчик выбора роли
@bot.callback_query_handler(func=lambda call: call.data.startswith("role_"))
def choose_role(call):
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
        asyncio.run(test_websocket(question, call.message, role, specialization, question_id))
    else:
        handling_cached_requests(question_id, call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith("group_2"))
def handle_predefined_question_group_2(call):
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
        asyncio.run(test_websocket(question, call.message, role, specialization, question_id))
    else:
        handling_cached_requests(question_id, call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("po_question"))
def handle_predefined_question_group_2(call):
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
        asyncio.run(test_websocket(question, call.message, role, specialization, question_id))
    else:
        handling_cached_requests(question_id, call.message)



@bot.callback_query_handler(func=lambda call: call.data in ["question_1", "question_2", "question_3", "question_4", "question_5"])
def handle_predefined_question(call):
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
        asyncio.run(test_websocket(question, call.message, role, specialization, question_id))
    else:
        handling_cached_requests(question_id, call.message)

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
    asyncio.run(test_websocket(question, message, role, specialization, question_id))

def handling_cached_requests(question_id, message):
    print("Кешированное сообщение")

    arr = cache_dict[question_id]

    # Отправляем каждую часть с задержкой
    for i in arr:
        bot.send_message(chat_id=message.chat.id, text=i)
        time.sleep(1)

    send_welcome(message)

async def test_websocket(question, message, role, specialization, question_id):
    print(question)
    wanted_simbols = [".", ":"]

    async with websockets.connect(WEBSOCKET_URL) as websocket:
        await websocket.send(question) # Отправляем вопрос
        await websocket.send(role)
        await websocket.send(specialization)
        await websocket.send(str(question_id))

        try:
            message_2 = bot.send_message(message.chat.id, "Ожидайте ответа...")
            full_answer = ""
            last_send_time = time.time()
            answer_for_cache = []
            while True:
                answer_part = await websocket.recv()  # Получаем ответ частями
                if answer_part:
                    for char in answer_part:
                        if (char in wanted_simbols):
                            answer_part += "\n"

                    full_answer += answer_part
                    if time.time() - last_send_time >= 1:
                        try:
                            bot.send_message(chat_id=message_2.chat.id, text=full_answer)
                            answer_for_cache.append(full_answer)
                            full_answer = ""
                            last_send_time = time.time()
                        except telebot.apihelper.ApiTelegramException as e:
                            if e.error_code == 429:
                                retry_after = int(e.result.headers.get('Retry-After', 1))
                                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                                time.sleep(retry_after)
                                bot.send_message(chat_id=message_2.chat.id, text=full_answer)
                                answer_for_cache.append(full_answer)
                                last_send_time = time.time()
                                full_answer = ""
                else:
                    print("Получено пустое сообщение от WebSocket.")
            
        except websockets.exceptions.ConnectionClosed:
            if (full_answer != ""):
                bot.send_message(chat_id=message_2.chat.id, text=full_answer)
                answer_for_cache.append(full_answer)
            print("")
            if(question_id != 777):
                cache_dict[question_id] = answer_for_cache
            
        
        send_welcome(message_2)

        
while True:
    try:
        bot.polling(none_stop=True)

    except Exception as e:
        print(e)  # или просто print(e) если у вас логгера нет,
        time.sleep(15)