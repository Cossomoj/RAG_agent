#!/bin/bash

VERSION="1.0.9"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/deployment.log"
DB_DIRECTORY="/home/user1/sqlite_data_rag"
DB_NAME="AI_agent.db"
DB_PATH="$DB_DIRECTORY/$DB_NAME"
LOCK_FILE="$DB_DIRECTORY/.lock"
YANDEX_DISK_PATH="/home/user1/Yandex.Disk"
REQUIRED_SPACE=1000000
BACKUP_RETENTION_DAYS=7
CRON_TMP=""
REPO_URL="git@github.com:Cossomoj/RAG_agent.git"
REPO_DIR="/tmp/RAG_agent"
BRANCH="develop"

log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

handle_error() {
    log "Ошибка: код $1"
    cleanup
    exit 1
}

cleanup() {
    log "Выполняем очистку..."
    [ -n "$CRON_TMP" ] && [ -f "$CRON_TMP" ] && rm -f "$CRON_TMP"
    [ -f "$LOCK_FILE" ] && rm -f "$LOCK_FILE"
    [ -f "${DB_PATH}.bak" ] && rm -f "${DB_PATH}.bak"
}

trap 'cleanup' EXIT
trap 'handle_error $?' ERR

check_disk_space() {
    local available_space=$(df /home/user1 | awk 'NR==2 {print $4}')
    
    if [ "$available_space" -lt "$REQUIRED_SPACE" ]; then
        log "Ошибка: Недостаточно места на диске"
        return 1
    fi
    return 0
}

check_docker_status() {
    if ! docker info >/dev/null 2>&1; then
        log "Docker демон не запущен"
        return 1
    fi
    
    if ! docker network ls >/dev/null 2>&1; then
        log "Проблемы с сетью Docker"
        return 1
    fi
    
    # Проверяем наличие необходимых портов
    if lsof -i :80 >/dev/null 2>&1 || lsof -i :443 >/dev/null 2>&1; then
        log "Порты 80 и/или 443 уже заняты. Проверьте, не запущен ли уже nginx"
        return 1
    fi
    
    return 0
}

save_state() {
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "${DB_PATH}.bak"
        log "Создана резервная копия базы данных"
    fi
}

restore_state() {
    if [ -f "${DB_PATH}.bak" ]; then
        mv "${DB_PATH}.bak" "$DB_PATH"
        log "Восстановлена резервная копия базы данных"
    fi
}

show_help() {
    cat << EOF
Скрипт развертывания v${VERSION}
Использование: $0 [опции]

Опции:
    -h, --help     Показать эту справку
    -v, --version  Показать версию
    --no-backup    Пропустить начальное резервное копирование
EOF
}

SKIP_BACKUP=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--version)
            echo "v${VERSION}"
            exit 0
            ;;
        --no-backup)
            SKIP_BACKUP=1
            shift
            ;;
        *)
            log "Неизвестный параметр: $1"
            show_help
            exit 1
            ;;
    esac
done

