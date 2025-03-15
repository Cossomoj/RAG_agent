"""
Модуль мониторинга системных ресурсов с оповещением через Telegram.

Этот модуль предоставляет функционал для мониторинга различных системных параметров,
включая использование CPU, RAM, дискового пространства и сетевых соединений.
Результаты мониторинга отправляются через Telegram-бот.

Основные возможности:
    - Мониторинг загрузки CPU
    - Отслеживание использования RAM
    - Проверка свободного места на диске
    - Подсчет активных сетевых соединений
    - Визуализация данных через графики
    - Отправка уведомлений через Telegram

Требования:
    - Установленный Python 3.6+
    - Доступ к системным ресурсам
    - Токен Telegram бота в переменной окружения ALERT_BOT_TOKEN
    - Установленные зависимости: psutil, telebot, matplotlib

Пример использования:
    $ python monitor.py
"""

import os
import psutil
import telebot
import logging
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import matplotlib.pyplot as plt

# Загружаем токен бота из переменных окружения
ALERT_BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN")
bot = telebot.TeleBot(ALERT_BOT_TOKEN)

# Настройка логирования
logging.basicConfig(
    filename="monitor.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Функции мониторинга
def get_uptime():
    """
    Получает время работы системы.

    Returns:
        str: Форматированная строка со временем работы системы в часах.
            Пример: '🕒 Время работы системы: 23.50 часа'

    Raises:
        Exception: При ошибке чтения файла /proc/uptime
    """
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_hours = uptime_seconds / 3600
            return f"🕒 Время работы системы: {uptime_hours:.2f} часов"
    except Exception as e:
        logging.error(f"Ошибка получения uptime: {e}")
        return f"Ошибка получения uptime: {e}"


def get_cpu_load():
    """
    Измеряет текущую загрузку процессора.

    Returns:
        str: Форматированная строка с процентом загрузки CPU.
            Пример: '🔥 Загрузка CPU: 45.2%'

    Raises:
        Exception: При ошибке получения данных через psutil
    """
    try:
        cpu_load = psutil.cpu_percent(interval=1)
        return f"🔥 Загрузка CPU: {cpu_load}%"
    except Exception as e:
        logging.error(f"Ошибка получения загрузки CPU: {e}")
        return f"Ошибка получения загрузки CPU: {e}"


def get_ram_usage():
    """
    Получает информацию об использовании оперативной памяти.

    Returns:
        str: Форматированная строка с информацией об использовании RAM.
            Пример: '💾 Использование RAM: 4.20 ГБ / 16.00 ГБ (26.25%)'

    Raises:
        Exception: При ошибке получения данных через psutil
    """
    try:
        mem = psutil.virtual_memory()
        return f"💾 Использование RAM: {mem.used / (1024**3):.2f} ГБ / {mem.total / (1024**3):.2f} ГБ ({mem.percent}%)"
    except Exception as e:
        logging.error(f"Ошибка получения RAM: {e}")
        return f"Ошибка получения RAM: {e}"


def get_disk_usage():
    """
    Получает информацию об использовании дискового пространства.

    Returns:
        str: Форматированная строка с информацией о свободном месте на диске.
            Пример: '📀 Доступно на диске: 100.50 ГБ из 500.00 ГБ (79.90% занято)'

    Raises:
        Exception: При ошибке получения данных через psutil
    """
    try:
        disk = psutil.disk_usage("/")
        return f"📀 Доступно на диске: {disk.free / (1024**3):.2f} ГБ из {disk.total / (1024**3):.2f} ГБ ({disk.percent}% занято)"
    except Exception as e:
        logging.error(f"Ошибка получения дискового пространства: {e}")
        return f"Ошибка получения дискового пространства: {e}"


def get_active_connections():
    """
    Подсчитывает количество активных сетевых соединений.

    Returns:
        str: Форматированная строка с количеством активных соединений.
            Пример: '🌐 Активные сетевые соединения: 42'

    Raises:
        Exception: При ошибке получения данных через psutil
    """
    try:
        connections = len(psutil.net_connections(kind="inet"))
        return f"🌐 Активные сетевые соединения: {connections}"
    except Exception as e:
        logging.error(f"Ошибка получения активных соединений: {e}")
        return f"Ошибка получения активных соединений: {e}"


def generate_graph():
    """
    Генерирует график загрузки CPU и RAM.

    Создает столбчатую диаграмму, показывающую текущую загрузку CPU и RAM
    в процентах. График сохраняется в файл 'system_graph.png'.

    Returns:
        str | None: Путь к сохраненному графику или None в случае ошибки.

    Raises:
        Exception: При ошибке генерации или сохранения графика
    """
    try:
        cpu_load = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent

        labels = ["CPU Load", "RAM Usage"]
        values = [cpu_load, ram_usage]

        plt.figure(figsize=(5, 3))
        plt.bar(labels, values, color=["red", "blue"])
        plt.ylabel("Процент (%)")
        plt.title("Загрузка CPU и RAM")
        plt.ylim(0, 100)

        # Сохраняем график
        graph_path = "system_graph.png"
        plt.savefig(graph_path)
        plt.close()
        return graph_path
    except Exception as e:
        logging.error(f"Ошибка генерации графика: {e}")
        return None


@bot.message_handler(commands=["start"])
def send_welcome(message):
    """
    Обработчик команды /start для Telegram бота.

    Отправляет приветственное сообщение и добавляет кнопку для
    быстрого доступа к команде /status.

    Args:
        message (telebot.types.Message): Объект сообщения Telegram
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    status_button = KeyboardButton("/status")
    markup.add(status_button)
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для мониторинга системы. Нажмите кнопку ниже, чтобы узнать текущий статус.",
        reply_markup=markup,
    )


@bot.message_handler(commands=["status"])
def send_status(message):
    """
    Обработчик команды /status для Telegram бота.

    Собирает информацию о состоянии системы и отправляет её пользователю
    вместе с графиком загрузки CPU и RAM.

    Args:
        message (telebot.types.Message): Объект сообщения Telegram
    """
    report = "\n".join(
        [
            get_uptime(),
            get_cpu_load(),
            get_ram_usage(),
            get_disk_usage(),
            get_active_connections(),
        ]
    )

    bot.send_message(
        message.chat.id, f"📊 *Системный статус:*\n\n{report}", parse_mode="Markdown"
    )

    # Генерация и отправка графика
    graph_path = generate_graph()
    if graph_path:
        with open(graph_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo)


# Запуск бота
if __name__ == "__main__":
    bot.infinity_polling()
