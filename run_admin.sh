#!/bin/bash

echo "⚙️ Запуск Admin панели..."

# Переходим в директорию Admin
cd admin

# Проверяем существование виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено. Запустите сначала ./install_dependencies.sh"
    exit 1
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем, что .env файл существует
if [ ! -f "../.env" ]; then
    echo "❌ Файл .env не найден. Создайте его в корневой директории проекта"
    exit 1
fi

# Копируем .env в текущую директорию для загрузки переменных
cp ../.env .

# Устанавливаем переменные для локального запуска
export DATABASE_URL="../src/main_version/AI_agent.db"

echo "🔧 Запуск Flask Admin панели на порту 8002..."
echo "🌐 Admin панель будет доступна по адресу: http://localhost:8002"
echo "🔐 Логин: admin_tg_bot"
echo "🔑 Пароль: 135beton531"
echo ""
echo "📋 Функции админки:"
echo "   • Управление промптами"
echo "   • Управление документами"
echo "   • Просмотр пользователей"
echo "   • Статистика и системные настройки"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Устанавливаем переменные окружения для Flask
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Запускаем Flask приложение
python -m flask run --host=0.0.0.0 --port=8002 