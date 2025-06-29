# 🚀 Локальный запуск RAG Agent

Этот проект представляет собой многокомпонентную систему с RAG (Retrieval-Augmented Generation) агентом, включающую:

- **RAG сервис** (FastAPI + WebSocket) - основной AI движок
- **Telegram бот** - интерфейс через мессенджер  
- **Web API** (Flask) - REST API для веб-интерфейса
- **Admin панель** (Flask) - административный интерфейс

## 📋 Предварительные требования

### Системные требования:
- **Python 3.8+**
- **pip** (менеджер пакетов Python)
- **curl** (для проверки сервисов)
- **lsof** (для управления процессами)

### API ключи:
Убедитесь, что у вас есть следующие API ключи в файле `.env`:

```env
# Основные настройки
GIGACHAT_API_KEY=ваш_ключ_gigachat
TELEGRAM_API_KEY=ваш_токен_telegram_бота
FEEDBACK_BOT_TOKEN=токен_для_фидбек_бота
FEEDBACK_CHAT_ID=id_чата_для_фидбека

# Настройки базы данных
DATABASE_URL=./src/main_version/AI_agent.db

# Настройки для веб-приложения
RAG_PATH=./src/main_version

# Настройки логирования
LOG_LEVEL=INFO
```

## 🛠 Быстрый старт

### 1. Установка зависимостей

```bash
# Делаем скрипты исполняемыми
chmod +x *.sh

# Устанавливаем все зависимости
./install_dependencies.sh
```

### 2. Запуск всех сервисов

```bash
# Запускаем все компоненты одновременно
./run_all.sh
```

После успешного запуска будут доступны:

| Сервис | URL | Описание |
|--------|-----|----------|
| 🔥 RAG API | http://localhost:8000 | FastAPI с документацией на `/docs` |
| 🌐 Web API | http://localhost:5001 | REST API для веб-интерфейса |
| ⚙️ Admin панель | http://localhost:5002 | Административный интерфейс |
| 🤖 Telegram бот | - | Работает в фоне |

### 3. Остановка сервисов

```bash
# Остановка всех сервисов
./stop_all.sh

# Или если запущено через run_all.sh - нажать Ctrl+C
```

## 🔧 Запуск отдельных компонентов

Если нужно запустить только определенные компоненты:

```bash
# Только RAG сервис
./run_rag_service.sh

# Только Telegram бот 
./run_telegram_bot.sh

# Только Web API
./run_webapp_api.sh

# Только Admin панель
./run_admin.sh
```

## 📊 Мониторинг и логи

### Просмотр логов:
```bash
# Логи сохраняются в папку logs/
tail -f logs/rag_service.log     # RAG сервис
tail -f logs/telegram_bot.log    # Telegram бот
tail -f logs/webapp_api.log      # Web API  
tail -f logs/admin.log           # Admin панель
```

### Проверка статуса сервисов:
```bash
# Проверка портов
netstat -tulpn | grep -E ':(8000|5001|5002)'

# Проверка здоровья RAG API
curl http://localhost:8000/docs

# Проверка Web API
curl http://localhost:5001/api/health
```

## 🏗 Структура проекта

```
RAG_agent/
├── src/main_version/          # Основной RAG сервис
│   ├── rag_service.py         # FastAPI приложение
│   ├── telegram_bot.py        # Telegram бот
│   ├── requirements.txt       # Зависимости
│   └── txt_docs/              # Документы для RAG
├── webapp/api/                # Web API
│   ├── app.py                 # Flask приложение  
│   └── requirements.txt       # Зависимости
├── admin/                     # Admin панель
│   ├── app.py                 # Flask приложение
│   └── requirements.txt       # Зависимости
├── .env                       # Переменные окружения
└── *.sh                       # Скрипты запуска
```

## 🔐 Доступ к Admin панели

- **URL:** http://localhost:5002
- **Логин:** `admin_tg_bot`  
- **Пароль:** `135beton531`

Функции админки:
- Управление промптами для AI
- Управление документами RAG
- Просмотр пользователей и статистики
- Системные настройки

## 🐛 Решение проблем

### Проблема: RAG сервис не запускается
```bash
# Проверить логи
cat logs/rag_service.log

# Проверить, что порт свободен
lsof -i :8000

# Проверить зависимости
cd src/main_version && source venv/bin/activate && pip list
```

### Проблема: Telegram бот не отвечает
```bash
# Проверить логи бота
cat logs/telegram_bot.log

# Проверить переменные окружения
grep TELEGRAM_API_KEY .env

# Проверить подключение к RAG сервису
curl http://localhost:8000/docs
```

### Проблема: Порты заняты
```bash
# Найти процессы на портах
lsof -i :8000
lsof -i :5001  
lsof -i :5002

# Остановить все
./stop_all.sh
```

### Проблема: Недостаточно памяти
RAG сервис использует модели машинного обучения, которые требуют памяти:
- Минимум: 4GB RAM
- Рекомендуется: 8GB+ RAM

## 📚 API документация

### RAG API (порт 8000)
- **Swagger UI:** http://localhost:8000/docs
- **WebSocket:** ws://localhost:8000/ws
- **Suggestions:** ws://localhost:8000/ws_suggest

### Web API (порт 5001)
- **POST /api/ask** - отправка вопросов
- **GET /api/questions** - библиотека вопросов
- **GET /api/health** - проверка здоровья
- **POST /api/feedback** - отправка отзывов

## 🔄 Обновление проекта

```bash
# Остановить все сервисы
./stop_all.sh

# Обновить код (git pull и т.д.)

# Переустановить зависимости при необходимости
./install_dependencies.sh

# Запустить заново
./run_all.sh
```

## 💡 Полезные советы

1. **Первый запуск может занять время** - модели загружаются и индексируются
2. **Проверяйте логи** при проблемах - они содержат подробную информацию
3. **Используйте Admin панель** для настройки промптов и документов
4. **Telegram бот требует интернет** для работы с Telegram API
5. **RAG сервис можно использовать** независимо через API

---

✨ **Готово!** Ваш RAG Agent работает локально и готов к использованию! 