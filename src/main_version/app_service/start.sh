#!/bin/bash

# Создаем директории логов
mkdir -p /var/log/supervisor

# Настройка директорий для данных
mkdir -p /app/sqlite_data_rag
if [ ! -f "/app/src/main_version/AI_agent.db" ]; then
    echo "База данных не найдена, создаем новую..."
    touch /app/src/main_version/AI_agent.db
fi

# Проверяем наличие файлов requirements
if [ ! -f "/app/requirements_rag.txt" ] || [ ! -f "/app/requirements_admin.txt" ]; then
    echo "Ошибка: Отсутствуют файлы requirements_rag.txt или requirements_admin.txt"
    exit 1
fi

# Запускаем supervisor
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf 