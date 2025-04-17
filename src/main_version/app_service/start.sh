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

# Создаем и активируем виртуальные окружения
log "Настраиваем виртуальные окружения..."

# Настраиваем RAG окружение
log "Настраиваем виртуальное окружение для RAG сервиса..."
python -m venv /opt/venv_rag
export PATH_RAG="/opt/venv_rag/bin"

# Устанавливаем базовые пакеты в правильном порядке
log "Устанавливаем зависимости для RAG сервиса..."
$PATH_RAG/pip install --no-cache-dir pip==23.1.2
$PATH_RAG/pip install --no-cache-dir setuptools==68.0.0 wheel==0.38.4

# Устанавливаем пакеты по одному для избежания конфликтов
log "Устанавливаем основные пакеты для RAG сервиса..."
$PATH_RAG/pip install --no-cache-dir telebot==0.0.5
$PATH_RAG/pip install --no-cache-dir python-dotenv==1.0.1
$PATH_RAG/pip install --no-cache-dir asyncio==3.4.3
$PATH_RAG/pip install --no-cache-dir websockets==15.0
$PATH_RAG/pip install --no-cache-dir fastapi==0.115.10
$PATH_RAG/pip install --no-cache-dir uvicorn==0.34.0
$PATH_RAG/pip install --no-cache-dir python-multipart==0.0.5
$PATH_RAG/pip install --no-cache-dir pytz==2025.1
$PATH_RAG/pip install --no-cache-dir schedule==1.2.2
$PATH_RAG/pip install --no-cache-dir faiss-cpu==1.10.0

# Устанавливаем более сложные пакеты
log "Устанавливаем ML пакеты для RAG сервиса..."
$PATH_RAG/pip install --no-cache-dir transformers==4.41.0
$PATH_RAG/pip install --no-cache-dir sentence-transformers==3.4.1
$PATH_RAG/pip install --no-cache-dir langchain-huggingface==0.1.2
$PATH_RAG/pip install --no-cache-dir langchain-community==0.3.18
$PATH_RAG/pip install --no-cache-dir langchain-gigachat==0.3.4

# Проверяем успешность установки пакетов
if [ $? -ne 0 ]; then
    log "Ошибка при установке пакетов для RAG сервиса"
    exit 1
fi

# Настраиваем Admin окружение
log "Настраиваем виртуальное окружение для админ-панели..."
python -m venv /opt/venv_admin
export PATH_ADMIN="/opt/venv_admin/bin"
$PATH_ADMIN/pip install --no-cache-dir -r /app/requirements_admin.txt

# Проверяем успешность установки пакетов
if [ $? -ne 0 ]; then
    log "Ошибка при установке пакетов для админ-панели"
    exit 1
fi

log "Запускаем supervisor..."
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf 