FROM python:3.9-slim

WORKDIR /app

# Создаем и активируем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем файлы приложения
COPY . .

# Устанавливаем зависимости в виртуальное окружение
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем сервис
CMD ["python", "-m", "uvicorn", "app.src.main_version.telegram_bot:app", "--host", "0.0.0.0", "--port", "8001"]