#!/bin/bash

# RAG Agent - Установка зависимостей для новой архитектуры с поддержкой markdown
# Версия 2.0 - Обновлено для 5 векторных баз и .md файлов

set -e  # Останавливаем выполнение при ошибке

echo "🚀 Начинаем установку зависимостей для RAG Agent (новая архитектура)"
echo "=================================================="

# Функция для проверки успешности команды
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 - успешно"
    else
        echo "❌ $1 - ошибка"
        exit 1
    fi
}

# Обновляем системные пакеты
echo "📦 Обновление системных пакетов..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update && sudo apt-get install -y python3-dev python3-pip python3-venv
    check_success "Установка системных зависимостей (Ubuntu/Debian)"
elif command -v brew &> /dev/null; then
    brew install python@3.11
    check_success "Установка Python через Homebrew (macOS)"
else
    echo "⚠️ Автоматическая установка системных пакетов недоступна"
fi

# 1. RAG Сервис (основной компонент)
echo "🧠 Устанавливаем зависимости для RAG сервиса..."
cd src/main_version

if [ ! -d "venv" ]; then
    echo "Создаем виртуальное окружение для RAG сервиса..."
    python3 -m venv venv
    check_success "Создание venv для RAG сервиса"
fi

echo "Активируем окружение и устанавливаем зависимости..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
deactivate
check_success "Установка зависимостей RAG сервиса"

cd ../..

# 2. Web API
echo "🌐 Устанавливаем зависимости для Web API..."
cd webapp/api

if [ ! -d "venv" ]; then
    echo "Создаем виртуальное окружение для Web API..."
    python3 -m venv venv
    check_success "Создание venv для Web API"
fi

echo "Активируем окружение и устанавливаем зависимости..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
deactivate
check_success "Установка зависимостей Web API"

cd ../..

# 3. Admin панель
echo "⚙️ Устанавливаем зависимости для Admin панели..."
cd admin

if [ ! -d "venv" ]; then
    echo "Создаем виртуальное окружение для Admin панели..."
    python3 -m venv venv
    check_success "Создание venv для Admin панели"
fi

echo "Активируем окружение и устанавливаем зависимости..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
deactivate
check_success "Установка зависимостей Admin панели"

cd ..

# 4. Проверяем структуру документов
echo "📁 Проверяем структуру документов..."
if [ ! -d "src/main_version/docs" ]; then
    echo "⚠️ Папка docs не найдена, создаем базовую структуру..."
    mkdir -p src/main_version/docs/{Competency_Lead,Intern,Specialist,PO,full}
    check_success "Создание базовой структуры docs"
else
    echo "✅ Структура docs уже существует"
fi

# 5. Создаем необходимые директории
echo "📂 Создаем необходимые директории..."
mkdir -p logs
mkdir -p backups
check_success "Создание служебных директорий"

# 6. Загружаем языковые модели
echo "🤖 Проверяем языковые модели..."
cd src/main_version
source venv/bin/activate

echo "Загружаем модель для эмбеддингов..."
python3 -c "
import sentence_transformers
try:
    model = sentence_transformers.SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
    print('✅ Модель эмбеддингов загружена успешно')
except Exception as e:
    print(f'❌ Ошибка загрузки модели: {e}')
    exit(1)
"
check_success "Загрузка модели эмбеддингов"

deactivate
cd ../..

# 7. Проверяем .env файлы
echo "🔐 Проверяем конфигурационные файлы..."
if [ ! -f ".env" ]; then
    echo "Создаем базовый .env файл..."
    cat > .env << EOF
# RAG Agent Configuration

# GigaChat API
GIGACHAT_API_KEY=your_gigachat_api_key_here

# Database
DATABASE_URL=AI_agent.db

# Paths (для локального запуска)
DOCS_PATH=src/main_version/docs
LOGS_PATH=logs

# Ports
RAG_SERVICE_PORT=8000
WEBAPP_API_PORT=5001
ADMIN_PANEL_PORT=8002

# Context7 (если используется)
OPENAI_API_KEY=your_openai_api_key_here
EOF
    echo "⚠️ Не забудьте заполнить .env файл своими API ключами!"
fi

# 8. Создаем тестовый markdown документ (если нет документов)
echo "📝 Проверяем наличие тестовых документов..."
if [ ! -f "src/main_version/docs/full/test_document.md" ]; then
    echo "Создаем тестовый документ..."
    cat > src/main_version/docs/full/test_document.md << 'EOF'
# Тестовый документ для RAG системы

## Описание
Это тестовый документ для проверки работы новой архитектуры RAG Agent с поддержкой markdown файлов.

## Функции системы
- Обработка markdown документов
- 5 векторных баз данных
- Улучшенный поиск по семантике
- Поддержка Context7

## Векторные базы
1. **Competency Lead** - для лидов компетенций
2. **Intern** - для стажеров  
3. **Specialist** - для специалистов
4. **PO/PM** - для продакт-менеджеров
5. **Full** - полная база для свободных вопросов

## Технологии
- FastAPI + WebSocket для RAG сервиса
- Flask для веб-интерфейса и админки
- FAISS для векторных индексов
- sentence-transformers для эмбеддингов
- GigaChat для генерации ответов
EOF
    echo "✅ Создан тестовый документ"
fi

# 9. Финальная проверка
echo "🔍 Финальная проверка установки..."

# Проверяем Python окружения
for component in "src/main_version" "webapp/api" "admin"; do
    if [ -d "$component/venv" ]; then
        echo "✅ Виртуальное окружение $component - OK"
    else
        echo "❌ Виртуальное окружение $component - НЕ НАЙДЕНО"
    fi
done

# Проверяем файлы требований
echo "📋 Проверка requirements.txt файлов:"
for req_file in "src/main_version/requirements.txt" "webapp/api/requirements.txt" "admin/requirements.txt"; do
    if [ -f "$req_file" ]; then
        echo "✅ $req_file - найден"
    else
        echo "❌ $req_file - НЕ НАЙДЕН"
    fi
done

echo ""
echo "🎉 Установка зависимостей завершена!"
echo "=================================================="
echo ""
echo "📋 Следующие шаги:"
echo "1. Заполните .env файл своими API ключами"
echo "2. Запустите: ./run_all.sh для старта всех сервисов"
echo "3. Или запустите отдельные компоненты:"
echo "   - ./run_rag_service.sh (RAG сервис)"
echo "   - ./run_webapp_api.sh (веб-интерфейс)"
echo "   - ./run_admin.sh (админ панель)"
echo ""
echo "🔗 Адреса сервисов после запуска:"
echo "   - RAG API: http://localhost:8000"
echo "   - Веб-приложение: http://localhost:5001"
echo "   - Админ панель: http://localhost:8002"
echo ""
echo "✅ Система готова к работе с новой архитектурой markdown документов!" 