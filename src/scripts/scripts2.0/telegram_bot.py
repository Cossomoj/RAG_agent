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
        "role_PM": "Бизнес-PO/PM",
        "role_lead": "Лид компетенций",
        "role_employee": "Специалист"
    }
    selected_role = role_mapping.get(call.data)
    user_data[call.message.chat.id] = {"role": selected_role, "specialization": None}

    markup = types.InlineKeyboardMarkup(row_width=2)
    specializations = [
        types.InlineKeyboardButton(text="Аналитик", callback_data="spec_analyst"),
        types.InlineKeyboardButton(text="Тестировщик", callback_data="spec_tester"),
        types.InlineKeyboardButton(text="Девопс", callback_data="spec_devops"),
        types.InlineKeyboardButton(text="Разработчик", callback_data="spec_developer")
    ]
    markup.add(*specializations)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали роль: {selected_role}\nТеперь выберите специализацию:", reply_markup=markup)

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
    user_data[call.message.chat.id]["specialization"] = selected_spec

    markup = types.InlineKeyboardMarkup(row_width=1)

    if(selected_spec == "Аналитик"):
        questions = [
            types.InlineKeyboardButton(text="Что я могу ожидать от своего PO/PM", callback_data="question_1"),
            types.InlineKeyboardButton(text="Что я могу ожидать от своего Лида", callback_data="question_2"),
            types.InlineKeyboardButton(text="Что ожидается от меня, как от Junior аналитика?", callback_data="question_3")
        ]
    else:
        questions = [
            types.InlineKeyboardButton(text="Что я могу ожидать от своего PO/PM", callback_data="question_777"),
            types.InlineKeyboardButton(text="Что я могу ожидать от своего Лида", callback_data="question_777"),
            types.InlineKeyboardButton(text="Что ожидается от меня, как от Junior аналитика?", callback_data="question_777")
        ]
    markup.add(*questions)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали специализацию: {selected_spec}\nТеперь выберите вопрос:", reply_markup=markup)

# Обработчик предопределенных вопросов
@bot.callback_query_handler(func=lambda call: call.data in ["question_1", "question_2", "question_3"])
def handle_predefined_question(call):
    role = ""
    specialization = ""
    if(user_data[call.message.chat.id]['role']):
        role = user_data[call.message.chat.id]['role']
    else:
        role = "Специалист"
    if(user_data[call.message.chat.id]['specialization']):
        specialization = user_data[call.message.chat.id]['specialization']
    else:
        specialization = "Аналитик"
    question_id = 777

    if call.data == "question_1":
        question = "Что я могу ожидать от своего PO/PM?"
        question_id = 1
    elif call.data == "question_2":
        question = "Что я могу ожидать от своего Лида?"
        question_id = 2
    elif call.data == "question_3":
        question = "Что ожидается от меня, как от Junior аналитика?"
        question_id = 3
    

    asyncio.run(test_websocket(question, call.message, role, specialization, question_id))

# Обработчик пользовательского вопроса
@bot.callback_query_handler(func=lambda call: call.data == "question_custom")
def ask_custom_question(call):
    bot.send_message(call.message.chat.id, "Введите ваш вопрос:")
    bot.register_next_step_handler(call.message, process_custom_question)

@bot.callback_query_handler(func=lambda call: call.data == "question_custom_add")
def ask_custom_question(call):
    bot.send_message(call.message.chat.id, "Введите ваш вопрос:")
    bot.register_next_step_handler(call.message, process_custom_question)


def process_custom_question(message):
    if(user_data[message.chat.id]['role']):
        role = user_data[message.chat.id]['role']
    else:
        role = "Специалист"
    if(user_data[message.chat.id]['specialization']):
        specialization = user_data[message.chat.id]['specialization']
    else:
        specialization = "Аналитик"
    question_id = 777
    question = message.text
    asyncio.run(test_websocket(question, message, role, specialization, 777))


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
                            full_answer = ""
                            last_send_time = time.time()
                        except telebot.apihelper.ApiTelegramException as e:
                            if e.error_code == 429:
                                retry_after = int(e.result.headers.get('Retry-After', 1))
                                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                                time.sleep(retry_after)
                                bot.send_message(chat_id=message_2.chat.id, text=full_answer)
                                last_send_time = time.time()
                                full_answer = ""

                        

                else:
                    print("Получено пустое сообщение от WebSocket.")
            
        except websockets.exceptions.ConnectionClosed:
            if (full_answer != ""):
                bot.send_message(chat_id=message_2.chat.id, text=full_answer)
            print("")
        
        send_welcome(message_2)

        
if __name__ == "__main__":
    bot.polling(none_stop=True)