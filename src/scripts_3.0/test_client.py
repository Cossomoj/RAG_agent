import asyncio
import websockets

# Указываем URL WebSocket-сервера
WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"


async def test_websocket():
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        question = "Кто я?"  # Тестовый вопрос
        print(f"Отправляю запрос: {question}")
        
        await websocket.send(question)  # Отправляем вопрос

        print("") # ответ сервера
        try:
            while True:
                message = await websocket.recv()  # Получаем ответ частями
                print(message)  # Выводим в консоль каждую часть ответа
        except websockets.exceptions.ConnectionClosed:
            print("")

# Запускаем клиента
asyncio.run(test_websocket())
