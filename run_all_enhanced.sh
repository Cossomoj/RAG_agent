#!/bin/bash

# Улучшенный скрипт запуска RAG Agent с централизованной конфигурацией
# Исправляет все обнаруженные проблемы:
# 1. Использует config.yaml для настроек
# 2. Проверяет все зависимости
# 3. Валидирует конфигурацию
# 4. Создает резервную копию БД
# 5. Запускает мониторинг

set -e  # Остановка при ошибке

echo "🚀 Запуск RAG Agent (Enhanced Version)"
echo "======================================="
echo ""

# Проверка наличия config.yaml
if [ ! -f "config.yaml" ]; then
    echo "❌ Файл config.yaml не найден!"
    echo "   Создайте конфигурационный файл перед запуском"
    exit 1
fi

# Валидация конфигурации
echo "🔍 Валидация конфигурации..."
if python3 scripts/validate_config.py config.yaml; then
    echo "✅ Конфигурация валидна"
else
    echo "❌ Ошибка в конфигурации. Исправьте и запустите снова."
    exit 1
fi

echo ""

# Проверка зависимостей
echo "📦 Проверка зависимостей..."

check_venv() {
    local service_name=$1
    local venv_path=$2
    
    echo -n "   $service_name: "
    if [ -d "$venv_path" ]; then
        echo "✅ venv найден"
        return 0
    else
        echo "❌ venv не найден в $venv_path"
        return 1
    fi
}

check_venv "RAG Service" "src/main_version/venv"
check_venv "Web API" "webapp/api/venv" 
check_venv "Admin Panel" "admin/venv"

echo ""

# Создание резервной копии
echo "💾 Создание резервной копии базы данных..."
if [ -f "scripts/backup_database.sh" ]; then
    ./scripts/backup_database.sh
else
    echo "⚠️  Скрипт резервного копирования не найден"
fi

echo ""

# Функция для получения настроек из config.yaml
get_config_value() {
    python3 -c "
import yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
value = config
for key in '$1'.split('.'):
    value = value.get(key, '')
print(value)
"
}

# Получаем порты из конфигурации
RAG_PORT=$(get_config_value "network.rag_service.port")
WEB_PORT=$(get_config_value "network.webapp_api.port")
ADMIN_PORT=$(get_config_value "network.admin_panel.port")

echo "🔧 Настройки из config.yaml:"
echo "   RAG Service: localhost:$RAG_PORT"
echo "   Web API: localhost:$WEB_PORT" 
echo "   Admin Panel: localhost:$ADMIN_PORT"
echo ""

