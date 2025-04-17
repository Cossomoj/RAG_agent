#!/bin/bash

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> /app/logs/setup.log
}

# Инициализация файла журнала
mkdir -p /app/logs
echo "=== Начало настройки $(date '+%Y-%m-%d %H:%M:%S') ===" > /app/logs/setup.log

# Вывод версий установленного ПО для диагностики
log "Версия Python: $(python --version 2>&1)"
log "Версия pip: $(pip --version 2>&1)"
log "Операционная система: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')"

# Создаем директории логов
mkdir -p /var/log/supervisor
log "Созданы директории для логов supervisor"

# Проверка и настройка файла .env
log "Настройка файла .env..."

# Проверяем в различных местах
ENV_LOCATIONS=(
    "/.env"
    "/app/.env"
    "/app/src/main_version/.env"
)

ENV_FOUND=false

for env_path in "${ENV_LOCATIONS[@]}"; do
    if [ -f "$env_path" ]; then
        log "Найден файл .env в $env_path"
        # Если найден, но не в корне /app, копируем его туда
        if [ "$env_path" != "/app/.env" ]; then
            cp "$env_path" "/app/.env"
            log "Файл .env скопирован в /app/.env"
        fi
        ENV_FOUND=true
        break
    fi
done

if [ "$ENV_FOUND" = false ]; then
    log "ПРЕДУПРЕЖДЕНИЕ: Файл .env не найден в известных местах. Многие функции могут быть недоступны!"
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

# Попытаемся загрузить переменные из .env файла в окружение
if [ -f "/app/.env" ]; then
    log "Загружаем переменные из /app/.env в текущую среду..."
    set -a  # Включить export для всех новых переменных
    source /app/.env
    set +a  # Выключить автоматический export
    log "Переменные окружения загружены из .env файла"
fi

# Копирование .env в нужные места
if [ -f "/app/.env" ]; then
    mkdir -p /app/src/main_version
    cp /app/.env /app/src/main_version/.env
    log "Файл .env скопирован в /app/src/main_version/"
    
    mkdir -p /app/admin
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

if [ -n "${TELEGRAM_BOT_TOKEN}" ]; then
    log "TELEGRAM_BOT_TOKEN: доступен (значение скрыто)"
else
    log "TELEGRAM_BOT_TOKEN: НЕ НАЙДЕН"
fi

if [ -n "${TELEGRAM_CHAT_ID}" ]; then
    log "TELEGRAM_CHAT_ID: ${TELEGRAM_CHAT_ID}"
else
    log "TELEGRAM_CHAT_ID: НЕ НАЙДЕН"
fi

if [ -z "${GIGACHAT_API_KEY}" ] || [ -z "${TELEGRAM_API_KEY}" ] || [ -z "${TELEGRAM_BOT_TOKEN}" ]; then
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
    log "Файл скопирован: /app/telegram_bot.py -> /app/src/main_version/telegram_bot.py"
fi

if [ -f "/app/websocket_server.py" ] && [ ! -f "/app/src/main_version/websocket_server.py" ]; then
    log "Перемещаем websocket_server.py в правильное место"
    cp /app/websocket_server.py /app/src/main_version/
    log "Файл скопирован: /app/websocket_server.py -> /app/src/main_version/websocket_server.py"
fi

# Проверяем наличие важных файлов
log "Проверяем наличие критических файлов в директории /app/src/main_version/"
CRITICAL_FILES=("telegram_bot.py" "websocket_server.py")
for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "/app/src/main_version/$file" ]; then
        log "ОШИБКА: Файл $file не найден в /app/src/main_version/"
        if [ -f "/app/$file" ]; then
            cp "/app/$file" "/app/src/main_version/"
            log "Файл $file скопирован из корневой директории"
        else
            log "КРИТИЧЕСКАЯ ОШИБКА: Файл $file не найден нигде в контейнере!"
            # Не выходим, продолжаем установку других компонентов
        fi
    else
        log "Файл $file найден в правильном месте"
    fi
done

# Проверяем содержимое важных файлов
if [ -f "/app/src/main_version/telegram_bot.py" ]; then
    log "Первые 10 строк файла telegram_bot.py:"
    head -n 10 "/app/src/main_version/telegram_bot.py" | while read line; do
        log "| $line"
    done
fi

# Настройка директорий для данных
mkdir -p /app/sqlite_data_rag
if [ ! -f "/app/src/main_version/AI_agent.db" ]; then
    log "База данных не найдена, создаем новую..."
    touch /app/src/main_version/AI_agent.db
    chmod 644 /app/src/main_version/AI_agent.db
    log "Создан пустой файл базы данных: /app/src/main_version/AI_agent.db"
else
    log "Найдена существующая база данных: /app/src/main_version/AI_agent.db"
    log "Размер: $(du -h /app/src/main_version/AI_agent.db | cut -f1)"
fi

# Проверяем структуру директорий
log "Проверяем структуру приложения..."

# Проверяем наличие файлов requirements
if [ ! -f "/app/requirements_rag.txt" ]; then
    log "Ошибка: Отсутствует файл requirements_rag.txt"
    if [ -f "/app/requirements.txt" ]; then
        log "Найден альтернативный файл requirements.txt, используем его"
        cp "/app/requirements.txt" "/app/requirements_rag.txt"
    else
        log "КРИТИЧЕСКАЯ ОШИБКА: Не найдены файлы с зависимостями"
    fi
else
    log "Найден файл requirements_rag.txt"
fi

