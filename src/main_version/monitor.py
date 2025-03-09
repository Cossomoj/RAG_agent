import os
import psutil
import telebot
import logging
import matplotlib.pyplot as plt

# Загружаем токен бота из переменных окружения
ALERT_BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN")
bot = telebot.TeleBot(ALERT_BOT_TOKEN)


# Настройка логирования
logging.basicConfig(filename="monitor.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# Функции мониторинга
def get_uptime():
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_hours = uptime_seconds / 3600
            return f"🕒 Время работы системы: {uptime_hours:.2f} часов"
    except Exception as e:
        logging.error(f"Ошибка получения uptime: {e}")
        return f"Ошибка получения uptime: {e}"

def get_cpu_load():
    try:
        cpu_load = psutil.cpu_percent(interval=1)
        return f"🔥 Загрузка CPU: {cpu_load}%"
    except Exception as e:
        logging.error(f"Ошибка получения загрузки CPU: {e}")
        return f"Ошибка получения загрузки CPU: {e}"

def get_ram_usage():
    try:
        mem = psutil.virtual_memory()
        return f"💾 Использование RAM: {mem.used / (1024**3):.2f} ГБ / {mem.total / (1024**3):.2f} ГБ ({mem.percent}%)"
    except Exception as e:
        logging.error(f"Ошибка получения RAM: {e}")
        return f"Ошибка получения RAM: {e}"

def get_disk_usage():
    try:
        disk = psutil.disk_usage("/")
        return f"📀 Доступно на диске: {disk.free / (1024**3):.2f} ГБ из {disk.total / (1024**3):.2f} ГБ ({disk.percent}% занято)"
    except Exception as e:
        logging.error(f"Ошибка получения дискового пространства: {e}")
        return f"Ошибка получения дискового пространства: {e}"

def get_active_connections():
    try:
        connections = len(psutil.net_connections(kind="inet"))
        return f"🌐 Активные сетевые соединения: {connections}"
    except Exception as e:
        logging.error(f"Ошибка получения активных соединений: {e}")
        return f"Ошибка получения активных соединений: {e}"

def generate_graph():
    """Генерирует график загрузки CPU и RAM"""
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

# Обработчик команды /status
@bot.message_handler(commands=['status'])
def send_status(message):
    """Отправляет отчет о состоянии системы с графиком"""
    report = "\n".join([
        get_uptime(),
        get_cpu_load(),
        get_ram_usage(),
        get_disk_usage(),
        get_active_connections()
    ])

    bot.send_message(message.chat.id, f"📊 *Системный статус:*\n\n{report}", parse_mode="Markdown")

    # Генерация и отправка графика
    graph_path = generate_graph()
    if graph_path:
        with open(graph_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo)

# Запуск бота
if __name__ == "__main__":
    bot.infinity_polling() 