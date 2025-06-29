#!/bin/bash

echo "🚀 Запуск всех компонентов RAG Agent системы..."

# Функция для остановки всех процессов при завершении скрипта
cleanup() {
    echo ""
    echo "🛑 Остановка всех сервисов..."
    
    # Останавливаем процессы по PID
    if [ ! -z "$RAG_PID" ]; then
        kill $RAG_PID 2>/dev/null
        echo "   ✅ RAG сервис остановлен"
    fi
    
    if [ ! -z "$BOT_PID" ]; then
        kill $BOT_PID 2>/dev/null
        echo "   ✅ Telegram бот остановлен"
    fi
    
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
        echo "   ✅ Web API остановлен"
    fi
    
    if [ ! -z "$ADMIN_PID" ]; then
        kill $ADMIN_PID 2>/dev/null
        echo "   ✅ Admin панель остановлена"
    fi
    
    echo "🏁 Все сервисы остановлены"
    exit 0
}

# Устанавливаем обработчик сигналов для корректного завершения
trap cleanup SIGINT SIGTERM

# Проверяем, что зависимости установлены
echo "🔍 Проверка зависимостей..."
if [ ! -d "src/main_version/venv" ] || [ ! -d "webapp/api/venv" ] || [ ! -d "admin/venv" ]; then
    echo "❌ Не все зависимости установлены. Запустите: ./install_dependencies.sh"
    exit 1
fi

# Проверяем .env файл
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден в корневой директории"
    exit 1
fi

echo "✅ Все проверки пройдены"
echo ""

# Создаем папку для логов, если она не существует
mkdir -p logs

# Запускаем RAG сервис
echo "1️⃣ Запуск RAG сервиса (порт 8000)..."
./run_rag_service.sh > logs/rag_service.log 2>&1 &
RAG_PID=$!
echo "   PID: $RAG_PID"

# Ждем, пока RAG сервис запустится
echo "   ⏳ Ожидание запуска RAG сервиса..."
sleep 10

# Проверяем, что RAG сервис запустился
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo "   ❌ RAG сервис не запустился. Проверьте logs/rag_service.log"
    cleanup
    exit 1
fi
echo "   ✅ RAG сервис запущен"

# Запускаем Web API
echo ""
echo "2️⃣ Запуск Web API (порт 5001)..."
./run_webapp_api.sh > logs/webapp_api.log 2>&1 &
API_PID=$!
echo "   PID: $API_PID"
sleep 3
echo "   ✅ Web API запущен"

# Запускаем Admin панель
echo ""
echo "3️⃣ Запуск Admin панели (порт 8002)..."
./run_admin.sh > logs/admin.log 2>&1 &
ADMIN_PID=$!
echo "   PID: $ADMIN_PID"
sleep 3
echo "   ✅ Admin панель запущена"

# Запускаем Telegram бота
echo ""
echo "4️⃣ Запуск Telegram бота..."
./run_telegram_bot.sh > logs/telegram_bot.log 2>&1 &
BOT_PID=$!
echo "   PID: $BOT_PID"
sleep 3
echo "   ✅ Telegram бот запущен"

echo ""
echo "🎉 Все компоненты запущены успешно!"
echo ""
echo "📋 Доступные сервисы:"
echo "   🔥 RAG API:      http://localhost:8000 (docs: /docs)"
echo "   🌐 Web API:      http://localhost:5001"
echo "   ⚙️  Admin панель: http://localhost:8002"
echo "   🤖 Telegram бот: работает в фоне"
echo ""
echo "📊 Логи сохраняются в папку logs/"
echo "🛑 Для остановки всех сервисов нажмите Ctrl+C"
echo ""
echo "⏳ Ожидание... (мониторинг процессов)"

# Мониторинг процессов
while true; do
    sleep 30
    
    # Проверяем, что все процессы еще работают
    if ! kill -0 $RAG_PID 2>/dev/null; then
        echo "❌ RAG сервис прекратил работу"
        cleanup
        exit 1
    fi
    
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "❌ Web API прекратил работу"
        cleanup
        exit 1
    fi
    
    if ! kill -0 $ADMIN_PID 2>/dev/null; then
        echo "❌ Admin панель прекратила работу"
        cleanup
        exit 1
    fi
    
    if ! kill -0 $BOT_PID 2>/dev/null; then
        echo "❌ Telegram бот прекратил работу"
        cleanup
        exit 1
    fi
done 