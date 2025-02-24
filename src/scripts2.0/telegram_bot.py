import telebot
from telebot import types
import asyncio
import websockets
import requests

WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"

# Токен Telegram-бота
bot = telebot.TeleBot("7765491915:AAHhTJUfHoM6QshSHjzormMTQr3AAw6UJCs")

# Словарь для хранения данных пользователя
user_data = {}

# Функция для дообогащения промпта
def enrich_prompt(role, specialization, question):
    base_prompt = f"Роль: {role}, Специализация: {specialization}. Вопрос: {question}.\n"

    # Добавление контекста в зависимости от роли
    if role == "Лид компетенций":
        base_prompt += (
            "Ты выступаешь как эксперт по управлению командой. "
            "Твоя задача — дать рекомендации по развитию сотрудников, определению ролей и ответам на вопросы, связанные с лидерством.\n"
        )
    elif role == "Бизнес-заказчик":
        base_prompt += (
            "Ты выступаешь как представитель клиента. "
            "Твоя задача — формулировать требования к продукту, оценивать предложения команды разработки и принимать решения.\n"
        )
    elif role == "Специалист":
        base_prompt += (
            "Ты выступаешь как член команды разработки. "
            "Твоя задача — выполнять технические задачи, задавать уточняющие вопросы и предоставлять профессиональные рекомендации.\n"
        )

    # Добавление контекста в зависимости от специализации
    if specialization == "Аналитик":
        base_prompt += (
            "Ты выступаешь как бизнес-аналитик и системный аналитик. "
            "Твоя задача — собирать требования, анализировать данные и формировать рекомендации для команды.\n"
        )
    elif specialization == "Тестировщик":
        base_prompt += (
            "Ты выступаешь как тестировщик. "
            "Твоя задача — создавать тест-кейсы, находить дефекты и обеспечивать качество продукта.\n"
        )
    elif specialization == "Девопс":
        base_prompt += (
            "Ты выступаешь как девопс-инженер. "
            "Твоя задача — автоматизировать процессы развертывания, мониторинга и управления инфраструктурой.\n"
        )
    elif specialization == "Разработчик":
        base_prompt += (
            "Ты выступаешь как программист. "
            "Твоя задача — писать код, решать технические задачи и консультировать команду.\n"
        )

    return base_prompt

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
        types.InlineKeyboardButton(text="Бизнес-заказчик", callback_data="role_business"),
        types.InlineKeyboardButton(text="Лид компетенций", callback_data="role_lead"),
        types.InlineKeyboardButton(text="Специалист", callback_data="role_employee")
    ]
    markup.add(*roles)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите вашу роль:", reply_markup=markup)

# Обработчик выбора роли
@bot.callback_query_handler(func=lambda call: call.data.startswith("role_"))
def choose_role(call):
    role_mapping = {
        "role_business": "Бизнес-заказчик",
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
    questions = [
        types.InlineKeyboardButton(text="Пример требований", callback_data="question_example"),
        types.InlineKeyboardButton(text="Мой лид компетенций", callback_data="question_lead"),
        types.InlineKeyboardButton(text="Ввести свой вопрос", callback_data="question_custom")
    ]
    markup.add(*questions)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали специализацию: {selected_spec}\nТеперь выберите вопрос:", reply_markup=markup)

# Обработчик предопределенных вопросов
@bot.callback_query_handler(func=lambda call: call.data in ["question_example", "question_lead"])
def handle_predefined_question(call):
    role = user_data[call.message.chat.id]['role']
    specialization = user_data[call.message.chat.id]['specialization']

    if call.data == "question_example":
        question = "Приведи пример функциональных требований."
    elif call.data == "question_lead":
        question = "Кто является моим лидом компетенций? С какими вопросами можно к нему обратиться?"

    enriched_prompt = enrich_prompt(role, specialization, question)
    asyncio.run(test_websocket(question, call.message))

# Обработчик пользовательского вопроса
@bot.callback_query_handler(func=lambda call: call.data == "question_custom")
def ask_custom_question(call):
    bot.send_message(call.message.chat.id, "Введите ваш вопрос:")
    bot.register_next_step_handler(call.message, process_custom_question)


def process_custom_question(message):
    role = user_data[message.chat.id]['role']
    specialization = user_data[message.chat.id]['specialization']
    question = message.text
    asyncio.run(test_websocket(question, message))


async def test_websocket(question, message):
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        await websocket.send(question)  # Отправляем вопрос
        try:
            while True:
                answer_part = await websocket.recv()  # Получаем ответ частями
                if answer_part:

                    bot.send_message(message.chat.id, answer_part)
                else:
                    print("Получено пустое сообщение от WebSocket.")
        except websockets.exceptions.ConnectionClosed:
            send_welcome(message)


#def process_custom_question(message):
#   role = user_data[message.chat.id]['role']
 #   specialization = user_data[message.chat.id]['specialization']
#    question = message.text

#    enriched_prompt = enrich_prompt(role, specialization, question)
#   answer = ask_gigachat(enriched_prompt)
#    bot.send_message(message.chat.id, answer)
#    send_welcome(message)

# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)