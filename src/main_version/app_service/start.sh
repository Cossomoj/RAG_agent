#!/bin/bash

# Выход при любой ошибке
set -e

# Настройка логирования
LOG_DIR="/var/log"
LOG_FILE="$LOG_DIR/start_script.log"
mkdir -p "$LOG_DIR"

log_message() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "Запуск скрипта установки..."

# Проверяем наличие .env файла и создаем базовую версию, если его нет
if [ ! -f /app/.env ]; then
    log_message "ВНИМАНИЕ: Файл .env не найден! Создаем базовый файл..."
    cat > /app/.env << EOL
TELEGRAM_BOT_TOKEN=ваш_токен_телеграм_бота
GIGACHAT_BASE_URL=https://gigachat.devices.sberbank.ru/api/v1
GIGACHAT_TOKEN=ваш_токен_gigachat
YANDEX_GPT_TOKEN=ваш_токен_yandex_gpt
EOL
    log_message "Создан базовый .env файл. Необходимо заполнить правильными значениями."
else
    log_message "Файл .env найден."
fi

# Создаем нужные директории
log_message "Создаем директории для логов..."
mkdir -p /var/log/supervisor

# Копируем .env файл в нужные места
log_message "Копируем .env файл в требуемые расположения..."
cp /app/.env /app/src/main_version/.env
cp /app/.env /app/admin/.env

# Выводим текущие переменные окружения для диагностики (без значений)
log_message "Текущие переменные окружения (только имена):"
env | cut -d= -f1 | sort | tee -a "$LOG_FILE"

# Проверяем директорию RAG сервиса
log_message "Проверяем директорию RAG сервиса..."
if [ ! -d /app/src/main_version ]; then
    log_message "ОШИБКА: Директория /app/src/main_version не существует!"
    exit 1
fi

# Проверяем наличие основных файлов
if [ ! -f /app/src/main_version/telegram_bot.py ]; then
    log_message "ОШИБКА: Файл telegram_bot.py не найден! Проверка содержимого директории:"
    ls -la /app/src/main_version/ | tee -a "$LOG_FILE"
    exit 1
fi

if [ ! -f /app/src/main_version/websocket_server.py ]; then
    log_message "ОШИБКА: Файл websocket_server.py не найден!"
    exit 1
fi

# Устанавливаем переменные окружения из .env файла
log_message "Установка переменных окружения из .env файла..."
if [ -f /app/.env ]; then
    export $(grep -v '^#' /app/.env | xargs)
    log_message "Переменные окружения установлены."
else
    log_message "ОШИБКА: Файл .env не найден при попытке установить переменные окружения."
    exit 1
fi

# Создаем виртуальные окружения и устанавливаем зависимости
log_message "Создание виртуального окружения для RAG сервиса..."
if [ ! -d /opt/venv_rag ]; then
    python -m venv /opt/venv_rag
    log_message "Виртуальное окружение для RAG создано."
else
    log_message "Виртуальное окружение для RAG уже существует."
fi

if [ -f /app/src/main_version/requirements.txt ]; then
    log_message "Установка зависимостей для RAG сервиса..."
    /opt/venv_rag/bin/pip install --no-cache-dir -r /app/src/main_version/requirements.txt
else
    log_message "ПРЕДУПРЕЖДЕНИЕ: Файл requirements.txt для RAG сервиса не найден!"
fi

log_message "Создание виртуального окружения для админ-панели..."
if [ ! -d /opt/venv_admin ]; then
    python -m venv /opt/venv_admin
    log_message "Виртуальное окружение для админ-панели создано."
else
    log_message "Виртуальное окружение для админ-панели уже существует."
fi

if [ -f /app/admin/requirements.txt ]; then
    log_message "Установка зависимостей для админ-панели..."
    /opt/venv_admin/bin/pip install --no-cache-dir -r /app/admin/requirements.txt
else
    log_message "ПРЕДУПРЕЖДЕНИЕ: Файл requirements.txt для админ-панели не найден!"
fi

# Запускаем supervisord
log_message "Запуск supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf 