# 🚀 Руководство по переносу RAG Agent на VPS

## 📋 Обзор изменений

При переносе на VPS необходимо изменить следующие категории настроек:
- 🌐 **Localhost URL-ы** на IP вашего сервера
- 📁 **Пути к файлам** на серверные пути
- 🔌 **Порты и хосты** для внешнего доступа
- 🔒 **Безопасность и CORS** настройки

---

## 🎯 КРИТИЧЕСКИЕ файлы для изменения

### 1. 📄 `config.yaml` - Основная конфигурация

**Что менять:**
```yaml
# Сетевые настройки
network:
  rag_service:
    host: "0.0.0.0"           # ✅ Уже правильно
    port: 8000
    websocket_url: "ws://YOUR_SERVER_IP:8000/ws"  # 🔧 ИЗМЕНИТЬ

  webapp_api:
    host: "0.0.0.0"           # ✅ Уже правильно  
    port: 5001
    
  admin_panel:
    host: "0.0.0.0"           # ✅ Уже правильно
    port: 8002

# Пути (если размещаете не в /var/www/html/)
paths:
  database: "/var/www/html/src/main_version/AI_agent.db"      # 🔧 ИЗМЕНИТЬ
  rag_path: "/var/www/html/src/main_version"                # 🔧 ИЗМЕНИТЬ
  docs_dir: "/var/www/html/src/main_version/docs"           # 🔧 ИЗМЕНИТЬ
  txt_docs_dir: "/var/www/html/src/main_version/txt_docs"   # 🔧 ИЗМЕНИТЬ

# CORS для вашего домена
security:
  allowed_origins: ["http://YOUR_DOMAIN", "https://YOUR_DOMAIN"]  # 🔧 ИЗМЕНИТЬ

# Health check endpoints
health_check:
  endpoints:
    - name: "rag_service"
      url: "http://YOUR_SERVER_IP:8000/docs"       # 🔧 ИЗМЕНИТЬ
    - name: "webapp_api" 
      url: "http://YOUR_SERVER_IP:5001/api/health" # 🔧 ИЗМЕНИТЬ
    - name: "admin_panel"
      url: "http://YOUR_SERVER_IP:8002/"           # 🔧 ИЗМЕНИТЬ
```

### 2. 🤖 `src/main_version/telegram_bot.py`

**Строка 34:**
```python
# БЫЛО:
WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"

# ЗАМЕНИТЬ НА:
WEBSOCKET_URL = "ws://YOUR_SERVER_IP:8000/ws"
```

### 3. 🌐 `webapp/nginx.conf`

**Строка 20 (API proxy):**
```nginx
# БЫЛО:
proxy_pass http://127.0.0.1:5000;

# ЗАМЕНИТЬ НА:
proxy_pass http://127.0.0.1:5001;  # Правильный порт
```

**Строка 1-2 (домен):**
```nginx
# ЗАМЕНИТЬ restocorp.ru НА ВАШ ДОМЕН
server_name YOUR_DOMAIN;
```

**SSL сертификаты (строки 53-54):**
```nginx
ssl_certificate /path/to/your/certificate.crt;         # 🔧 ПУТЬ К СЕРТИФИКАТУ
ssl_certificate_key /path/to/your/private.key;         # 🔧 ПУТЬ К КЛЮЧУ
```

### 4. 🎨 `webapp/app.js` (если есть WebSocket соединения)

**При наличии WebSocket подключений в JavaScript:**
```javascript
// БЫЛО:
const ws = new WebSocket('ws://127.0.0.1:8000/ws_suggest');

// ЗАМЕНИТЬ НА:
const ws = new WebSocket('ws://YOUR_SERVER_IP:8000/ws_suggest');
```

### 5. 🔧 `webapp/api/app.py`

**Строка 40:**
```python
# Проверить что путь правильный для вашего VPS
fallback_path = '/var/www/html/src/main_version'  # 🔧 ПУТЬ НА VPS
```

**Строка 56:**
```python
# Если база данных в другом месте
DATABASE_URL = os.getenv("DATABASE_URL", "/var/www/html/src/main_version/AI_agent.db")
```

---

## 🛠️ Скрипты запуска (опционально)

### 6. 📝 Все `run_*.sh` скрипты

**Если не используете config.yaml, то в скриптах заменить:**

`run_telegram_bot.sh` строки 30-31:
```bash
# БЫЛО:
if ! curl -s http://localhost:8000/docs > /dev/null; then
echo "⚠️  Внимание: RAG сервис (localhost:8000) недоступен."

# ЗАМЕНИТЬ НА:
if ! curl -s http://YOUR_SERVER_IP:8000/docs > /dev/null; then
echo "⚠️  Внимание: RAG сервис (YOUR_SERVER_IP:8000) недоступен."
```

