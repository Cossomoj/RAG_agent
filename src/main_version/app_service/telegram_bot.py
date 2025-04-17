import os
import logging
from fastapi import FastAPI, Request, Response
from telebot import TeleBot
from dotenv import load_dotenv
import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("telegram_bot")

# Загружаем переменные окружения из .env файла
load_dotenv()
logger.info("Загрузка переменных окружения из .env файла...")

# Получаем переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY")

logger.info(f"TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN[:10]}... (обрезано для безопасности)")
logger.info(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")
logger.info(f"GIGACHAT_API_KEY доступен: {bool(GIGACHAT_API_KEY)}")

# Проверка наличия обязательных переменных
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден. Проверьте .env файл или переменные окружения.")
    TELEGRAM_BOT_TOKEN = "default_token"  # Заглушка для запуска FastAPI

# Инициализация Telegram бота
bot = None
try:
    bot = TeleBot(TELEGRAM_BOT_TOKEN)
    logger.info("Telegram бот инициализирован успешно")
except Exception as e:
    logger.error(f"Ошибка при инициализации Telegram бота: {e}")

# Инициализация FastAPI приложения
app = FastAPI(title="RAG Service API")

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    logger.info("Получен запрос к корневому эндпоинту")
    return {"message": "RAG Service API работает", "status": "online"}

@app.get("/health")
async def health():
    """Проверка состояния сервиса"""
    bot_status = "ready" if bot else "not initialized"
    logger.info(f"Проверка состояния: бот {bot_status}")
    return {
        "status": "ok", 
        "telegram_bot": bot_status,
        "environment_variables": {
            "TELEGRAM_BOT_TOKEN": bool(TELEGRAM_BOT_TOKEN),
            "TELEGRAM_CHAT_ID": bool(TELEGRAM_CHAT_ID),
            "GIGACHAT_API_KEY": bool(GIGACHAT_API_KEY)
        }
    }

@app.get("/send-test")
async def send_test():
    """Отправка тестового сообщения в Telegram"""
    if not bot or not TELEGRAM_CHAT_ID:
        logger.error("Невозможно отправить тестовое сообщение: бот не инициализирован или отсутствует CHAT_ID")
        return {"status": "error", "message": "Бот не инициализирован или отсутствует CHAT_ID"}
    
    try:
        bot.send_message(TELEGRAM_CHAT_ID, "Тестовое сообщение от RAG сервиса")
        logger.info(f"Тестовое сообщение отправлено в чат {TELEGRAM_CHAT_ID}")
        return {"status": "success", "message": "Тестовое сообщение отправлено"}
    except Exception as e:
        logger.error(f"Ошибка при отправке тестового сообщения: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Запуск сервера FastAPI
    logger.info("Запуск FastAPI сервера...")
    uvicorn.run("telegram_bot:app", host="0.0.0.0", port=8001) 