if [ ! -f "/app/requirements_admin.txt" ]; then
    log "Ошибка: Отсутствует файл requirements_admin.txt"
    # Создаем минимальный файл для админки
    cat > "/app/requirements_admin.txt" << EOF
flask==2.0.1
werkzeug==2.0.1
python-dotenv==0.19.0
flask-login==0.5.0
sqlalchemy==1.4.23
EOF
    log "Создан минимальный файл requirements_admin.txt"
fi

# Проверяем директорию admin
if [ ! -d "/app/admin" ]; then
    log "Ошибка: директория для админ-панели не найдена"
    mkdir -p /app/admin
    log "Создана директория /app/admin"
    
    # Создаем минимальное Flask-приложение
    cat > "/app/admin/app.py" << EOF
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>Admin Panel</h1>
            <p>This is a placeholder admin panel.</p>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF
    log "Создано минимальное Flask-приложение для админ-панели"
fi

# Проверяем наличие Flask приложения
if [ ! -f "/app/admin/app.py" ]; then
    log "Ошибка: файл app.py для админ-панели не найден"
    # Создаем минимальное Flask-приложение
    cat > "/app/admin/app.py" << EOF
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>Admin Panel</h1>
            <p>This is a placeholder admin panel.</p>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF
    log "Создано минимальное Flask-приложение для админ-панели"
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
find /app -type d | sort | while read dir; do
    log "DIR: $dir"
done

log "Файлы в главной директории:"
ls -la /app | grep -v "^d" | while read file; do
    log "FILE: $file"
done

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

# Устанавливаем базовые пакеты
log "Устанавливаем базовые зависимости для RAG сервиса..."
$PATH_RAG/pip install --no-cache-dir pip==23.1.2
$PATH_RAG/pip install --no-cache-dir setuptools==68.0.0 wheel==0.38.4

# Устанавливаем пакеты по одному для избежания конфликтов
log "Устанавливаем пакеты для RAG сервиса из requirements_rag.txt..."
if [ -f "/app/requirements_rag.txt" ]; then
    $PATH_RAG/pip install --no-cache-dir -r /app/requirements_rag.txt
    if [ $? -ne 0 ]; then
        log "ОШИБКА при установке пакетов из requirements_rag.txt"
        log "Пробуем установить основные пакеты по отдельности..."
        
        $PATH_RAG/pip install --no-cache-dir telebot==0.0.5
        $PATH_RAG/pip install --no-cache-dir python-dotenv==1.0.1
        $PATH_RAG/pip install --no-cache-dir asyncio==3.4.3
        $PATH_RAG/pip install --no-cache-dir websockets==12.0
        $PATH_RAG/pip install --no-cache-dir fastapi==0.115.0
        $PATH_RAG/pip install --no-cache-dir uvicorn==0.29.0
        $PATH_RAG/pip install --no-cache-dir python-multipart==0.0.7
    else
        log "Пакеты для RAG сервиса установлены успешно"
    fi
else
    log "КРИТИЧЕСКАЯ ОШИБКА: Файл requirements_rag.txt не найден!"
    # Устанавливаем минимальный набор пакетов
    log "Устанавливаем минимальный набор пакетов..."
    $PATH_RAG/pip install --no-cache-dir telebot==0.0.5
    $PATH_RAG/pip install --no-cache-dir python-dotenv==1.0.1
    $PATH_RAG/pip install --no-cache-dir asyncio==3.4.3
    $PATH_RAG/pip install --no-cache-dir websockets==12.0
    $PATH_RAG/pip install --no-cache-dir fastapi==0.115.0
    $PATH_RAG/pip install --no-cache-dir uvicorn==0.29.0
    $PATH_RAG/pip install --no-cache-dir python-multipart==0.0.7
fi

# Проверяем установленные пакеты
log "Установленные пакеты в окружении RAG сервиса:"
$PATH_RAG/pip list | while read pkg; do
    log "PKG: $pkg"
done

# Настраиваем Admin окружение
log "Настраиваем виртуальное окружение для админ-панели..."
python -m venv /opt/venv_admin
export PATH_ADMIN="/opt/venv_admin/bin"

if [ -f "/app/requirements_admin.txt" ]; then
    $PATH_ADMIN/pip install --no-cache-dir -r /app/requirements_admin.txt
    if [ $? -ne 0 ]; then
        log "ОШИБКА при установке пакетов из requirements_admin.txt"
        # Устанавливаем минимальный набор пакетов
        $PATH_ADMIN/pip install --no-cache-dir flask==2.0.1
        $PATH_ADMIN/pip install --no-cache-dir werkzeug==2.0.1
        $PATH_ADMIN/pip install --no-cache-dir python-dotenv==0.19.0
    else
        log "Пакеты для админ-панели установлены успешно"
    fi
else
    log "ОШИБКА: Файл requirements_admin.txt не найден!"
    # Устанавливаем минимальный набор пакетов
    $PATH_ADMIN/pip install --no-cache-dir flask==2.0.1
    $PATH_ADMIN/pip install --no-cache-dir werkzeug==2.0.1
    $PATH_ADMIN/pip install --no-cache-dir python-dotenv==0.19.0
fi

# Проверяем .env файл в последний раз перед запуском
if [ ! -f "/app/.env" ]; then
    log "КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ: .env файл все еще отсутствует перед запуском supervisor!"
    log "Многие функции могут не работать!"
else
    log ".env файл присутствует, сервисы должны иметь доступ к переменным окружения"
fi

log "Запускаем supervisor..."
log "=== Завершение настройки $(date '+%Y-%m-%d %H:%M:%S') ==="
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf 