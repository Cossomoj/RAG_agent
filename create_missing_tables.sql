-- SQL скрипт для создания недостающих таблиц в базе данных AI_agent.db на VPS

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
(1, 'Расскажи о методологии разработки ПО', 'methodology', NULL, NULL, 'auto', 1, 'q_1', 1, TRUE),
(2, 'Что такое SDLC и его этапы?', 'methodology', NULL, NULL, 'auto', 1, 'q_2', 2, TRUE),
(3, 'Основы Agile разработки', 'methodology', NULL, NULL, 'auto', 1, 'q_3', 3, TRUE),
(4, 'Что такое DevOps?', 'methodology', NULL, NULL, 'auto', 1, 'q_4', 4, TRUE),
(5, 'Принципы чистого кода', 'development', NULL, NULL, 'auto', 1, 'q_5', 5, TRUE),

-- Вопросы для аналитиков
(10, 'Как писать технические требования?', 'analysis', 'Специалист', 'Аналитик', 'docs_pack_bsa', 2, 'q_10', 10, TRUE),
(11, 'Методы сбора требований', 'analysis', 'Специалист', 'Аналитик', 'docs_pack_bsa', 2, 'q_11', 11, TRUE),
(12, 'UML диаграммы для аналитиков', 'analysis', 'Специалист', 'Аналитик', 'docs_pack_bsa', 2, 'q_12', 12, TRUE),

-- Вопросы для Java разработчиков
(20, 'Основы Java для начинающих', 'java', 'Специалист', 'Java', 'docs_pack_java', 2, 'q_20', 20, TRUE),
(21, 'Spring Framework основы', 'java', 'Специалист', 'Java', 'docs_pack_java', 2, 'q_21', 21, TRUE),
(22, 'Паттерны проектирования в Java', 'java', 'Специалист', 'Java', 'docs_pack_java', 2, 'q_22', 22, TRUE),

-- Вопросы для Python разработчиков
(30, 'Основы Python разработки', 'python', 'Специалист', 'Python', 'docs_pack_python', 2, 'q_30', 30, TRUE),
(31, 'Django или Flask - что выбрать?', 'python', 'Специалист', 'Python', 'docs_pack_python', 2, 'q_31', 31, TRUE),
(32, 'Тестирование в Python', 'python', 'Специалист', 'Python', 'docs_pack_python', 2, 'q_32', 32, TRUE),

-- Вопросы для веб-разработчиков
(40, 'HTML/CSS основы', 'web', 'Специалист', 'WEB', 'docs_pack_web', 2, 'q_40', 40, TRUE),
(41, 'JavaScript современные возможности', 'web', 'Специалист', 'WEB', 'docs_pack_web', 2, 'q_41', 41, TRUE),
(42, 'React или Vue - что выбрать?', 'web', 'Специалист', 'WEB', 'docs_pack_web', 2, 'q_42', 42, TRUE),

-- Вопросы для тестировщиков
(50, 'Основы тестирования ПО', 'testing', 'Специалист', 'Тестировщик', 'docs_pack_test', 2, 'q_50', 50, TRUE),
(51, 'Автоматизация тестирования', 'testing', 'Специалист', 'Тестировщик', 'docs_pack_test', 2, 'q_51', 51, TRUE),
(52, 'Виды тестирования', 'testing', 'Специалист', 'Тестировщик', 'docs_pack_test', 2, 'q_52', 52, TRUE),

-- Вопросы для лидов
(60, 'Управление командой разработки', 'leadership', 'Лид компетенции', NULL, 'auto', 3, 'q_60', 60, TRUE),
(61, 'Код-ревью: лучшие практики', 'leadership', 'Лид компетенции', NULL, 'auto', 3, 'q_61', 61, TRUE),
(62, 'Планирование спринтов', 'leadership', 'Лид компетенции', NULL, 'auto', 3, 'q_62', 62, TRUE),

-- Вопросы для PO/PM
(70, 'Основы Product Management', 'product', 'PO/PM', NULL, 'auto', 3, 'q_70', 70, TRUE),
(71, 'Работа с заказчиками', 'product', 'PO/PM', NULL, 'auto', 3, 'q_71', 71, TRUE),
(72, 'Приоритизация задач', 'product', 'PO/PM', NULL, 'auto', 3, 'q_72', 72, TRUE),

-- Специальные вопросы
(888, 'Свободный вопрос', 'general', NULL, NULL, 'auto', 1, 'q_888', 888, TRUE),
(777, 'Помощь с заданием', 'general', NULL, NULL, 'auto', 1, 'q_777', 777, TRUE);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_questions_role ON Questions(role);
CREATE INDEX IF NOT EXISTS idx_questions_specialization ON Questions(specialization);
CREATE INDEX IF NOT EXISTS idx_questions_category ON Questions(category);
CREATE INDEX IF NOT EXISTS idx_questions_active ON Questions(is_active);
CREATE INDEX IF NOT EXISTS idx_questions_order ON Questions(order_position);
CREATE INDEX IF NOT EXISTS idx_message_history_user ON Message_history(user_id);
CREATE INDEX IF NOT EXISTS idx_message_history_time ON Message_history(time); 