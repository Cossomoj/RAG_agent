FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание необходимых директорий
RUN mkdir -p /app/src/main_version

# Установка переменных окружения
ENV PYTHONPATH=/app

# Запуск приложения
CMD ["sh", "-c", "uvicorn app.src.main_version.telegram_bot:app --reload --host 0.0.0.0 --port 8001 & uvicorn app.src.main_version.admin_panel:app --reload --host 0.0.0.0 --port 8088"]