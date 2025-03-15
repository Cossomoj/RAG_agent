## Тип проекта 
**RAG** (Retrieval-Augmented Generation) агент, реализованный как **Telegram**-бот

## Основные компоненты
* **telegram_bot.py** - реализация Telegram бота
* **rag_service.py** - сервис RAG для обработки запросов
* **main.py** - точка входа, запускающая бота и RAG сервис
* **monitor.py** - мониторинг работы системы

## Технологический стек
* **Telegram Bot API** (через telebot)
* **LangChain** (с модулями для GigaChat и Hugging Face)
* **FAISS** для векторного поиска
* **FastAPI** и **Uvicorn** для веб-сервисов
* **Sentence Transformers** для эмбеддингов

## Структура проекта
* **src/main_version/** - основной код
* **src/bot/** - дополнительные компоненты бота и тесты
* **src/config/** - конфигурационные файлы
* **src/scripts/** - вспомогательные скрипты

## Архитектура
* Проект использует **микросервисную архитектуру** с отдельными компонентами для бота и RAG сервиса
* Компоненты запускаются **параллельно** через **main.py**
* Есть система мониторинга через **monitor.py**

## Особенности реализации
* Использование асинхронного программирования (**asyncio**, **websockets**)
* Интеграция с различными LLM через **LangChain** (**GigaChat**, Hugging **Face**)
* Векторный поиск на базе **FAISS**
* Использование современных трансформеров для обработки текста
* Проект является полноценным решением для **RAG** с использованием современных технологий, разделен на логические компоненты и использует популярные библиотеки для работы с **LLM** и векторными базами данных
