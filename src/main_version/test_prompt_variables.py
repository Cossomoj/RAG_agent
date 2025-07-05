"""
Тестирование правильного использования переменных {input} и {context} в промптах
"""
import asyncio
import websockets

async def test_prompt_variables():
    """Тестируем промпты с переменными {input} и {context}"""
    
    test_cases = [
        {
            "name": "Промпт 3 - Матрица компетенций (с {input} и {context})",
            "prompt_id": 3,
            "question": "Получить матрицу компетенций",
            "role": "Аналитик", 
            "specialization": "БизнесАналитик",
            "expected_behavior": "Заполнение {input} и {context}"
        },
        {
            "name": "Промпт 777 - Общие вопросы (с {input} и {context})",
            "prompt_id": 777,
            "question": "Как развиваться в карьере?",
            "role": "Python разработчик",
            "specialization": "Backend",
            "expected_behavior": "Заполнение {input} и {context}"
        },
        {
            "name": "Промпт 888 - Свободный ввод (с {input} и {context})",
            "prompt_id": 888,
            "question": "Расскажи про лучшие практики",
            "role": "Лид",
            "specialization": "Управление командой",
            "expected_behavior": "Заполнение {input} и {context}"
        }
    ]
    
    uri = "ws://localhost:8000/ws"
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"🧪 ТЕСТ: {test_case['name']}")
        print(f"📝 Вопрос: {test_case['question']}")
        print(f"👤 Роль: {test_case['role']}")
        print(f"🎯 Специализация: {test_case['specialization']}")
        print(f"🔧 Ожидаемое поведение: {test_case['expected_behavior']}")
        print(f"{'='*60}")
        
        try:
            async with websockets.connect(uri) as websocket:
                # Отправляем данные
                await websocket.send(test_case['question'])
                await websocket.send(test_case['role'])
                await websocket.send(test_case['specialization'])
                await websocket.send(str(test_case['prompt_id']))
                await websocket.send("[]")  # context
                await websocket.send("1")   # count
                await websocket.send("by_specialization")  # vector_store
                
                print("📤 Данные отправлены, ожидаем ответ...")
                
                # Собираем первые части ответа
                response_parts = []
                try:
                    for i in range(5):  # Получаем первые 5 частей
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        if response:
                            response_parts.append(response)
                            print(f"📥 Часть {i+1}: {response[:100]}...")
                        else:
                            break
                except asyncio.TimeoutError:
                    print("⏰ Таймаут ожидания ответа")
                
                if response_parts:
                    full_response = "".join(response_parts)
                    print(f"\n📄 НАЧАЛО ОТВЕТА ({len(full_response)} символов):")
                    print("-" * 40)
                    print(full_response[:500])
                    print("-" * 40)
                    
                    # Проверяем качество ответа
                    quality_indicators = [
                        "матрица компетенций", "junior", "middle", "senior", "lead",
                        "компетенция", "навык", "развитие", "карьера"
                    ]
                    
                    found_indicators = []
                    for indicator in quality_indicators:
                        if indicator.lower() in full_response.lower():
                            found_indicators.append(indicator)
                    
                    print(f"\n🔍 АНАЛИЗ КАЧЕСТВА:")
                    print(f"Найдены индикаторы: {found_indicators}")
                    print(f"Качество: {'✅ ХОРОШЕЕ' if len(found_indicators) > 2 else '⚠️ СРЕДНЕЕ' if len(found_indicators) > 0 else '❌ НИЗКОЕ'}")
                else:
                    print("❌ Ответ не получен!")
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ПЕРЕМЕННЫХ В ПРОМПТАХ")
    print("=" * 60)
    asyncio.run(test_prompt_variables())
    print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО") 