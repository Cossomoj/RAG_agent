FROM python:3.9-slim

WORKDIR /app

# Копируем файлы приложения
COPY . .

# Создаем и настраиваем виртуальное окружение для RAG сервиса
RUN python -m venv /opt/venv_rag
ENV PATH_RAG="/opt/venv_rag/bin"
RUN $PATH_RAG/pip install --no-cache-dir -r requirements_rag.txt

# Создаем и настраиваем виртуальное окружение для админ-панели
RUN python -m venv /opt/venv_admin
ENV PATH_ADMIN="/opt/venv_admin/bin"
RUN $PATH_ADMIN/pip install --no-cache-dir -r requirements_admin.txt

# Устанавливаем supervisor для управления процессами
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# Копируем конфигурацию supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Делаем скрипт запуска исполняемым
RUN chmod +x /app/start.sh

# Запускаем supervisor, который будет управлять обоими процессами
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 