main() {
    log "Начинаем процесс развертывания..."

    if [ "$EUID" -ne 0 ]; then
        log "Для выполнения операций с Docker требуются права суперпользователя."
        exit 1
    fi

    for cmd in docker docker-compose sqlite3 git; do
        if ! command -v $cmd &> /dev/null; then
            log "Ошибка: $cmd не установлен."
            exit 1
        fi
    done

    check_disk_space || exit 1
    check_docker_status || exit 1

    # Настраиваем SSH для Git
    if [ ! -f "$HOME/.ssh/id_ed25519" ]; then
        log "Копируем SSH ключи..."
        mkdir -p "$HOME/.ssh"
        cp id_ed25519 "$HOME/.ssh/"
        cp id_ed25519.pub "$HOME/.ssh/"
        chmod 600 "$HOME/.ssh/id_ed25519"
        chmod 644 "$HOME/.ssh/id_ed25519.pub"
        
        # Добавляем GitHub в known_hosts
        ssh-keyscan github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null
    fi

    # Клонируем репозиторий
    log "Клонируем репозиторий..."
    rm -rf "$REPO_DIR"
    GIT_SSH_COMMAND="ssh -i $HOME/.ssh/id_ed25519" git clone -b "$BRANCH" "$REPO_URL" "$REPO_DIR" || {
        log "Ошибка при клонировании репозитория"
        exit 1
    }

    # Создаем рабочую директорию и переходим в нее
    WORK_DIR="/home/user1"
    cd "$WORK_DIR" || {
        log "Ошибка: не удалось перейти в директорию $WORK_DIR"
        exit 1
    }

    # Создаем необходимые директории
    log "Создаем необходимые директории..."
    for dir in "app_service" "monitor2" "nginx" "certbot" "sqlite_data_rag"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            chown user1:user1 "$dir"
            chmod 755 "$dir"
            log "Создана директория $dir"
        fi
    done

    # Создаем директории для RAG сервиса с правильной структурой
    mkdir -p "app_service/src/main_version"
    
    # Создаем файлы __init__.py для корректной работы импорта модулей Python
    log "Создаем файлы __init__.py для модулей Python..."
    touch "app_service/src/__init__.py"
    touch "app_service/src/main_version/__init__.py"
    chmod 644 "app_service/src/__init__.py"
    chmod 644 "app_service/src/main_version/__init__.py"
    
    # Копируем файлы RAG сервиса с сохранением структуры
    cp -r "$REPO_DIR/src/main_version/rag_service2/"* "app_service/"
    
    # Переносим ключевые файлы в нужную структуру директорий
    if [ -f "app_service/telegram_bot.py" ]; then
        cp "app_service/telegram_bot.py" "app_service/src/main_version/"
        log "Скопирован файл telegram_bot.py в app_service/src/main_version/"
    fi
    
    if [ -f "app_service/websocket_server.py" ]; then
        cp "app_service/websocket_server.py" "app_service/src/main_version/"
        log "Скопирован файл websocket_server.py в app_service/src/main_version/"
    fi
    
    # Копируем файлы админки в нужное место внутри app_service
    mkdir -p "app_service/admin"
    cp -r "$REPO_DIR/src/main_version/admin/"* "app_service/admin/"
    
    # Проверяем структуру директорий
    log "Проверяем структуру директорий..."
    if [ ! -d "app_service/admin" ]; then
        log "Ошибка: директория админки не создана"
        mkdir -p "app_service/admin"
    fi
    
    if [ ! -f "app_service/admin/app.py" ]; then
        log "Ошибка: файл app.py для админки не найден"
        if [ -f "$REPO_DIR/src/main_version/admin/app.py" ]; then
            cp "$REPO_DIR/src/main_version/admin/app.py" "app_service/admin/"
        else
            log "Критическая ошибка: исходный файл app.py для админки не найден"
            exit 1
        fi
    fi
    
    # Проверяем директорию src/main_version
    if [ ! -d "app_service/src/main_version" ]; then
        log "Ошибка: директория src/main_version не создана"
        mkdir -p "app_service/src/main_version"
    fi
    
    if [ ! -f "app_service/src/main_version/telegram_bot.py" ]; then
        log "Ошибка: файл telegram_bot.py не найден в правильной директории"
        if [ -f "app_service/telegram_bot.py" ]; then
            cp "app_service/telegram_bot.py" "app_service/src/main_version/"
            log "Перемещен файл telegram_bot.py в нужную директорию"
        else
            log "Критическая ошибка: файл telegram_bot.py не найден"
            exit 1
        fi
    fi
    
    if [ ! -f "app_service/src/main_version/websocket_server.py" ]; then
        log "Ошибка: файл websocket_server.py не найден в правильной директории"
        if [ -f "app_service/websocket_server.py" ]; then
            cp "app_service/websocket_server.py" "app_service/src/main_version/"
            log "Перемещен файл websocket_server.py в нужную директорию"
        else
            log "Критическая ошибка: файл websocket_server.py не найден"
            exit 1
        fi
    fi
    
    # Копируем файлы зависимостей для разных сервисов
    cp "$REPO_DIR/src/main_version/app_service/requirements_rag.txt" "app_service/"
    cp "$REPO_DIR/src/main_version/app_service/requirements_admin.txt" "app_service/"
    
    # Копируем конфигурацию supervisor и скрипт запуска
    cp "$REPO_DIR/src/main_version/app_service/supervisord.conf" "app_service/"
    cp "$REPO_DIR/src/main_version/app_service/start.sh" "app_service/"
    chmod +x "app_service/start.sh"
    
    # Копируем Dockerfile для app_service
    cp "$REPO_DIR/src/main_version/app_service/Dockerfile" "app_service/"
    
    # Копируем файлы мониторинга
    cp -r "$REPO_DIR/src/main_version/monitor2/"* "monitor2/"
    
    # Копируем файлы nginx и certbot
    cp -r "$REPO_DIR/src/main_version/nginx/"* "nginx/"
    cp -r "$REPO_DIR/src/main_version/certbot/"* "certbot/"
    
    # Копируем docker-compose.yml
    cp "$REPO_DIR/src/main_version/docker-compose.yml" .

    # Устанавливаем правильные права
    chown -R user1:user1 app_service monitor2 nginx certbot docker-compose.yml
    chmod -R 755 app_service monitor2 nginx certbot

    # Проверяем наличие необходимых файлов
    for file in ".env" "docker-compose.yml"; do
        if [ ! -f "$file" ]; then
            log "Ошибка: Не найден файл $file"
            exit 1
        fi
    done

    # Копируем конфигурационные файлы
    cp -f .env app_service/
    cp -f .env monitor2/

    # Создаем базу данных если её нет
    if [ ! -f "$DB_PATH" ]; then
        mkdir -p "$DB_DIRECTORY"
        chown user1:user1 "$DB_DIRECTORY"
        chmod 755 "$DB_DIRECTORY"
    fi

    save_state

    setup_database
    setup_nginx

    log "Запускаем Docker контейнеры..."
    if ! docker-compose up -d --build; then
        log "Ошибка при запуске Docker контейнеров"
        restore_state
        exit 1
    fi

    # Ждем, пока контейнеры запустятся
    log "Ожидаем запуска контейнеров..."
    sleep 30

    # Настраиваем Яндекс.Диск после запуска контейнеров
    setup_yandex_disk
    setup_backup
    setup_timezone

    if [ "$SKIP_BACKUP" -eq 0 ]; then
        perform_initial_backup
    fi

    # Очищаем временные файлы
    rm -rf "$REPO_DIR"

    log "Процесс развертывания успешно завершен"
    log "Для получения SSL-сертификата выполните:"
    log "docker-compose run --rm certbot certbot certonly --webroot --webroot-path=/var/www/certbot --email your-email@example.com --agree-tos --no-eff-email -d gigamentor.ru"
}

