import os
import telebot
import logging
import requests
import schedule
import time
import threading
from dotenv import load_dotenv
from threading import Thread
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Загрузка переменных окружения
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(env_path)
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_BOT_ACCESS = os.getenv("TELEGRAM_BOT_ACCESS")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_API_KEY or not TELEGRAM_BOT_ACCESS or not CHAT_ID:
    raise ValueError("Переменные окружения TELEGRAM_API_KEY, TELEGRAM_BOT_ACCESS или CHAT_ID не найдены!")

bot_access = telebot.TeleBot(TELEGRAM_BOT_ACCESS)

# Настройка логирования
logging.basicConfig(
    filename="bot_test.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def check_bot():
    """Проверка доступности Telegram-бота и отправка результата в другой бот"""
    try:
        bot_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/getMe").json()
        if bot_info.get("ok"):
            message = (f"✅ Бот доступен!\n"
                       f"Имя: {bot_info['result']['first_name']}\n"
                       f"Юзернейм: @{bot_info['result']['username']}")
            logging.info(message)
            bot_access.send_message(CHAT_ID, message)
        else:
            raise Exception("Ошибка получения данных бота")

    except Exception as e:
        error_message = f"❌ Ошибка доступа к боту: {e}"
        logging.error(error_message)
        bot_access.send_message(CHAT_ID, error_message)

def schedule_check(stop_event):
    """Запуск проверки бота каждые 5 минут"""
    schedule.every(5).minutes.do(check_bot)
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def send_welcome_message(chat_id):
    """Отправка приветственного сообщения с кнопкой"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    check_button = KeyboardButton("CHECK_BOT ✅")
    markup.add(check_button)
    bot_access.send_message(chat_id, "Используйте кнопку ниже, чтобы проверить бота:", reply_markup=markup)

@bot_access.message_handler(func=lambda message: message.text == "CHECK_BOT ✅")
def handle_check_bot(message):
    """Обработчик нажатия кнопки для проверки бота"""
    check_bot()
    bot_access.send_message(message.chat.id, "Проверка запущена!")

def stop_bot(stop_event):
    """Функция для остановки бота по команде из терминала"""
    input("Введите 'stop' для остановки бота:\n")
    stop_event.set()

if __name__ == "__main__":
    # Создаем событие для остановки бота
    stop_event = threading.Event()

    # Отправка приветственного сообщения при запуске бота
    send_welcome_message(CHAT_ID)

    # Запуск проверки бота в отдельном потоке
    check_thread = Thread(target=schedule_check, args=(stop_event,))
    check_thread.start()

    # Запуск потока для ожидания команды остановки
    stop_thread = Thread(target=stop_bot, args=(stop_event,))
    stop_thread.start()

    # Запуск бота для обработки команд
    bot_access.polling(none_stop=True)

    # Ожидание завершения потоков
    check_thread.join()
    stop_thread.join()
