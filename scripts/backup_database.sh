#!/bin/bash

# Скрипт резервного копирования базы данных RAG Agent
# Использует настройки из config.yaml

echo "📦 Создание резервной копии базы данных RAG Agent..."

# Настройки
DB_PATH="src/main_version/AI_agent.db"
BACKUP_DIR="backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="AI_agent_backup_${DATE}.db"
MAX_BACKUPS=7

# Создаем директорию для бэкапов если её нет
mkdir -p "$BACKUP_DIR"

# Проверяем существование базы данных
if [ ! -f "$DB_PATH" ]; then
    echo "❌ База данных не найдена: $DB_PATH"
    exit 1
fi

# Создаем резервную копию
echo "💾 Копирование базы данных..."
cp "$DB_PATH" "$BACKUP_DIR/$BACKUP_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Резервная копия создана: $BACKUP_DIR/$BACKUP_NAME"
    
    # Получаем размер файла
    DB_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
    echo "📊 Размер резервной копии: $DB_SIZE"
else
    echo "❌ Ошибка создания резервной копии"
    exit 1
fi

# Удаляем старые бэкапы (оставляем только последние MAX_BACKUPS)
echo "🧹 Очистка старых резервных копий..."
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/AI_agent_backup_*.db 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    TO_DELETE=$((BACKUP_COUNT - MAX_BACKUPS))
    ls -1t "$BACKUP_DIR"/AI_agent_backup_*.db | tail -n "$TO_DELETE" | xargs rm -f
    echo "🗑️  Удалено старых копий: $TO_DELETE"
fi

# Показываем все существующие бэкапы
echo ""
echo "📋 Все резервные копии:"
ls -lah "$BACKUP_DIR"/AI_agent_backup_*.db 2>/dev/null | awk '{print "   " $9 " (" $5 ", " $6 " " $7 ")"}'

echo ""
echo "🎉 Резервное копирование завершено успешно!" 