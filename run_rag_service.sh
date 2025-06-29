#!/bin/bash

echo "🔥 Запуск RAG сервиса..."

# Переходим в директорию RAG сервиса
cd src/main_version

# Проверяем существование виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено. Запустите сначала ./install_dependencies.sh"
    exit 1
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем, что .env файл существует
if [ ! -f "../../.env" ]; then
    echo "❌ Файл .env не найден. Создайте его в корневой директории проекта"
    exit 1
fi

# Копируем .env в текущую директорию для загрузки переменных
cp ../../.env .

# Устанавливаем переменную для пути к базе данных для локального запуска
export DATABASE_URL="AI_agent.db"

echo "📡 Запуск FastAPI сервера на порту 8000..."
echo "🌐 RAG API будет доступен по адресу: http://localhost:8000"
echo "📈 WebSocket: ws://localhost:8000/ws"
echo "📋 Документация API: http://localhost:8000/docs"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Запускаем RAG сервис
uvicorn rag_service:app --host 0.0.0.0 --port 8000 --reload 