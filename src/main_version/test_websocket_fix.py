#!/usr/bin/env python3
"""
Быстрый тест WebSocket стриминга для проверки исправлений
"""
import asyncio
import websockets
import json

async def test_websocket_streaming():
    """Тестирует WebSocket стриминг с исправлениями"""
    uri = "ws://localhost:8000/ws"
    
    # Тестовые данные
    test_cases = [
        {
            "name": "ID 1 - Обычный вопрос с RAG",
            "question": "Что я могу ожидать от своего PO/PM?",
            "role": "Стажер",
            "specialization": "Аналитик", 
            "question_id": "1",
            "context": "[]",
            "count": "1"
        },
        {
            "name": "ID 777 - Свободный вопрос",
            "question": "Как улучшить навыки коммуникации?",
            "role": "Специалист", 
            "specialization": "Python",
            "question_id": "777",
            "context": "[]",
            "count": "1"
        },
        {
            "name": "ID 888 - Свободный ввод с памятью",
            "question": "Расскажи больше про ИПР",
            "role": "Лид компетенции",
            "specialization": "Аналитик",
            "question_id": "888", 
            "context": "[]",
            "count": "1"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Тестируем: {test_case['name']}")
        print(f"   Вопрос: {test_case['question']}")
        
        try:
            async with websockets.connect(uri) as websocket:
                # Отправляем данные последовательно как в оригинальном коде
                await websocket.send(test_case["question"])
                await websocket.send(test_case["role"])
                await websocket.send(test_case["specialization"])
                await websocket.send(test_case["question_id"])
                await websocket.send(test_case["context"])
                await websocket.send(test_case["count"])
                
                print("   📤 Данные отправлены, ждем ответ...")
                
                # Собираем стриминг ответ
                response_chunks = []
                chunk_count = 0
                
                try:
                    while True:
                        chunk = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        chunk_count += 1
                        response_chunks.append(chunk)
                        print(f"   📥 Chunk #{chunk_count}: {chunk[:50]}...")
                        
                        # Ограничиваем количество chunks для теста
                        if chunk_count >= 10:
                            break
                            
                except asyncio.TimeoutError:
                    print("   ⏰ Timeout - стриминг завершен")
                except websockets.exceptions.ConnectionClosed:
                    print("   🔌 Соединение закрыто")
                
                full_response = "".join(response_chunks)
                
                print(f"\n   📊 Результат:")
                print(f"      Chunks получено: {chunk_count}")
                print(f"      Общая длина: {len(full_response)} символов")
                print(f"      Начало ответа: {full_response[:200]}...")
                
                if chunk_count == 0:
                    print("   ❌ ОШИБКА: Нет ответа!")
                elif len(full_response.strip()) == 0:
                    print("   ❌ ОШИБКА: Пустой ответ!")
                else:
                    print("   ✅ Ответ получен успешно")
                    
        except Exception as e:
            print(f"   ❌ ОШИБКА подключения: {e}")
        
        print("-" * 60)

if __name__ == "__main__":
    print("🚀 Запуск теста WebSocket стриминга...")
    asyncio.run(test_websocket_streaming())
    print("✅ Тест завершен") 