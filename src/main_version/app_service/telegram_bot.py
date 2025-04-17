import os
import logging
from fastapi import FastAPI
import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("telegram_bot")

# Загрузка переменных окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Переменные окружения загружены из .env файла")
except ImportError:
    logger.warning("python-dotenv не установлен. Используем переменные окружения из системы.")
except Exception as e:
    logger.error(f"Ошибка при загрузке .env файла: {e}")

# Получаем переменные окружения с проверкой
def get_env_var(name, default=None):
    value = os.environ.get(name, default)
    if value:
        logger.info(f"Переменная {name} найдена")
    else:
        logger.warning(f"Переменная {name} не найдена")
    return value

# Токены API
TELEGRAM_BOT_TOKEN = get_env_var("TELEGRAM_BOT_TOKEN") or get_env_var("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = get_env_var("TELEGRAM_CHAT_ID") or get_env_var("CHAT_ID")
GIGACHAT_API_KEY = get_env_var("GIGACHAT_API_KEY")

# Инициализация Telegram бота (если возможно)
bot = None
try:
    from telebot import TeleBot
    if TELEGRAM_BOT_TOKEN:
        bot = TeleBot(TELEGRAM_BOT_TOKEN)
        logger.info("Telegram бот инициализирован успешно")
    else:
        logger.error("Не удалось инициализировать Telegram бот: токен не найден")
except ImportError:
    logger.warning("Пакет telebot не установлен. Функции Telegram бота недоступны.")
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
    logger.info("Получен запрос к эндпоинту health")
    env_vars = {
        "TELEGRAM_BOT_TOKEN": bool(TELEGRAM_BOT_TOKEN),
        "TELEGRAM_CHAT_ID": bool(TELEGRAM_CHAT_ID),
        "GIGACHAT_API_KEY": bool(GIGACHAT_API_KEY)
    }
    
    # Проверка библиотек
    libraries = {}
    for lib_name in ["telebot", "fastapi", "uvicorn", "dotenv"]:
        try:
            __import__(lib_name)
            libraries[lib_name] = "installed"
        except ImportError:
            libraries[lib_name] = "not installed"
    
    return {
        "status": "ok", 
        "telegram_bot": "ready" if bot else "not initialized",
        "environment_variables": env_vars,
        "libraries": libraries,
        "python_path": os.environ.get("PYTHONPATH", "not set")
    }

@app.get("/send-test")
async def send_test():
    """Отправка тестового сообщения в Telegram"""
    logger.info("Получен запрос к эндпоинту send-test")
    
    if not bot:
        logger.error("Telegram бот не инициализирован")
        return {"status": "error", "message": "Telegram бот не инициализирован"}
    
    if not TELEGRAM_CHAT_ID:
        logger.error("Идентификатор чата не найден")
        return {"status": "error", "message": "Идентификатор чата не найден"}
    
    try:
        bot.send_message(TELEGRAM_CHAT_ID, "Тестовое сообщение от RAG сервиса")
        logger.info(f"Тестовое сообщение отправлено в чат {TELEGRAM_CHAT_ID}")
        return {"status": "success", "message": "Тестовое сообщение отправлено"}
    except Exception as e:
        logger.error(f"Ошибка при отправке тестового сообщения: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/debug")
async def debug():
    """Расширенная отладочная информация"""
    logger.info("Получен запрос к эндпоинту debug")
    
    # Окружение
    env_vars = {}
    for key, value in os.environ.items():
        if key.lower().startswith(("telegram", "gigachat", "chat_id", "api_key", "token", "python")):
            env_vars[key] = "***SECRET***" if "key" in key.lower() or "token" in key.lower() else value
    
    # Директории
    dirs = {}
    for dir_path in ["/app", "/app/src", "/app/src/main_version", "/app/admin"]:
        if os.path.exists(dir_path):
            try:
                dirs[dir_path] = os.listdir(dir_path)
            except Exception as e:
                dirs[dir_path] = f"Error: {str(e)}"
        else:
            dirs[dir_path] = "не существует"
    
    return {
        "status": "ok",
        "environment": env_vars,
        "directories": dirs,
        "current_directory": os.getcwd(),
        "python_version": os.popen("python --version").read().strip(),
        "system_info": os.popen("uname -a").read().strip()
    }

if __name__ == "__main__":
    logger.info("Запуск FastAPI сервера...")
    uvicorn.run("telegram_bot:app", host="0.0.0.0", port=8001) 