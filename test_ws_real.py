import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Подключено к WebSocket!")
            # Отправляем сообщения как ожидает RAG сервис
            await websocket.send("Привет, как дела?")
            await websocket.send("user")  
            await websocket.send("none")
            await websocket.send("888")
            
            print("📤 Сообщения отправлены, ждем ответ...")
            
            # Читаем ответ
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    if response:
                        print(f"📥 Получен ответ: {response}")
                        break
                    else:
                        print("⚠️ Пустой ответ")
                except asyncio.TimeoutError:
                    print("⏰ Таймаут ожидания ответа")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Соединение закрыто")
                    break
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws()) 