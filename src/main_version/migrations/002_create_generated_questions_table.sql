-- Создание таблицы для хранения сгенерированных вопросов
CREATE TABLE IF NOT EXISTS Generated_questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    original_question TEXT NOT NULL,
    original_answer TEXT NOT NULL,
    generated_question TEXT NOT NULL,
    selected BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- Создание индекса для ускорения поиска по user_id
CREATE INDEX IF NOT EXISTS idx_generated_questions_user_id ON Generated_questions(user_id);

-- Создание индекса для поиска по дате создания
CREATE INDEX IF NOT EXISTS idx_generated_questions_created_at ON Generated_questions(created_at); 