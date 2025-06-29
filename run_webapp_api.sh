#!/bin/bash

echo "🌐 Запуск Web API..."

# Переходим в директорию Web API
cd webapp/api

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

# Устанавливаем переменные для локального запуска
export DATABASE_URL="../../src/main_version/AI_agent.db"
export RAG_PATH="../../src/main_version"

# Проверяем, что RAG сервис запущен
echo "🔍 Проверка доступности RAG сервиса..."
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo "⚠️  Внимание: RAG сервис (localhost:8000) недоступен."
    echo "   Убедитесь, что он запущен (./run_rag_service.sh)"
    echo "   Продолжаем запуск Web API..."
fi

echo "🚀 Запуск Flask Web API на порту 5001..."
echo "🌐 Web API будет доступен по адресу: http://localhost:5001"
echo "📋 Основные эндпоинты:"
echo "   • POST /api/ask - отправка вопросов"
echo "   • GET  /api/questions - получение библиотеки вопросов"
echo "   • GET  /api/health - проверка здоровья"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Устанавливаем переменные окружения для Flask
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Запускаем Flask приложение
python -m flask run --host=0.0.0.0 --port=5001 