# Функция проверки занятости порта
check_port_free() {
    local port=$1
    local service=$2
    
    if lsof -i :$port > /dev/null 2>&1; then
        echo "⚠️  Порт $port занят ($service)"
        echo "   Останавливаю процесс..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Проверяем и освобождаем порты
echo "🔌 Проверка портов..."
check_port_free $RAG_PORT "RAG Service"
check_port_free $WEB_PORT "Web API"
check_port_free $ADMIN_PORT "Admin Panel"

echo ""

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p logs
mkdir -p backups
mkdir -p src/main_version/docs
mkdir -p src/main_version/txt_docs

# Запуск сервисов
echo "🚀 Запуск сервисов..."
echo ""

# 1. RAG Service
echo "1️⃣ Запуск RAG сервиса (порт $RAG_PORT)..."
./run_rag_service.sh > logs/rag_service.log 2>&1 &
RAG_PID=$!
echo "   PID: $RAG_PID"

# Ждем запуска RAG сервиса
echo "   ⏳ Ожидание запуска RAG сервиса..."
for i in {1..30}; do
    if curl -s http://localhost:$RAG_PORT/docs > /dev/null 2>&1; then
        echo "   ✅ RAG сервис запущен"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "   ❌ RAG сервис не запустился. Проверьте logs/rag_service.log"
        ./stop_all.sh
        exit 1
    fi
    sleep 2
done

# 2. Web API
echo ""
echo "2️⃣ Запуск Web API (порт $WEB_PORT)..."
./run_webapp_api.sh > logs/webapp_api.log 2>&1 &
WEB_PID=$!
echo "   PID: $WEB_PID"

# Ждем запуска Web API
echo "   ⏳ Ожидание запуска Web API..."
for i in {1..20}; do
    if curl -s http://localhost:$WEB_PORT/api/health > /dev/null 2>&1; then
        echo "   ✅ Web API запущен"
        break
    fi
    if [ $i -eq 20 ]; then
        echo "   ❌ Web API не запустился. Проверьте logs/webapp_api.log"
        ./stop_all.sh
        exit 1
    fi
    sleep 2
done

# 3. Admin Panel
echo ""
echo "3️⃣ Запуск Admin панели (порт $ADMIN_PORT)..."
./run_admin.sh > logs/admin.log 2>&1 &
ADMIN_PID=$!
echo "   PID: $ADMIN_PID"

# Ждем запуска Admin панели
echo "   ⏳ Ожидание запуска Admin панели..."
for i in {1..20}; do
    if curl -s http://localhost:$ADMIN_PORT/ > /dev/null 2>&1; then
        echo "   ✅ Admin панель запущена"
        break
    fi
    if [ $i -eq 20 ]; then
        echo "   ❌ Admin панель не запустилась. Проверьте logs/admin.log"
        ./stop_all.sh
        exit 1
    fi
    sleep 2
done

# 4. Telegram Bot
echo ""
echo "4️⃣ Запуск Telegram бота..."
./run_telegram_bot.sh > logs/telegram_bot.log 2>&1 &
BOT_PID=$!
echo "   PID: $BOT_PID"

# Ждем запуска бота
sleep 5
if ps -p $BOT_PID > /dev/null; then
    echo "   ✅ Telegram бот запущен"
else
    echo "   ❌ Telegram бот не запустился. Проверьте logs/telegram_bot.log"
fi

echo ""
echo "🎉 Все сервисы RAG Agent запущены!"
echo "=================================="
echo ""
echo "📋 Доступные сервисы:"
echo "   🔥 RAG API:      http://localhost:$RAG_PORT (docs: /docs)"
echo "   🌐 Web App:      http://localhost:$WEB_PORT"
echo "   ⚙️  Admin панель: http://localhost:$ADMIN_PORT"
echo "   🤖 Telegram бот: работает в фоне"
echo ""

# Получаем данные админа из конфигурации
ADMIN_USER=$(get_config_value "admin.username")
ADMIN_PASS=$(get_config_value "admin.password")

echo "🔐 Данные для входа в админку:"
echo "   👤 Логин: $ADMIN_USER"
echo "   🔑 Пароль: $ADMIN_PASS"
echo ""

# Запуск мониторинга в фоне
if [ -f "scripts/health_check.sh" ]; then
    echo "🏥 Запуск мониторинга здоровья..."
    (
        while true; do
            sleep 60
            ./scripts/health_check.sh > logs/health_check.log 2>&1
        done
    ) &
    MONITOR_PID=$!
    echo "   ✅ Мониторинг запущен (PID: $MONITOR_PID)"
fi

echo ""
echo "📊 Статистика:"
echo "   Процессы: $(ps aux | grep -E "(rag_service|flask|telegram_bot)" | grep -v grep | wc -l)"
echo "   Открытые порты: $(lsof -i :$RAG_PORT,:$WEB_PORT,:$ADMIN_PORT 2>/dev/null | wc -l)"
echo ""

echo "✅ Система RAG Agent полностью готова к работе!"
echo ""
echo "📋 Полезные команды:"
echo "   ./stop_all.sh                    - остановить все сервисы"  
echo "   ./scripts/health_check.sh        - проверить здоровье системы"
echo "   ./scripts/backup_database.sh     - создать резервную копию"
echo "   tail -f logs/<service>.log       - просмотр логов сервиса"
echo ""

# Держим скрипт активным для мониторинга
echo "🔄 Мониторинг запущен. Нажмите Ctrl+C для остановки всех сервисов."

# Обработчик сигнала для корректной остановки
trap 'echo ""; echo "🛑 Получен сигнал остановки..."; ./stop_all.sh; exit 0' INT TERM

# Ожидание в фоне
while true; do
    sleep 10
    
    # Проверяем, что все процессы еще живы
    if ! ps -p $RAG_PID > /dev/null 2>&1; then
        echo "⚠️  RAG сервис остановился"
        break
    fi
    if ! ps -p $WEB_PID > /dev/null 2>&1; then
        echo "⚠️  Web API остановился"
        break
    fi
    if ! ps -p $ADMIN_PID > /dev/null 2>&1; then
        echo "⚠️  Admin панель остановилась"
        break
    fi
done

echo "❌ Один из сервисов остановился. Завершение работы..."
./stop_all.sh 