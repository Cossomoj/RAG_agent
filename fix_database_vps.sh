#!/bin/bash

# Скрипт для исправления базы данных на VPS
# Выполнить на VPS: ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85

echo "🔧 Исправление базы данных AI_agent.db на VPS..."

# Путь к базе данных на VPS
DB_PATH="/home/user1/sqlite_data_rag/AI_agent.db"

# Проверяем существование базы данных
if [ ! -f "$DB_PATH" ]; then
    echo "❌ База данных не найдена: $DB_PATH"
    echo "Создаем новую базу данных..."
    touch "$DB_PATH"
fi

# Проверяем текущие таблицы
echo "📋 Текущие таблицы в базе данных:"
sqlite3 "$DB_PATH" ".tables"

# Проверяем существование таблицы Questions
QUESTIONS_EXISTS=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='Questions';" | wc -l)

if [ "$QUESTIONS_EXISTS" -eq 0 ]; then
    echo "❌ Таблица Questions не найдена. Создаем недостающие таблицы..."
    
    # Создаем таблицы из SQL скрипта
    cat << 'EOF' | sqlite3 "$DB_PATH"
-- Создание таблицы VectorStores
CREATE TABLE IF NOT EXISTS VectorStores (
    name TEXT PRIMARY KEY,
    display_name TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы Prompts
CREATE TABLE IF NOT EXISTS Prompts (
    question_id INTEGER PRIMARY KEY,
    prompt_template TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы Questions
CREATE TABLE IF NOT EXISTS Questions (
    question_id INTEGER PRIMARY KEY,
    question_text TEXT NOT NULL,
    category TEXT,
    role TEXT,
    specialization TEXT,
    vector_store TEXT,
    prompt_id INTEGER,
    callback_data TEXT,
    order_position INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prompt_id) REFERENCES Prompts(question_id),
    FOREIGN KEY (vector_store) REFERENCES VectorStores(name)
);

-- Вставка тестовых данных в VectorStores
INSERT OR REPLACE INTO VectorStores (name, display_name, description) VALUES
('docs_pack_bsa', 'БизнесАналитик', 'Документы для бизнес-аналитиков'),
('docs_pack_java', 'Java Developer', 'Документы для Java разработчиков'),
('docs_pack_python', 'Python Developer', 'Документы для Python разработчиков'),
('docs_pack_web', 'Web Developer', 'Документы для веб-разработчиков'),
('docs_pack_test', 'QA Engineer', 'Документы для тестировщиков'),
('auto', 'Авто-выбор', 'Автоматический выбор векторного хранилища');

-- Вставка тестовых промптов
INSERT OR REPLACE INTO Prompts (question_id, prompt_template) VALUES
(1, 'Ты - опытный наставник для {role} с специализацией {specialization}. Ответь на вопрос: {question}'),
(2, 'Ты - эксперт по {specialization}. Подробно объясни: {question}'),
(3, 'Ты - ментор для {role}. Дай практические советы по: {question}');

-- Вставка тестовых вопросов
INSERT OR REPLACE INTO Questions (question_id, question_text, category, role, specialization, vector_store, prompt_id, callback_data, order_position, is_active) VALUES
-- Общие вопросы
(1, 'Расскажи о методологии разработки ПО', 'methodology', NULL, NULL, 'auto', 1, 'q_1', 1, 1),
(2, 'Что такое SDLC и его этапы?', 'methodology', NULL, NULL, 'auto', 1, 'q_2', 2, 1),
(3, 'Основы Agile разработки', 'methodology', NULL, NULL, 'auto', 1, 'q_3', 3, 1),
(4, 'Что такое DevOps?', 'methodology', NULL, NULL, 'auto', 1, 'q_4', 4, 1),
(5, 'Принципы чистого кода', 'development', NULL, NULL, 'auto', 1, 'q_5', 5, 1),

-- Вопросы для аналитиков
(10, 'Как писать технические требования?', 'analysis', 'Специалист', 'Аналитик', 'docs_pack_bsa', 2, 'q_10', 10, 1),
(11, 'Методы сбора требований', 'analysis', 'Специалист', 'Аналитик', 'docs_pack_bsa', 2, 'q_11', 11, 1),
(12, 'UML диаграммы для аналитиков', 'analysis', 'Специалист', 'Аналитик', 'docs_pack_bsa', 2, 'q_12', 12, 1),

-- Вопросы для Java разработчиков
(20, 'Основы Java для начинающих', 'java', 'Специалист', 'Java', 'docs_pack_java', 2, 'q_20', 20, 1),
(21, 'Spring Framework основы', 'java', 'Специалист', 'Java', 'docs_pack_java', 2, 'q_21', 21, 1),
(22, 'Паттерны проектирования в Java', 'java', 'Специалист', 'Java', 'docs_pack_java', 2, 'q_22', 22, 1),

-- Вопросы для Python разработчиков
(30, 'Основы Python разработки', 'python', 'Специалист', 'Python', 'docs_pack_python', 2, 'q_30', 30, 1),
(31, 'Django или Flask - что выбрать?', 'python', 'Специалист', 'Python', 'docs_pack_python', 2, 'q_31', 31, 1),
(32, 'Тестирование в Python', 'python', 'Специалист', 'Python', 'docs_pack_python', 2, 'q_32', 32, 1),

-- Вопросы для веб-разработчиков
(40, 'HTML/CSS основы', 'web', 'Специалист', 'WEB', 'docs_pack_web', 2, 'q_40', 40, 1),
(41, 'JavaScript современные возможности', 'web', 'Специалист', 'WEB', 'docs_pack_web', 2, 'q_41', 41, 1),
(42, 'React или Vue - что выбрать?', 'web', 'Специалист', 'WEB', 'docs_pack_web', 2, 'q_42', 42, 1),

-- Вопросы для тестировщиков
(50, 'Основы тестирования ПО', 'testing', 'Специалист', 'Тестировщик', 'docs_pack_test', 2, 'q_50', 50, 1),
(51, 'Автоматизация тестирования', 'testing', 'Специалист', 'Тестировщик', 'docs_pack_test', 2, 'q_51', 51, 1),
(52, 'Виды тестирования', 'testing', 'Специалист', 'Тестировщик', 'docs_pack_test', 2, 'q_52', 52, 1),

-- Вопросы для лидов
(60, 'Управление командой разработки', 'leadership', 'Лид компетенции', NULL, 'auto', 3, 'q_60', 60, 1),
(61, 'Код-ревью: лучшие практики', 'leadership', 'Лид компетенции', NULL, 'auto', 3, 'q_61', 61, 1),
(62, 'Планирование спринтов', 'leadership', 'Лид компетенции', NULL, 'auto', 3, 'q_62', 62, 1),

-- Вопросы для PO/PM
(70, 'Основы Product Management', 'product', 'PO/PM', NULL, 'auto', 3, 'q_70', 70, 1),
(71, 'Работа с заказчиками', 'product', 'PO/PM', NULL, 'auto', 3, 'q_71', 71, 1),
(72, 'Приоритизация задач', 'product', 'PO/PM', NULL, 'auto', 3, 'q_72', 72, 1),

-- Специальные вопросы
(888, 'Свободный вопрос', 'general', NULL, NULL, 'auto', 1, 'q_888', 888, 1),
(777, 'Помощь с заданием', 'general', NULL, NULL, 'auto', 1, 'q_777', 777, 1);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_questions_role ON Questions(role);
CREATE INDEX IF NOT EXISTS idx_questions_specialization ON Questions(specialization);
CREATE INDEX IF NOT EXISTS idx_questions_category ON Questions(category);
CREATE INDEX IF NOT EXISTS idx_questions_active ON Questions(is_active);
CREATE INDEX IF NOT EXISTS idx_questions_order ON Questions(order_position);
CREATE INDEX IF NOT EXISTS idx_message_history_user ON Message_history(user_id);
CREATE INDEX IF NOT EXISTS idx_message_history_time ON Message_history(time);
EOF

    echo "✅ Таблицы созданы успешно!"
else
    echo "✅ Таблица Questions уже существует"
fi

# Проверяем результат
echo "📊 Финальные таблицы в базе данных:"
sqlite3 "$DB_PATH" ".tables"

# Проверяем количество вопросов
QUESTIONS_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM Questions WHERE is_active = 1;")
echo "📋 Количество активных вопросов: $QUESTIONS_COUNT"

# Проверяем количество категорий
CATEGORIES_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(DISTINCT category) FROM Questions WHERE category IS NOT NULL AND is_active = 1;")
echo "📂 Количество категорий: $CATEGORIES_COUNT"

echo "🎉 Миграция базы данных завершена!"
echo ""
echo "📋 Для проверки выполните:"
echo "  sqlite3 $DB_PATH \"SELECT category, COUNT(*) FROM Questions WHERE is_active = 1 GROUP BY category;\""
echo ""
echo "🔄 Перезапустите веб-приложение для применения изменений" 