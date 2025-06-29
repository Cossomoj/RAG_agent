#!/bin/bash

# Скрипт для запуска всех компонентов RAG Agent
# Убедитесь, что все виртуальные окружения созданы и зависимости установлены

# Функция для запуска компонента в новой вкладке терминала (macOS)
run_in_new_tab() {
    osascript -e "tell application \"Terminal\" to do script \"$1\""
}

echo "🚀 Запуск всех сервисов RAG Agent..."

# 1. Запуск RAG Service
echo "1. Запускаю RAG Service (FastAPI + WebSocket)..."
CMD_RAG="cd $(pwd)/src/main_version && source venv/bin/activate && python rag_service.py"
run_in_new_tab "$CMD_RAG"

# 2. Запуск WebApp API
echo "2. Запускаю WebApp API (Flask)..."
CMD_WEBAPI="cd $(pwd)/webapp/api && source venv/bin/activate && python app.py"
run_in_new_tab "$CMD_WEBAPI"

# 3. Запуск Admin Panel
echo "3. Запускаю Admin Panel (Flask)..."
CMD_ADMIN="cd $(pwd)/admin && source venv/bin/activate && python app.py"
run_in_new_tab "$CMD_ADMIN"

# 4. Запуск Telegram Bot
echo "4. Запускаю Telegram Bot..."
CMD_BOT="cd $(pwd)/src/main_version && source venv/bin/activate && python telegram_bot.py"
run_in_new_tab "$CMD_BOT"


echo "✅ Все сервисы запущены в отдельных вкладках терминала."
echo "Используйте 'stop_all.sh' для остановки." 