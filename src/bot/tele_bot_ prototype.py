import telebot
from telebot import types
from gigachat import GigaChat

# Ваш API-токен GigaChat


def ask_gigachat(question):
    API_TOKEN = "YTU3OTBkMzktYzA4OS00MmM2LTllYWUtNWE5Nzg5OGQyOGU4OjRkNDRiODU1LTRjYTMtNGY3NC1hZmUwLTc3NjRjZGRjMWY5Mg=="
    giga = GigaChat(credentials=API_TOKEN, verify_ssl_certs=False)  # Инициализация с API-ключом
    response = giga.chat(question)  # Используем метод chat
    return response.choices[0].message.content


# Вставьте сюда ваш токен
bot = telebot.TeleBot("7765491915:AAHhTJUfHoM6QshSHjzormMTQr3AAw6UJCs")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Создаем inline-клавиатуру с большой синей кнопкой
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Start", callback_data="start")
    markup.add(button)
    
    # Отправляем сообщение с кнопкой
    bot.send_message(message.chat.id, "Добро пожаловать! Нажмите кнопку ниже, чтобы начать:", reply_markup=markup)

@bot.message_handler(commands=['menu'])
def handle_menu(message):
    bot.send_message(message.chat.id, "выберите роль")
    


@bot.callback_query_handler(func=lambda call: call.data == "start")
def handle_start(call):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Menu", callback_data="menu")
    markup.add(button)

    # Редактируем сообщение, чтобы убрать кнопку после нажатия
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Вы нажали Start!")
    # Дополнительные действия после нажатия кнопки
    bot.send_message(call.message.chat.id, "Теперь вы можете продолжить использовать бота.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "menu")
def handle_menu(call):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="SA", callback_data="sa")
    markup.add(button)


    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите роль", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "sa")
def handle_menu(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Введите ваш вопрос")

    bot.register_next_step_handler(call.message, process_question)


def process_question(message):
    question = message.text
    answer = ask_gigachat(question)
    bot.send_message(message.chat.id, answer)
    send_welcome(message)

# Запуск бота
bot.polling(none_stop=True)


