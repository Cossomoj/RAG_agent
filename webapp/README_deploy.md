# Инструкция по развертыванию мини-приложения Telegram

## Требования

- Ubuntu/Debian сервер
- Nginx
- Python 3.8+
- SSL сертификат (для продакшена)
- Домен, указывающий на ваш сервер

## Установка

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y nginx python3 python3-pip python3-venv git

# Создание пользователя для приложения (опционально)
sudo useradd -m -s /bin/bash webapp
```

### 2. Размещение файлов

```bash
# Копирование файлов мини-приложения в /var/www/html
sudo mkdir -p /var/www/html/webapp
sudo cp -r webapp/* /var/www/html/webapp/

# Установка правильных прав доступа
sudo chown -R www-data:www-data /var/www/html/webapp
sudo chmod -R 755 /var/www/html/webapp
```

### 3. Настройка API сервера

```bash
# Переход в директорию API
cd /var/www/html/webapp/api

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание systemd сервиса для API
sudo tee /etc/systemd/system/ragapp-api.service > /dev/null <<EOF
[Unit]
Description=RAG App API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/html/webapp/api
Environment=PATH=/var/www/html/webapp/api/venv/bin
ExecStart=/var/www/html/webapp/api/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Запуск и включение автозапуска сервиса
sudo systemctl daemon-reload
sudo systemctl enable ragapp-api
sudo systemctl start ragapp-api

# Проверка статуса
sudo systemctl status ragapp-api
```

### 4. Настройка Nginx

```bash
# Создание конфигурации сайта
sudo tee /etc/nginx/sites-available/ragapp > /dev/null <<EOF
server {
    listen 80;
    server_name restocorp.ru;
    
    location / {
        root /var/www/html/webapp;
        index index.html;
        try_files \$uri \$uri/ /index.html;
        
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
            return 204;
        }
    }
    
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        root /var/www/html/webapp;
    }
}
EOF

# Активация сайта
sudo ln -s /etc/nginx/sites-available/ragapp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Удаление дефолтного сайта

# Проверка конфигурации и перезагрузка
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Настройка SSL (обязательно для Telegram Web App)

```bash
# Установка Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot --nginx -d restocorp.ru

# Проверка автообновления
sudo certbot renew --dry-run
```

### 6. Настройка Telegram бота

1. Отредактируйте файл `src/main_version/telegram_bot.py`
2. Замените `https://restocorp.ru` на ваш реальный домен в строке:
   ```python
   types.InlineKeyboardButton(text="🚀 Мини-приложение", web_app=types.WebAppInfo(url="https://restocorp.ru"))
   ```

### 7. Настройка RAG сервиса

Убедитесь, что ваш RAG WebSocket сервер запущен на порту 8000:

```bash
# Переход в директорию основного проекта
cd /var/www/html/src/main_version

# Запуск в фоне (используйте screen или systemd для продакшена)
python3 telegram_bot.py &
```

## Проверка работы

1. Откройте ваш домен в браузере - должно загрузиться мини-приложение
2. Проверьте API: `curl https://restocorp.ru/api/health`
3. В Telegram боте нажмите кнопку "🚀 Мини-приложение"

## Логи и диагностика

```bash
# Логи API сервера
sudo journalctl -u ragapp-api -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Проверка статуса сервисов
sudo systemctl status ragapp-api
sudo systemctl status nginx
```

## Обновление

```bash
# Остановка сервисов
sudo systemctl stop ragapp-api

# Обновление файлов
sudo cp -r webapp/* /var/www/html/webapp/

# Установка новых зависимостей (если есть)
cd /var/www/html/webapp/api
source venv/bin/activate
pip install -r requirements.txt

# Перезапуск сервисов
sudo systemctl start ragapp-api
sudo systemctl reload nginx
```

## Безопасность

1. Настройте фаервол:
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 'Nginx Full'
   sudo ufw enable
   ```

2. Регулярно обновляйте систему
3. Мониторьте логи на подозрительную активность
4. Используйте HTTPS для всех соединений

## Поддержка

Если возникли проблемы:
1. Проверьте логи сервисов
2. Убедитесь, что все сервисы запущены
3. Проверьте правильность конфигурации
4. Убедитесь, что домен правильно настроен

## Telegram Web App Requirements

1. **HTTPS обязателен** - Telegram Web App работает только по HTTPS
2. **Корректный домен** - должен быть зарегистрирован и доступен
3. **Правильные заголовки** - настроены в конфигурации Nginx
4. **Валидный SSL** - сертификат должен быть действующим 