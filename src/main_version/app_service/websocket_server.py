import asyncio
import json
import logging
import os
import websockets
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("websocket_server")

# Загружаем переменные окружения
load_dotenv()
logger.info("Загрузка переменных окружения из .env файла...")

# Порт для WebSocket сервера
WS_PORT = int(os.getenv("WEBSOCKET_PORT", "8000"))
logger.info(f"WebSocket сервер будет запущен на порту {WS_PORT}")

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
                elif data.get("type") == "broadcast":
                    # Пересылаем сообщение всем клиентам
                    await notify_clients(json.dumps({
                        "type": "broadcast",
                        "from": websocket.remote_address[0],
                        "message": data.get("message", "")
                    }))
                else:
                    # Если тип не распознан, просто отвечаем эхом
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
    
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Соединение закрыто: {e}")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
    finally:
        # Убираем клиента из списка при любом завершении соединения
        await unregister(websocket)

async def main():
    """Основная функция запуска WebSocket сервера"""
    logger.info(f"Запуск WebSocket сервера на порту {WS_PORT}...")
    
    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
        logger.info(f"WebSocket сервер запущен и слушает на 0.0.0.0:{WS_PORT}")
        # Бесконечный цикл для поддержания сервера активным
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске сервера: {e}")
        raise 