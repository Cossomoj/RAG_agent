FROM python:3.9-slim

WORKDIR /app

# Копируем файлы приложения
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем админ-панель
CMD ["python", "app.py"] 