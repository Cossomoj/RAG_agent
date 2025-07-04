# Прямое обращение к RAG Service в мини-приложении

## Описание

Реализовано прямое обращение к RAG service в мини-приложении, полностью идентичное работе в телеграм боте. Это обеспечивает единообразие ответов и функциональности между двумя интерфейсами.

## Изменения

### 1. Обновлен протокол WebSocket

Функция `send_websocket_question` теперь отправляет все 7 параметров, как в телеграм боте:

```python
await websocket.send(question)          # 1. question
await websocket.send(role)              # 2. role  
await websocket.send(specialization)    # 3. specialization
await websocket.send(str(question_id))  # 4. question_id
await websocket.send(context)           # 5. context
await websocket.send("1")               # 6. count
await websocket.send(vector_store)      # 7. vector_store (ДОБАВЛЕН)
```

### 2. Добавлена поддержка vector_store

- **Автоматический выбор**: Если в запросе не указан `vector_store`, система автоматически получает его из базы данных для конкретного вопроса
- **Ручная настройка**: Можно явно указать `vector_store` в запросе к API
- **Совместимость**: Поддерживает все типы векторных хранилищ: `auto`, `by_specialization`, `analyst`, `qa`, `web`, `java`, `python`, `ensemble`

### 3. Переменные окружения

Добавлена поддержка конфигурации через переменные окружения:

```bash
# URL к базе данных
DATABASE_URL=/path/to/AI_agent.db

# URL к WebSocket серверу RAG service
WEBSOCKET_URL=ws://127.0.0.1:8000/ws

# Уровень логирования
LOG_LEVEL=INFO
```

### 4. Обновлены API endpoints

#### `/api/ask` - Свободный ввод вопросов
```json
{
  "question": "Текст вопроса",
  "user_id": "user123",
  "role": "Специалист",
  "specialization": "Python",
  "question_id": 888,
  "vector_store": "auto"
}
```

#### `/api/ask_library` - Библиотечные вопросы
```json
{
  "question": "Текст вопроса",
  "user_id": "user123", 
  "role": "Специалист",
  "specialization": "Python",
  "question_id": 15,
  "vector_store": "auto"
}
```

## Преимущества

1. **Единообразие**: Ответы в мини-приложении полностью идентичны ответам в телеграм боте
2. **Кеширование**: Работает кеширование ответов, как в телеграм боте
3. **Контекст диалога**: Поддерживается контекст диалога для свободного ввода (question_id=888)
4. **Гибкость**: Можно настраивать векторное хранилище для каждого вопроса
5. **Совместимость**: Полная обратная совместимость с существующим API

## Использование

### Локальная разработка
```bash
export WEBSOCKET_URL="ws://127.0.0.1:8000/ws"
export DATABASE_URL="/path/to/local/AI_agent.db"
```

### Продакшн
```bash
export WEBSOCKET_URL="ws://213.171.25.85:8000/ws"
export DATABASE_URL="/home/user1/sqlite_data_rag/AI_agent.db"
```

## Тестирование

Для проверки работы прямого обращения к RAG service:

1. Запустите RAG service на порту 8000
2. Настройте переменные окружения
3. Отправьте тестовый запрос:

```bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Что такое SDLC?",
    "user_id": "test_user",
    "role": "Специалист", 
    "specialization": "Python",
    "question_id": 23
  }'
```

## Логирование

Добавлено подробное логирование для отладки:
- Отправляемые параметры WebSocket
- Настройки vector_store
- Использование кеша
- Ошибки соединения

Все логи включают информацию о question_id, role, specialization для упрощения отладки. 