### 7. 📊 `scripts/health_check.sh`

**Строки 104-107:**
```bash
# ЗАМЕНИТЬ localhost НА YOUR_SERVER_IP:
check_http "RAG API" "http://YOUR_SERVER_IP:8000/docs"
check_http "Web API Health" "http://YOUR_SERVER_IP:5001/api/health"  
check_http "Web App" "http://YOUR_SERVER_IP:5001/"
check_http "Admin Panel" "http://YOUR_SERVER_IP:8002/"
```

---

## 🔒 Безопасность для VPS

### 8. 🛡️ Firewall настройки

```bash
# Открыть необходимые порты
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw allow 8000    # RAG API
sudo ufw allow 5001    # Web API
sudo ufw allow 8002    # Admin (рекомендуется ограничить по IP)

# Для админки только с вашего IP:
sudo ufw allow from YOUR_IP to any port 8002
```

### 9. 📁 Права доступа

```bash
# Установить правильные права
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/
sudo chmod 644 /var/www/html/src/main_version/AI_agent.db
```

---

## 📝 Переменные окружения

### 10. 🌍 Создать `.env` файл

```bash
# /var/www/html/.env
DATABASE_URL=/var/www/html/src/main_version/AI_agent.db
RAG_PATH=/var/www/html/src/main_version
WEBSOCKET_URL=ws://YOUR_SERVER_IP:8000/ws
SERVER_HOST=0.0.0.0
DOMAIN=YOUR_DOMAIN
```

---

## 🚀 Инструкции по деплою

### Шаг 1: Подготовка сервера
```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить зависимости
sudo apt install python3 python3-pip python3-venv nginx git -y
```

### Шаг 2: Клонирование проекта
```bash
cd /var/www/html/
sudo git clone https://github.com/YOUR_REPO/RAG_agent.git
sudo chown -R www-data:www-data RAG_agent/
cd RAG_agent/
```

### Шаг 3: Изменение конфигурации
```bash
# Изменить config.yaml
sudo nano config.yaml

# Изменить telegram_bot.py  
sudo nano src/main_version/telegram_bot.py

# Обновить nginx конфигурацию
sudo cp webapp/nginx.conf /etc/nginx/sites-available/rag_agent
sudo ln -s /etc/nginx/sites-available/rag_agent /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
```

### Шаг 4: Установка зависимостей
```bash
# Запустить скрипт установки
chmod +x install_dependencies.sh
sudo ./install_dependencies.sh
```

### Шаг 5: Запуск сервисов
```bash
# Запустить все сервисы
chmod +x run_all_enhanced.sh
./run_all_enhanced.sh
```

### Шаг 6: Настройка systemd (опционально)

Создать сервисы для автозапуска:

```bash
# Создать сервис для RAG
sudo nano /etc/systemd/system/rag-agent.service
```

```ini
[Unit]
Description=RAG Agent Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/html/RAG_agent/src/main_version
ExecStart=/var/www/html/RAG_agent/src/main_version/venv/bin/python rag_service_context7_optimized.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## ✅ Проверка работоспособности

После деплоя проверить:

1. **RAG API**: `http://YOUR_SERVER_IP:8000/docs`
2. **Web App**: `http://YOUR_SERVER_IP:5001` 
3. **Admin Panel**: `http://YOUR_SERVER_IP:8002`
4. **Health Check**: `./scripts/health_check.sh`

---

## 🔧 Замените YOUR_SERVER_IP / YOUR_DOMAIN на:

- **YOUR_SERVER_IP**: IP-адрес вашего VPS (например: `45.123.456.789`)
- **YOUR_DOMAIN**: Ваш домен (например: `example.com`)

**Примеры замен:**
- `ws://127.0.0.1:8000/ws` → `ws://45.123.456.789:8000/ws`
- `http://localhost:8000` → `http://45.123.456.789:8000`
- `restocorp.ru` → `yourdomain.com`

---

## 🚨 Важные моменты

1. **Telegram бот**: Обновите webhook URL в BotFather на ваш домен
2. **SSL**: Настройте Let's Encrypt для HTTPS
3. **Бэкапы**: Настройте регулярные бэкапы базы данных
4. **Мониторинг**: Используйте скрипт health_check.sh в cron
5. **Логи**: Проверяйте логи в `/var/log/nginx/` и `logs/`

💡 **Совет**: Сначала протестируйте на тестовом поддомене, затем переносите на основной домен. 