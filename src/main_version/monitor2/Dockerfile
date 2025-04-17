FROM python:3.9-slim

WORKDIR /app

# Копирование исходного кода
COPY monitor.py .
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Запуск приложения с задержкой для ожидания запуска основного сервиса
CMD ["sh", "-c", "sleep 30 && python monitor.py"]
