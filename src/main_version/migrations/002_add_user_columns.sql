-- Добавление новых колонок в таблицу Users
ALTER TABLE Users ADD COLUMN Role TEXT;
ALTER TABLE Users ADD COLUMN Specialization TEXT;
ALTER TABLE Users ADD COLUMN is_onboarding BOOLEAN DEFAULT FALSE NOT NULL;

-- Добавление записи о применении миграции
INSERT INTO applied_migrations (migration_name)
VALUES ('002_add_user_columns.sql'); 