setup_database() {
    log "Настройка базы данных..."
    
    if [ ! -d "$DB_DIRECTORY" ]; then
        log "Создаем директорию базы данных: $DB_DIRECTORY"
        mkdir -p "$DB_DIRECTORY" || {
            log "Ошибка при создании директории базы данных. Пробуем через sudo..."
            sudo mkdir -p "$DB_DIRECTORY" || {
                log "Критическая ошибка: не удалось создать директорию для базы данных"
                return 1
            }
        }
        
        chown user1:user1 "$DB_DIRECTORY" 2>/dev/null || sudo chown user1:user1 "$DB_DIRECTORY" 2>/dev/null
        chmod 755 "$DB_DIRECTORY" 2>/dev/null || sudo chmod 755 "$DB_DIRECTORY" 2>/dev/null
    fi

    if [ -d "$DB_PATH" ]; then
        log "ВНИМАНИЕ: Обнаружена директория вместо файла БД. Удаляем её..."
        rmdir "$DB_PATH" 2>/dev/null || sudo rmdir "$DB_PATH" 2>/dev/null || {
            log "Не удалось удалить директорию. Пробуем принудительное удаление..."
            rm -rf "$DB_PATH" 2>/dev/null || sudo rm -rf "$DB_PATH" 2>/dev/null || {
                log "Невозможно удалить директорию $DB_PATH. Меняем имя файла БД."
                DB_NAME="AI_agent_new.db"
                DB_PATH="$DB_DIRECTORY/$DB_NAME"
                log "Новый путь к БД: $DB_PATH"
            }
        }
    fi

    if [ ! -f "$DB_PATH" ]; then
        log "Файл базы данных не найден. Создаем новую базу данных..."
        
        touch "$DB_PATH" 2>/dev/null || sudo touch "$DB_PATH" 2>/dev/null || {
            log "Ошибка при создании файла базы данных"
            return 1
        }
        
        chown user1:user1 "$DB_PATH" 2>/dev/null || sudo chown user1:user1 "$DB_PATH" 2>/dev/null
        chmod 644 "$DB_PATH" 2>/dev/null || sudo chmod 644 "$DB_PATH" 2>/dev/null
        
        log "Инициализация базы данных..."
        
        sqlite3 "$DB_PATH" <<EOF
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY,
    username TEXT DEFAULT NULL,
    user_fullname TEXT DEFAULT NULL,
    reminder BOOL DEFAULT TRUE,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Reminder (
    id_rem INTEGER PRIMARY KEY AUTOINCREMENT, 
    user_id INTEGER,
    reminder_text TEXT DEFAULT NULL,
    reminder_time TEXT DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS Message_history (
    user_id INTEGER, 
    role TEXT CHECK(role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
EOF
    fi
}

setup_nginx() {
    log "Настройка Nginx..."
    
    # Создаем директории для SSL сертификатов
    mkdir -p certbot/conf
    mkdir -p certbot/www
}

setup_yandex_disk() {
    log "Настройка Яндекс.Диска..."

    # Создаем виртуальное окружение для Яндекс.Диска
    YANDEX_VENV="/home/user1/yandex_venv"
    if [ ! -d "$YANDEX_VENV" ]; then
        log "Создаем виртуальное окружение для Яндекс.Диска..."
        apt-get update
        apt-get install -y python3-venv
        python3 -m venv "$YANDEX_VENV"
        chown -R user1:user1 "$YANDEX_VENV"
        chmod -R 755 "$YANDEX_VENV"
    fi

    if ! command -v yandex-disk &> /dev/null; then
        log "Установка Яндекс.Диска..."
        ARCH=$(uname -m)
        YANDEX_DISK_URL="https://repo.yandex.ru/yandex-disk/yandex-disk_latest_amd64.deb"
        [ "$ARCH" != "x86_64" ] && YANDEX_DISK_URL="https://repo.yandex.ru/yandex-disk/yandex-disk_latest_i386.deb"

        wget -O yandex-disk.deb "$YANDEX_DISK_URL"
        apt-get update
        apt-get install -y apt-utils
        DEBIAN_FRONTEND=noninteractive dpkg -i yandex-disk.deb || apt-get -f install -y
        rm -f yandex-disk.deb
    fi

    if id "user1" &>/dev/null; then
        # Останавливаем предыдущую версию, если она запущена
        su - user1 -c "yandex-disk stop 2>/dev/null || true"
        pkill -9 -u user1 yandex-disk 2>/dev/null || true
        sleep 3
        
        # Очищаем предыдущие конфигурации
        rm -rf /home/user1/.config/yandex-disk
        rm -f "/home/user1/yes"
        
        # Создаем нужные директории
        mkdir -p "$YANDEX_DISK_PATH"
        chown user1:user1 "$YANDEX_DISK_PATH"

        mkdir -p /home/user1/.config/yandex-disk
        cat > /home/user1/.config/yandex-disk/config.cfg << EOF
proxy="no"
ask_user_pass="no"
dir="$YANDEX_DISK_PATH"
auth="yes"
EOF
        chown -R user1:user1 /home/user1/.config/yandex-disk

        # Файл с автоматическими ответами для настройки
        ANSWERS_FILE="/tmp/yandex_answers.txt"
        echo -e "n\n\ny" > "$ANSWERS_FILE"
        chown user1:user1 "$ANSWERS_FILE"
        chmod 644 "$ANSWERS_FILE"

        # Активируем виртуальное окружение для команд
        ACTIVATE_VENV="source $YANDEX_VENV/bin/activate && "

        if [ -f "yandex_token.txt" ]; then
            TOKEN=$(cat yandex_token.txt)
            log "Используем предварительно сохраненный токен"
            mkdir -p /home/user1/.config/yandex-disk
            echo "$TOKEN" > /home/user1/.config/yandex-disk/token
            chown user1:user1 /home/user1/.config/yandex-disk/token
            
            log "Запускаем Яндекс.Диск с предварительно сохраненным токеном..."
            su - user1 -c "${ACTIVATE_VENV}yandex-disk start"
        else
            log "Запрос кода авторизации с ya.ru/device (потребуется ввод только этого кода)..."
            
            su - user1 -c "${ACTIVATE_VENV}yandex-disk setup < $ANSWERS_FILE"
            
            if [ -f "/home/user1/.config/yandex-disk/token" ]; then
                cp /home/user1/.config/yandex-disk/token yandex_token.txt
                log "Токен сохранен для будущего использования"
            elif [ -f "/home/user1/yes" ]; then
                cp "/home/user1/yes" yandex_token.txt
                log "Токен сохранен из нестандартного расположения"
            fi
        fi
        
        # Удаляем временный файл
        rm -f "$ANSWERS_FILE"
        
        # Проверяем статус
        sleep 10
        status=$(su - user1 -c "${ACTIVATE_VENV}yandex-disk status")
        log "Статус Яндекс.Диска: $status"
        
        if echo "$status" | grep -q -E "синхронизация|работает|sync|idle"; then
            log "Яндекс.Диск успешно настроен и запущен"
            rm -f "/home/user1/yes"
            return 0
        else
            log "Проблема с запуском Яндекс.Диска. Статус: $status"
            
            log "Содержимое каталога конфигурации:"
            ls -la /home/user1/.config/yandex-disk/
            
            if [ -f "/home/user1/.config/yandex-disk/token" ]; then
                log "Файл токена существует, размер: $(stat -c%s /home/user1/.config/yandex-disk/token) байт"
            else
                log "Файл токена не найден!"
            fi
            
            # Попытка перезапуска
            log "Пробуем перезапустить Яндекс.Диск..."
            su - user1 -c "${ACTIVATE_VENV}yandex-disk start"
            return 0
        fi
    else
        log "Ошибка: Пользователь user1 не существует"
        return 1
    fi
}

setup_backup() {
    log "Настройка резервного копирования..."
    
    CRON_TMP=$(mktemp)
    if [ ! -f "$CRON_TMP" ]; then
        log "Ошибка: Не удалось создать временный файл для cron"
        return 1
    fi
    
    # Подготавливаем команды для активации виртуального окружения
    VENV_PATH="/home/user1/yandex_venv"
    
    cat > "$CRON_TMP" << EOF
*/5 * * * * export DB_PATH="$DB_PATH"; export LOCK_FILE="$LOCK_FILE"; export PATH="/home/user1/yandex_venv/bin:\$PATH"; if [ -f "\$DB_PATH" ]; then touch "\$LOCK_FILE"; TIMESTAMP=\$(date +"%Y-%m-%d_%H-%M"); cp "\$DB_PATH" "$YANDEX_DISK_PATH/AI_agent_\$TIMESTAMP.db" && source "$VENV_PATH/bin/activate" && yandex-disk sync; rm -f "\$LOCK_FILE"; find "$YANDEX_DISK_PATH" -name "AI_agent_*.db" -type f -mmin +20 -delete; fi > /dev/null 2>&1

0 0 * * * export DB_PATH="$DB_PATH"; export LOCK_FILE="$LOCK_FILE"; export PATH="/home/user1/yandex_venv/bin:\$PATH"; if [ -f "\$DB_PATH" ]; then touch "\$LOCK_FILE"; TIMESTAMP=\$(date +"%Y-%m-%d"); cp "\$DB_PATH" "$YANDEX_DISK_PATH/AI_agent_\$TIMESTAMP.db" && source "$VENV_PATH/bin/activate" && yandex-disk sync; rm -f "\$LOCK_FILE"; find "$YANDEX_DISK_PATH" -name "AI_agent_*.db" -type f -mtime +$BACKUP_RETENTION_DAYS -delete; fi > /dev/null 2>&1
EOF

    # Устанавливаем cron для пользователя user1
    if ! crontab -u user1 "$CRON_TMP"; then
        log "Ошибка при установке cron-заданий для пользователя user1"
        log "Пробуем установить cron для текущего пользователя..."
        if ! crontab "$CRON_TMP"; then
            log "Ошибка при установке cron-заданий"
            rm -f "$CRON_TMP"
            return 1
        fi
    fi
    
    rm -f "$CRON_TMP"
    CRON_TMP=""
    log "Cron-задания установлены успешно"
}

setup_timezone() {
    log "Настройка времени..."
    
    if ! command -v timedatectl &> /dev/null; then
        DEBIAN_FRONTEND=noninteractive apt-get update
        DEBIAN_FRONTEND=noninteractive apt-get install -y systemd
    fi

    timedatectl set-timezone Europe/Moscow
    log "Установлен часовой пояс: Europe/Moscow"
    
    systemctl stop systemd-timesyncd
    sleep 2
    date -s "$(date +"%Y-%m-%d %H:%M:%S")"
    systemctl start systemd-timesyncd
    timedatectl set-ntp true
    
    log "Установлено время: $(date)"
}

perform_initial_backup() {
    log "Выполняем начальное резервное копирование..."
    
    if [ -f "$DB_PATH" ]; then
        local backup_dir="$DB_DIRECTORY/backups"
        mkdir -p "$backup_dir"
        
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local backup_file="$backup_dir/AI_agent_$timestamp.db"
        
        if cp "$DB_PATH" "$backup_file"; then
            log "Создана резервная копия: $backup_file"
            
            # Удаляем старые резервные копии
            find "$backup_dir" -name "AI_agent_*.db" -type f -mtime +$BACKUP_RETENTION_DAYS -delete
        else
            log "Ошибка при создании резервной копии"
        fi
    else
        log "Файл базы данных не найден, пропускаем резервное копирование"
    fi
}

main "$@"