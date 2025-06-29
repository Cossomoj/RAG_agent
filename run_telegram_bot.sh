#!/bin/bash

echo "🤖 Запуск Telegram бота..."

# Переходим в директорию RAG сервиса (там же лежит telegram_bot.py)
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

# Проверяем, что RAG сервис запущен
echo "🔍 Проверка доступности RAG сервиса..."
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo "⚠️  Внимание: RAG сервис (localhost:8000) недоступен."
    echo "   Убедитесь, что он запущен (./run_rag_service.sh)"
    echo "   Продолжаем запуск бота..."
fi

echo "📱 Запуск Telegram бота..."
echo "🔗 Бот будет подключаться к RAG сервису: ws://127.0.0.1:8000/ws"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Запускаем Telegram бота
python telegram_bot.py 