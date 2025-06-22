#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_websocket():
    """Тестирует WebSocket подключение к RAG сервису"""
    try:
        # Подключаемся к RAG сервису
        websocket_url = "ws://213.171.25.85:8000/ws"
        print(f"Подключаемся к {websocket_url}...")
        
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket подключение установлено!")
            
            # Тестируем готовый вопрос "Посмотреть матрицу компетенций"
            question = "Посмотреть матрицу компетенций"
            role = "Специалист"
            specialization = "Аналитик"
            question_id = "3"  # ID для этого готового вопроса
            context = "[]"
            count = "1"
            
            print(f"Отправляем данные:")
            print(f"  question: {question}")
            print(f"  role: {role}")
            print(f"  specialization: {specialization}")
            print(f"  question_id: {question_id}")
            print(f"  context: {context}")
            print(f"  count: {count}")
            
            # Отправляем данные в том же порядке, что и в телеграм боте
            await websocket.send(question)
            await websocket.send(role)
            await websocket.send(specialization)
            await websocket.send(question_id)
            await websocket.send(context)
            await websocket.send(count)
            
            print("\n📡 Данные отправлены, ожидаем ответ...")
            
            # Получаем ответ
            full_answer = ""
            empty_count = 0
            max_empty = 10
            
            while True:
                try:
                    chunk = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    if chunk:
                        empty_count = 0
                        full_answer += chunk
                        print(f"📥 Получен chunk: {chunk[:100]}...")
                    else:
                        empty_count += 1
                        print(f"📭 Пустой chunk #{empty_count}")
                        if empty_count >= max_empty:
                            break
                except asyncio.TimeoutError:
                    print("⏰ Таймаут ожидания ответа")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 WebSocket соединение закрыто")
                    break
            
            print(f"\n✅ Получен полный ответ длиной {len(full_answer)} символов:")
            print(f"Первые 500 символов: {full_answer[:500]}...")
            
            if len(full_answer) == 0:
                print("❌ ПРОБЛЕМА: Получен пустой ответ!")
                print("Это означает, что RAG сервис не может обработать готовый вопрос с ID=3")
            else:
                print("✅ Ответ получен успешно!")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 