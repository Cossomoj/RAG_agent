FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /app

# Создаём .ssh директорию и устанавливаем права
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Копируем SSH-ключи (если нужно клонировать по SSH)
COPY id_ed25519 /root/.ssh/id_rsa
COPY id_ed25519.pub /root/.ssh/id_rsa.pub

# Устанавливаем права доступа для SSH-ключей
RUN chmod 600 /root/.ssh/id_rsa /root/.ssh/id_rsa.pub

# Добавляем GitHub в known_hosts
RUN ssh-keyscan -H github.com >> /root/.ssh/known_hosts

# Клонируем обновленный репозиторий с ветки MVP_2
RUN git clone git@github.com:Cossomoj/RAG_agent.git /app && \
    cd /app && \
    git checkout MVP_2

# Создаём виртуальные окружения для каждого сервиса
RUN python3.12 -m venv /app/src/main_version/venv
RUN python3.12 -m venv /app/admin/venv  
RUN python3.12 -m venv /app/webapp/api/venv

# Обновляем pip в каждом venv и устанавливаем зависимости
RUN /app/src/main_version/venv/bin/pip install --upgrade pip && \
    /app/src/main_version/venv/bin/pip install --no-cache-dir -r /app/src/main_version/requirements.txt

RUN /app/admin/venv/bin/pip install --upgrade pip && \
    /app/admin/venv/bin/pip install --no-cache-dir -r /app/admin/requirements.txt

RUN /app/webapp/api/venv/bin/pip install --upgrade pip && \
    /app/webapp/api/venv/bin/pip install --no-cache-dir -r /app/webapp/api/requirements.txt

# Копируем config.yaml и .env внутрь контейнера
COPY config.yaml /app/config.yaml
COPY .env /app/.env

# Создаем необходимые директории
RUN mkdir -p /app/logs /app/backups /app/src/main_version/docs /app/src/main_version/txt_docs

# Устанавливаем права на исполнение для всех скриптов
RUN chmod +x /app/src/main_version/*.py /app/admin/*.py /app/webapp/api/*.py
RUN chmod +x /app/*.sh /app/scripts/*.sh

# Создаем конфигурацию supervisor с обновленными сервисами
RUN echo '[supervisord]\n\
nodaemon=true\n\
logfile=/var/log/supervisord.log\n\
logfile_maxbytes=50MB\n\
logfile_backups=10\n\
loglevel=info\n\
\n\
[program:rag_service]\n\
command=/app/src/main_version/venv/bin/python /app/src/main_version/rag_service_context7_optimized.py\n\
directory=/app/src/main_version\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/var/log/rag_service.log\n\
stderr_logfile=/var/log/rag_service_err.log\n\
priority=800\n\
\n\
[program:telegram_bot]\n\
command=/app/src/main_version/venv/bin/python /app/src/main_version/telegram_bot.py\n\
directory=/app/src/main_version\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/var/log/telegram_bot.log\n\
stderr_logfile=/var/log/telegram_bot_err.log\n\
startretries=5\n\
stopasgroup=true\n\
killasgroup=true\n\
priority=900\n\
depends_on=rag_service\n\
\n\
[program:webapp_api]\n\
command=/app/webapp/api/venv/bin/python /app/webapp/api/app.py\n\
directory=/app/webapp/api\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/var/log/webapp_api.log\n\
stderr_logfile=/var/log/webapp_api_err.log\n\
priority=850\n\
depends_on=rag_service\n\
\n\
[program:admin_app]\n\
command=/app/admin/venv/bin/python /app/admin/app.py\n\
directory=/app/admin\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/var/log/admin_app.log\n\
stderr_logfile=/var/log/admin_app_err.log\n\
priority=870\n\
depends_on=rag_service\n\
' > /etc/supervisor/conf.d/services.conf

# Создаем каталог для логов
RUN mkdir -p /var/log

# Устанавливаем переменные окружения
ENV PYTHONPATH="/app"
ENV CONFIG_PATH="/app/config.yaml"

# Health check для контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Запускаем supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/services.conf"] 