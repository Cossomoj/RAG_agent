import asyncio
import json
import logging
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("websocket_server")

# Загрузка переменных окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Переменные окружения загружены из .env файла")
except ImportError:
    logger.warning("python-dotenv не установлен. Используем переменные окружения из системы.")
except Exception as e:
    logger.error(f"Ошибка при загрузке .env файла: {e}")

# Порт для WebSocket сервера
WEBSOCKET_PORT = int(os.environ.get("WEBSOCKET_PORT", "8000"))
logger.info(f"WebSocket сервер будет запущен на порту {WEBSOCKET_PORT}")

# Проверяем наличие необходимых библиотек
try:
    import websockets
    logger.info("Библиотека websockets загружена успешно")
except ImportError:
    logger.error("Библиотека websockets не установлена. Сервер не может быть запущен.")
    # Создаем заглушку для функции main, чтобы скрипт не падал с ошибкой
    async def main():
        logger.error("WebSocket сервер не может быть запущен из-за отсутствия необходимых библиотек")
        while True:
            await asyncio.sleep(60)
            logger.error("WebSocket сервер не работает. Отсутствуют необходимые библиотеки.")
else:
    # Хранилище активных соединений
    connected_clients = set()

    async def notify_clients(message):
        """Отправка сообщения всем подключенным клиентам"""
        if connected_clients:
            await asyncio.gather(*[client.send(message) for client in connected_clients])
            logger.info(f"Отправлено сообщение всем клиентам: {message[:50]}...")

    async def register(websocket):
        """Регистрация нового клиента"""
        connected_clients.add(websocket)
        logger.info(f"Новое подключение: {websocket.remote_address}. Всего клиентов: {len(connected_clients)}")

    async def unregister(websocket):
        """Удаление клиента при отключении"""
        connected_clients.remove(websocket)
        logger.info(f"Отключение: {websocket.remote_address}. Осталось клиентов: {len(connected_clients)}")

    async def ws_handler(websocket, path):
        """Обработчик WebSocket соединений"""
        try:
            # Регистрируем нового клиента
            await register(websocket)
            
            # Отправляем приветственное сообщение
            await websocket.send(json.dumps({
                "type": "connection_established",
                "message": "Соединение с WebSocket сервером установлено"
            }))
            
            # Слушаем сообщения от клиента
            async for message in websocket:
                logger.info(f"Получено сообщение: {message[:100]}...")
                
                try:
                    # Пытаемся распарсить JSON
                    data = json.loads(message)
                    
                    # Обрабатываем сообщение в зависимости от типа
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": data.get("timestamp", "")
                        }))
                    else:
                        # Простое эхо для всех остальных сообщений
                        await websocket.send(json.dumps({
                            "type": "echo",
                            "message": data.get("message", ""),
                            "received": True
                        }))
                        
                except json.JSONDecodeError:
                    logger.warning(f"Получено сообщение в неверном формате: {message[:50]}...")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Неверный формат JSON"
                    }))
                except Exception as e:
                    logger.error(f"Ошибка при обработке сообщения: {e}")
        
        except Exception as e:
            logger.error(f"Ошибка соединения: {e}")
        finally:
            # Убираем клиента из списка при любом завершении соединения
            if websocket in connected_clients:
                await unregister(websocket)

    async def main():
        """Основная функция запуска WebSocket сервера"""
        logger.info(f"Запуск WebSocket сервера на порту {WEBSOCKET_PORT}...")
        
        try:
            async with websockets.serve(ws_handler, "0.0.0.0", WEBSOCKET_PORT):
                logger.info(f"WebSocket сервер запущен и слушает на 0.0.0.0:{WEBSOCKET_PORT}")
                # Бесконечный цикл для поддержания сервера активным
                await asyncio.Future()
        except Exception as e:
            logger.error(f"Ошибка при запуске WebSocket сервера: {e}")
            # Ожидаем перед повторной попыткой
            await asyncio.sleep(10)
            logger.info("Пробуем перезапустить WebSocket сервер...")
            await main()  # Рекурсивный вызов для перезапуска

if __name__ == "__main__":
    try:
        # Получаем информацию о системе для диагностики
        logger.info(f"Текущая директория: {os.getcwd()}")
        logger.info(f"Содержимое директории: {os.listdir()}")
        logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'не установлен')}")
        
        # Запуск основного цикла событий
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске сервера: {e}")
        # Добавляем бесконечный цикл, чтобы процесс не завершался и supervisor не перезапускал его постоянно
        while True:
            asyncio.sleep(60)
            logger.error("WebSocket сервер в состоянии ошибки, но процесс поддерживается активным.") 