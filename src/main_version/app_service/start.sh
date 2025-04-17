#!/bin/bash

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Создаем директории логов
mkdir -p /var/log/supervisor
log "Созданы директории для логов supervisor"

# Настройка директорий для данных
mkdir -p /app/sqlite_data_rag
if [ ! -f "/app/src/main_version/AI_agent.db" ]; then
    log "База данных не найдена, создаем новую..."
    touch /app/src/main_version/AI_agent.db
    chmod 644 /app/src/main_version/AI_agent.db
fi

# Проверяем структуру директорий
log "Проверяем структуру приложения..."

# Проверяем наличие файлов requirements
if [ ! -f "/app/requirements_rag.txt" ] || [ ! -f "/app/requirements_admin.txt" ]; then
    log "Ошибка: Отсутствуют файлы requirements_rag.txt или requirements_admin.txt"
    exit 1
fi

# Проверяем директорию admin
if [ ! -d "/app/admin" ]; then
    log "Ошибка: директория для админ-панели не найдена"
    mkdir -p /app/admin
    log "Создана директория /app/admin"
fi

# Проверяем наличие Flask приложения
if [ ! -f "/app/admin/app.py" ]; then
    log "Ошибка: файл app.py для админ-панели не найден"
    exit 1
fi

# Проверяем права доступа
chmod -R 755 /app
chmod 644 /app/requirements_rag.txt /app/requirements_admin.txt

# Активируем виртуальные окружения и проверяем установку пакетов
log "Проверяем установку пакетов в виртуальных окружениях..."

# Проверяем RAG окружение
if [ ! -f "/opt/venv_rag/bin/python" ]; then
    log "Ошибка: виртуальное окружение для RAG сервиса не настроено"
    python -m venv /opt/venv_rag
    /opt/venv_rag/bin/pip install --no-cache-dir -r /app/requirements_rag.txt
fi

# Проверяем Admin окружение
if [ ! -f "/opt/venv_admin/bin/python" ]; then
    log "Ошибка: виртуальное окружение для админ-панели не настроено"
    python -m venv /opt/venv_admin
    /opt/venv_admin/bin/pip install --no-cache-dir -r /app/requirements_admin.txt
fi

log "Запускаем supervisor..."
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf 