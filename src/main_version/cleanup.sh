#!/bin/bash

# Полностью автономный скрипт для остановки и очистки Docker-окружения

echo "Начинаем процесс остановки и очистки..."

# Проверка наличия docker и docker-compose
if ! command -v docker &> /dev/null; then
    echo "Ошибка: Docker не установлен."
    echo "Пожалуйста, установите Docker перед запуском этого скрипта."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Ошибка: Docker Compose не установлен."
    echo "Пожалуйста, установите Docker Compose перед запуском этого скрипта."
    exit 1
fi

# Проверка прав суперпользователя
if [ "$EUID" -ne 0 ]; then
    echo "Для выполнения операций с Docker требуются права суперпользователя."
    echo "Пожалуйста, запустите скрипт с помощью sudo."
    exit 1
fi

# ===============================================================
# Создание финальной резервной копии базы данных
# ===============================================================
echo "Создаем финальную резервную копию базы данных..."

# Определение пути к папке Яндекс.Диска
YANDEX_DISK_PATH="/home/user1/Yandex.Disk"
echo "Используем путь к Яндекс.Диску: $YANDEX_DISK_PATH"

# Путь к папке, где хранится база данных
DB_DIRECTORY="/home/user1/sqlite_data_rag"
DB_NAME="AI_agent.db"
DB_PATH="$DB_DIRECTORY/$DB_NAME"

# Файл блокировки
LOCK_FILE="$DB_DIRECTORY/.lock"

# Проверка существования базы данных
if [ -f "$DB_PATH" ]; then
    # Создание блокировки
    touch "$LOCK_FILE"

    # Копирование базы данных с добавлением даты и времени к имени
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
    
    # Создаем локальную копию (независимо от наличия Яндекс.Диска)
    LOCAL_BACKUP="./AI_agent_FINAL_$TIMESTAMP.db"
    cp "$DB_PATH" "$LOCAL_BACKUP"
    echo "Локальная резервная копия создана: $LOCAL_BACKUP"
    
    # Проверка наличия папки Yandex.Disk и создание копии там, если папка существует
    if [ -d "$YANDEX_DISK_PATH" ]; then
        BACKUP_FILE="$YANDEX_DISK_PATH/AI_agent_FINAL_$TIMESTAMP.db"
        cp "$DB_PATH" "$BACKUP_FILE"
        chown user1:user1 "$BACKUP_FILE"
        echo "Финальная резервная копия в Яндекс.Диске создана: $BACKUP_FILE"
    else
        echo "Папка Yandex.Disk не найдена. Резервная копия сохранена только локально."
    fi

    # Удаление блокировки
    rm -f "$LOCK_FILE"
else
    echo "База данных не найдена по пути $DB_PATH. Резервное копирование пропущено."
fi

# ===============================================================
# Очистка задач резервного копирования
# ===============================================================
# Очистка всех cron-задач
echo "Очищаем cron-задачи..."
crontab -r
echo "Все cron-задачи удалены."

# ===============================================================
# Остановка Яндекс.Диска
# ===============================================================
echo "Проверяем статус Яндекс.Диска..."

if command -v yandex-disk &> /dev/null; then
    # Проверка, запущен ли Яндекс.Диск
    DISK_STATUS=$(su - user1 -c "yandex-disk status" | grep -o "запущен\|started")
    
    if [ ! -z "$DISK_STATUS" ]; then
        echo "Останавливаем Яндекс.Диск..."
        su - user1 -c "yandex-disk stop"
        echo "Яндекс.Диск остановлен."
    else
        echo "Яндекс.Диск не запущен."
    fi
else
    echo "Яндекс.Диск не установлен."
fi

# ===============================================================
# Остановка и очистка Docker
# ===============================================================
# Останавливаем запущенные контейнеры
echo "Останавливаем запущенные контейнеры..."
docker-compose down

# Ожидание завершения процессов Docker
echo "Ожидаем завершения процессов Docker..."
sleep 5

# Очистка неиспользуемых образов, контейнеров, сетей и томов
echo "Выполняем полную очистку системы Docker..."
docker system prune -a -f

# Очистка директорий и файлов
echo "Очищаем директории и файлы..."
rm -rf monitor2 rag_service2 nginx certbot admin sqlite_data_rag
rm -f yandex_token.txt docker-compose.yml

# ===============================================================
# Удаление Яндекс.Диска (по желанию)
# ===============================================================
echo "Хотите полностью удалить Яндекс.Диск? (y/n)"
read -r answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    echo "Удаляем Яндекс.Диск из системы..."
    # Останавливаем процессы
    pkill -9 -u user1 yandex-disk 2>/dev/null
    sleep 2
    
    # Удаляем конфигурационные файлы
    rm -rf /home/user1/.config/yandex-disk
    
    # Удаляем пакет
    apt-get remove -y yandex-disk
    apt-get autoremove -y
    
    echo "Яндекс.Диск удален из системы."
    
    echo "Хотите также удалить содержимое папки Яндекс.Диска? (y/n)"
    read -r answer2
    if [[ "$answer2" =~ ^[Yy]$ ]]; then
        rm -rf "$YANDEX_DISK_PATH"
        echo "Папка Яндекс.Диска и её содержимое удалены."
    fi
else
    echo "Пропускаем удаление Яндекс.Диска."
fi

# ===============================================================
# Завершение процесса
# ===============================================================
echo "Процесс остановки и очистки завершен."
echo "Время: $(date)"
echo "Все контейнеры остановлены, неиспользуемые образы, контейнеры, сети и тома удалены."

REPO_URL="git@github.com:Cossomoj/RAG_agent.git"
REPO_DIR="/tmp/RAG_agent"
BRANCH="develop"

# Настраиваем SSH для Git
if [ ! -f "$HOME/.ssh/id_ed25519" ]; then
    echo "Копируем SSH ключи..."
    mkdir -p "$HOME/.ssh"
    cp id_ed25519 "$HOME/.ssh/"
    cp id_ed25519.pub "$HOME/.ssh/"
    chmod 600 "$HOME/.ssh/id_ed25519"
    chmod 644 "$HOME/.ssh/id_ed25519.pub"
    
    # Добавляем GitHub в known_hosts
    ssh-keyscan github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null
fi

# Клонируем репозиторий
echo "Клонируем репозиторий..."
rm -rf "$REPO_DIR"
GIT_SSH_COMMAND="ssh -i $HOME/.ssh/id_ed25519" git clone -b "$BRANCH" "$REPO_URL" "$REPO_DIR" || {
    echo "Ошибка при клонировании репозитория"
    exit 1
}

# Копируем необходимые файлы
echo "Копируем файлы из репозитория..."
cp "$REPO_DIR/src/main_version/docker-compose.yml" .

# Останавливаем и удаляем контейнеры
docker-compose down

# Удаляем все неиспользуемые ресурсы
docker system prune -af

# Удаляем все тома
docker volume prune -f

# Удаляем все сети
docker network prune -f

# Очищаем временные файлы
rm -rf "$REPO_DIR"
rm -f docker-compose.yml

echo "Очистка завершена"