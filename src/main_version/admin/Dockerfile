FROM python:3.9-slim

WORKDIR /app

# Создаем и активируем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем файлы приложения
COPY . .

# Устанавливаем зависимости в виртуальное окружение
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем админ-панель
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"] 