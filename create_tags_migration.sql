-- SQL скрипт для создания системы тегов и миграции от категорий к тегам

-- Создание таблицы тегов
CREATE TABLE IF NOT EXISTS Tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#6c757d',
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы связей вопросов и тегов (многие-ко-многим)
CREATE TABLE IF NOT EXISTS QuestionTags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES Questions(question_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES Tags(id) ON DELETE CASCADE,
    UNIQUE(question_id, tag_id)
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_question_tags_question_id ON QuestionTags(question_id);
CREATE INDEX IF NOT EXISTS idx_question_tags_tag_id ON QuestionTags(tag_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON Tags(name);

-- Миграция существующих категорий в теги
INSERT OR IGNORE INTO Tags (name, color, description)
SELECT DISTINCT 
    category,
    CASE 
        WHEN category = 'methodology' THEN '#007bff'
        WHEN category = 'development' THEN '#28a745'
        WHEN category = 'analysis' THEN '#ffc107'
        WHEN category = 'java' THEN '#fd7e14'
        WHEN category = 'python' THEN '#20c997'
        WHEN category = 'web' THEN '#6f42c1'
        WHEN category = 'testing' THEN '#dc3545'
        WHEN category = 'leadership' THEN '#6c757d'
        WHEN category = 'product' THEN '#e83e8c'
        WHEN category = 'general' THEN '#17a2b8'
        ELSE '#6c757d'
    END as color,
    CASE 
        WHEN category = 'methodology' THEN 'Методологии разработки'
        WHEN category = 'development' THEN 'Разработка'
        WHEN category = 'analysis' THEN 'Анализ'
        WHEN category = 'java' THEN 'Java разработка'
        WHEN category = 'python' THEN 'Python разработка'
        WHEN category = 'web' THEN 'Web разработка'
        WHEN category = 'testing' THEN 'Тестирование'
        WHEN category = 'leadership' THEN 'Лидерство'
        WHEN category = 'product' THEN 'Продуктовая разработка'
        WHEN category = 'general' THEN 'Общие вопросы'
        ELSE 'Без описания'
    END as description
FROM Questions 
WHERE category IS NOT NULL AND category != '';

-- Создание связей между вопросами и тегами на основе существующих категорий
INSERT OR IGNORE INTO QuestionTags (question_id, tag_id)
SELECT q.question_id, t.id
FROM Questions q
JOIN Tags t ON q.category = t.name
WHERE q.category IS NOT NULL AND q.category != '';

-- Добавление тригgers для обновления updated_at
CREATE TRIGGER IF NOT EXISTS update_tags_updated_at
    AFTER UPDATE ON Tags
    FOR EACH ROW
BEGIN
    UPDATE Tags SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 