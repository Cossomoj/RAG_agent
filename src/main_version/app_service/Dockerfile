FROM python:3.9-slim

WORKDIR /app

# Устанавливаем базовые инструменты и библиотеки
RUN apt-get update && apt-get install -y \
    supervisor \
    procps \
    net-tools \
    curl \
    vim \
    less \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы приложения
COPY . .

# Просто создаем виртуальные окружения, но не устанавливаем зависимости
# Их установка будет выполнена в start.sh
RUN python -m venv /opt/venv_rag
RUN python -m venv /opt/venv_admin

# Устанавливаем переменные окружения
ENV PATH_RAG="/opt/venv_rag/bin"
ENV PATH_ADMIN="/opt/venv_admin/bin"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8
ENV WEBSOCKET_PORT=8000
ENV PYTHONPATH=/app

# Создаем директорию для логов
RUN mkdir -p /var/log/supervisor
RUN mkdir -p /app/logs
RUN chmod -R 777 /var/log/supervisor /app/logs

# Копируем конфигурацию supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Делаем скрипт запуска исполняемым
RUN chmod +x /app/start.sh

# Запускаем скрипт запуска, который установит зависимости и запустит supervisor
CMD ["/app/start.sh"] 