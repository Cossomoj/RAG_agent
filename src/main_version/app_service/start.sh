#!/bin/bash

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Создаем директории логов
mkdir -p /var/log/supervisor
log "Созданы директории для логов supervisor"

# Проверка и настройка файла .env
log "Настройка файла .env..."
if [ -f "/.env" ]; then
    log "/.env обнаружен в корне контейнера"
    cp /.env /app/.env
    log "/.env скопирован в /app/.env"
elif [ -f "/app/.env" ]; then
    log "/app/.env обнаружен"
else
    log "ПРЕДУПРЕЖДЕНИЕ: Файл .env не найден. Многие функции могут быть недоступны!"
    log "Создаем пустой шаблон .env файла..."
    # Создаем пустой шаблон без реальных значений
    cat > /app/.env << EOF
# Токены для сервисов (необходимо заполнить)
# GigaChat API токен
GIGACHAT_API_KEY=

# Telegram API токены
TELEGRAM_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_ACCESS=

# Идентификаторы чатов Telegram
TELEGRAM_CHAT_ID=
CHAT_ID=
FEEDBACK_CHAT_ID=

# Токены для бота обратной связи и уведомлений
FEEDBACK_BOT_TOKEN=
ALERT_BOT_TOKEN=
EOF
    log "Создан пустой шаблон /app/.env"
    log "ВНИМАНИЕ: Для работы сервиса необходимо заполнить файл .env вручную!"
fi

# Копирование .env в нужные места
if [ -f "/app/.env" ]; then
    cp /app/.env /app/src/main_version/.env
    log "Файл .env скопирован в /app/src/main_version/"
    cp /app/.env /app/admin/.env
    log "Файл .env скопирован в /app/admin/"
else
    log "ВНИМАНИЕ: Файл .env отсутствует, переменные окружения могут быть недоступны"
fi

# Вывод текущих переменных окружения для диагностики
log "Проверка доступных переменных окружения:"
if [ -n "${GIGACHAT_API_KEY}" ]; then
    log "GIGACHAT_API_KEY: доступен (значение скрыто)"
else
    log "GIGACHAT_API_KEY: НЕ НАЙДЕН"
fi

if [ -n "${TELEGRAM_API_KEY}" ]; then
    log "TELEGRAM_API_KEY: доступен (значение скрыто)"
else
    log "TELEGRAM_API_KEY: НЕ НАЙДЕН"
fi

if [ -n "${TELEGRAM_CHAT_ID}" ]; then
    log "TELEGRAM_CHAT_ID: ${TELEGRAM_CHAT_ID}"
else
    log "TELEGRAM_CHAT_ID: НЕ НАЙДЕН"
fi

if [ -z "${GIGACHAT_API_KEY}" ] || [ -z "${TELEGRAM_API_KEY}" ]; then
    log "ПРЕДУПРЕЖДЕНИЕ: Одна или несколько важных переменных окружения отсутствуют!"
fi

# Проверяем структуру директорий для RAG сервиса
log "Проверяем структуру директорий для RAG сервиса..."
if [ ! -d "/app/src" ]; then
    log "Создаем директорию /app/src"
    mkdir -p /app/src
fi

if [ ! -d "/app/src/main_version" ]; then
    log "Создаем директорию /app/src/main_version"
    mkdir -p "/app/src/main_version"
fi

# Создаем файлы __init__.py для корректной работы импорта модулей Python
log "Создаем файлы __init__.py для модулей Python..."
touch /app/src/__init__.py
touch /app/src/main_version/__init__.py

# Перемещаем файлы RAG сервиса в нужную структуру если они находятся не там где нужно
if [ -f "/app/telegram_bot.py" ] && [ ! -f "/app/src/main_version/telegram_bot.py" ]; then
    log "Перемещаем telegram_bot.py в правильное место"
    cp /app/telegram_bot.py /app/src/main_version/
fi

if [ -f "/app/websocket_server.py" ] && [ ! -f "/app/src/main_version/websocket_server.py" ]; then
    log "Перемещаем websocket_server.py в правильное место"
    cp /app/websocket_server.py /app/src/main_version/
fi

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

# Проверяем и корректируем права доступа
log "Настраиваем права доступа..."
chmod -R 755 /app
chmod 644 /app/src/__init__.py
chmod 644 /app/src/main_version/__init__.py
if [ -f "/app/src/main_version/telegram_bot.py" ]; then
    chmod 644 /app/src/main_version/telegram_bot.py
fi
if [ -f "/app/src/main_version/websocket_server.py" ]; then
    chmod 644 /app/src/main_version/websocket_server.py
fi
chmod 644 /app/requirements_rag.txt /app/requirements_admin.txt

# Вывод содержимого директорий для диагностики
log "Структура директорий:"
find /app -type d | sort
log "Файлы в главной директории:"
ls -la /app
log "Файлы в директории src/main_version:"
ls -la /app/src/main_version 2>/dev/null || echo "Директория не существует"
log "Файлы в директории admin:"
ls -la /app/admin

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