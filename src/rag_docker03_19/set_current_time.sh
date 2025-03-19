#!/bin/bash

# Функция для установки timedatectl
install_timedatectl() {
    echo "Установка timedatectl..."
    sudo apt-get update
    sudo apt-get install -y systemd
}

# Проверка наличия timedatectl
if ! command -v timedatectl &> /dev/null; then
    echo "timedatectl не установлен."
    install_timedatectl
else
    echo "timedatectl уже установлен."
fi

# Установить часовой пояс на Москву (UTC+3)
sudo timedatectl set-timezone Europe/Moscow

# Получить текущее время и добавить 3 часа
current_time=$(date -u +'%Y-%m-%d %H:%M:%S')
new_time=$(date -d "$current_time 3 hours" +'%Y-%m-%d %H:%M:%S')

# Установить новое время
sudo timedatectl set-ntp false
sudo timedatectl set-time "$new_time"

# Включить синхронизацию времени с NTP-сервером (если нужно)
sudo timedatectl set-ntp true

# Вывести новое время на экран
echo "Новое время в Москве: $new_time"

echo "Новое время установлено и синхронизация с NTP-сервером включена."
