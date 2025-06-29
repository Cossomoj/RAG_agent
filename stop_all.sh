#!/bin/bash

echo "🛑 Остановка всех сервисов RAG Agent..."

# Находим и останавливаем процессы по портам
echo "🔍 Поиск запущенных процессов..."

# RAG сервис на порту 8000
RAG_PID=$(lsof -ti:8000)
if [ ! -z "$RAG_PID" ]; then
    echo "🔥 Остановка RAG сервиса (PID: $RAG_PID)..."
    kill -TERM $RAG_PID
    sleep 2
    if kill -0 $RAG_PID 2>/dev/null; then
        kill -KILL $RAG_PID
    fi
    echo "   ✅ RAG сервис остановлен"
else
    echo "   ℹ️  RAG сервис не запущен"
fi

# Web API на порту 5001  
API_PID=$(lsof -ti:5001)
if [ ! -z "$API_PID" ]; then
    echo "🌐 Остановка Web API (PID: $API_PID)..."
    kill -TERM $API_PID
    sleep 2
    if kill -0 $API_PID 2>/dev/null; then
        kill -KILL $API_PID
    fi
    echo "   ✅ Web API остановлен"
else
    echo "   ℹ️  Web API не запущен"
fi

# Admin панель на порту 8002
ADMIN_PID=$(lsof -ti:8002)
if [ ! -z "$ADMIN_PID" ]; then
    echo "⚙️ Остановка Admin панели (PID: $ADMIN_PID)..."
    kill -TERM $ADMIN_PID
    sleep 2
    if kill -0 $ADMIN_PID 2>/dev/null; then
        kill -KILL $ADMIN_PID
    fi
    echo "   ✅ Admin панель остановлена"
else
    echo "   ℹ️  Admin панель не запущена"
fi

# Telegram бот
BOT_PIDS=$(pgrep -f "telegram_bot.py")
if [ ! -z "$BOT_PIDS" ]; then
    echo "🤖 Остановка Telegram бота..."
    for pid in $BOT_PIDS; do
        kill -TERM $pid
        echo "   ✅ Бот остановлен (PID: $pid)"
    done
else
    echo "   ℹ️  Telegram бот не запущен"
fi

# Также останавливаем процессы Python, которые могут быть связаны с проектом
echo ""
echo "🧹 Очистка связанных процессов..."
PYTHON_PIDS=$(pgrep -f "rag_service\|uvicorn.*rag_service")
if [ ! -z "$PYTHON_PIDS" ]; then
    for pid in $PYTHON_PIDS; do
        kill -TERM $pid 2>/dev/null
        echo "   ✅ Python процесс остановлен (PID: $pid)"
    done
fi

echo ""
echo "🏁 Все сервисы остановлены"
echo ""
echo "📋 Для проверки запущенных процессов:"
echo "   netstat -tulpn | grep -E ':(8000|5001|8002)'" 