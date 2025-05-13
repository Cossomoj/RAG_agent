#!/bin/bash

# Путь к папке, где хранится база данных
DB_DIRECTORY="sqlite_data_rag"
DB_NAME="AI_agent.db"
DB_PATH="$DB_DIRECTORY/$DB_NAME"

# Путь к папке Yandex.Disk
YANDEX_DISK_PATH="Yandex.Disk"

# Файл блокировки
LOCK_FILE="$DB_DIRECTORY/.lock"

# Функция для резервного копирования базы данных
backup_database() {
  # Создание блокировки
  touch "$LOCK_FILE"

  # Копирование базы данных с добавлением времени к имени
  TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
  BACKUP_FILE="$YANDEX_DISK_PATH/AI_agent_$TIMESTAMP.db"
  cp "$DB_PATH" "$BACKUP_FILE"

  # Удаление блокировки
  rm "$LOCK_FILE"

  # Удаление старых резервных копий (оставляя не более 50 штук)
  ls -t "$YANDEX_DISK_PATH"/AI_agent_*.db | tail -n +51 | xargs rm -f

  echo "Резервное копирование базы данных завершено. Старые резервные копии удалены."
}

# Функция для настройки cron-задач
setup_cron_jobs() {
  # Путь к текущему скрипту
  SCRIPT_PATH=$(realpath "$0")

  # Добавление cron-задачи для резервного копирования каждый час
  (crontab -l ; echo "0 * * * * $SCRIPT_PATH") | crontab -

  echo "Cron-задачи успешно настроены."
}

# Делаем текущий скрипт исполняемым
chmod +x "$0"

# Настройка cron-задач
setup_cron_jobs

# Резервное копирование базы данных
backup_database

echo "Все скрипты завершили выполнение."