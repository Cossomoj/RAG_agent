#!/bin/bash

# Скрипт мониторинга здоровья RAG Agent
# Проверяет доступность всех сервисов

echo "🔍 Проверка здоровья системы RAG Agent..."
echo ""

# Функция проверки HTTP endpoint
check_http() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "   $name: "
    
    # Проверяем доступность с таймаутом 5 секунд
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
    
    if [ "$http_code" = "$expected_code" ]; then
        echo "✅ OK (HTTP $http_code)"
        return 0
    else
        echo "❌ FAIL (HTTP $http_code)"
        return 1
    fi
}

# Функция проверки порта
check_port() {
    local name=$1
    local port=$2
    
    echo -n "   $name (порт $port): "
    
    if lsof -i :$port > /dev/null 2>&1; then
        echo "✅ Активен"
        return 0
    else
        echo "❌ Неактивен"
        return 1
    fi
}

# Функция проверки процесса
check_process() {
    local name=$1
    local pattern=$2
    
    echo -n "   $name: "
    
    if pgrep -f "$pattern" > /dev/null; then
        pid=$(pgrep -f "$pattern" | tr '\n' ' ')
        echo "✅ Запущен (PID: $pid)"
        return 0
    else
        echo "❌ Не запущен"
        return 1
    fi
}

# Проверка файловой системы
echo "📁 Файловая система:"
check_file() {
    local name=$1
    local path=$2
    
    echo -n "   $name: "
    
    if [ -f "$path" ]; then
        size=$(du -h "$path" | cut -f1)
        echo "✅ Существует ($size)"
        return 0
    elif [ -d "$path" ]; then
        count=$(find "$path" -type f | wc -l)
        echo "✅ Существует ($count файлов)"
        return 0
    else
        echo "❌ Не найден"
        return 1
    fi
}

check_file "База данных" "src/main_version/AI_agent.db"
check_file "Конфигурация" "config.yaml"
check_file "Логи" "logs"
check_file "Документы" "src/main_version/docs"

echo ""
echo "🔌 Сетевые порты:"
check_port "RAG Service" 8000
check_port "Web API" 5001 
check_port "Admin Panel" 8002
check_port "Telegram Bot Cache" 8007

echo ""
echo "⚙️ Процессы:"
check_process "RAG Service" "rag_service"
check_process "Web API" "flask.*5001"
check_process "Admin Panel" "flask.*8002"
check_process "Telegram Bot" "telegram_bot"

echo ""
echo "🌐 HTTP Endpoints:"
check_http "RAG API" "http://localhost:8000/docs"
check_http "Web API Health" "http://localhost:5001/api/health"
check_http "Web App" "http://localhost:5001/"
check_http "Admin Panel" "http://localhost:8002/"

# Проверка ресурсов системы
echo ""
echo "💻 Системные ресурсы:"

# Использование диска
disk_usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
echo -n "   Диск: "
if [ "$disk_usage" -lt 90 ]; then
    echo "✅ OK (использовано ${disk_usage}%)"
else
    echo "⚠️  ВНИМАНИЕ (использовано ${disk_usage}%)"
fi

# Использование памяти
if command -v free > /dev/null; then
    mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    echo -n "   Память: "
    if [ "$mem_usage" -lt 90 ]; then
        echo "✅ OK (использовано ${mem_usage}%)"
    else
        echo "⚠️  ВНИМАНИЕ (использовано ${mem_usage}%)"
    fi
fi

# Проверка логов на ошибки
echo ""
echo "📋 Анализ логов:"
if [ -d "logs" ]; then
    for log_file in logs/*.log; do
        if [ -f "$log_file" ]; then
            log_name=$(basename "$log_file" .log)
            error_count=$(grep -c -i "error\|exception\|critical" "$log_file" 2>/dev/null || echo "0")
            echo -n "   $log_name: "
            if [ "$error_count" -eq 0 ]; then
                echo "✅ Без ошибок"
            else
                echo "⚠️  $error_count ошибок"
            fi
        fi
    done
fi

echo ""
echo "🎯 Проверка здоровья завершена!" 