import asyncio
import websockets
import json

async def test_prompt_with_rag_indicators(prompt_id, question, role, specialization, context="[]", expected_rag=True):
    """
    Тестирует промпт и проверяет, используется ли RAG на основе содержания ответа
    """
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"\n=== ТЕСТ ПРОМПТА {prompt_id} ===")
            print(f"Вопрос: {question}")
            print(f"Роль: {role}")
            print(f"Специализация: {specialization}")
            print(f"Ожидается RAG: {'ДА' if expected_rag else 'НЕТ'}")
            
            # Отправляем данные
            await websocket.send(question)
            await websocket.send(role)
            await websocket.send(specialization)
            await websocket.send(str(prompt_id))
            await websocket.send(context)
            await websocket.send("1")
            
            # Собираем ответ
            response_chunks = []
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    response_chunks.append(response)
                    if len(response_chunks) > 50:  # Ограничиваем количество chunks
                        break
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                pass
            
            if response_chunks:
                full_response = "".join(response_chunks)
                print(f"Получен ответ ({len(full_response)} символов)")
                
                # Индикаторы использования RAG (специфичные термины из документов)
                rag_indicators = [
                    "матрица компетенций", "junior", "middle", "senior", "lead",
                    "софт-скиллы", "хард-скиллы", "грейд", "компетенция", "компетенций",
                    "наставничество", "онбординг", "1-2-1", "ипр", "менторинг",
                    "backlog", "roadmap", "стейкхолдер", "po", "pm",
                    "архитектура", "микросервис", "монолит", "оценка", "производительность"
                ]
                
                # Проверяем наличие индикаторов RAG
                found_indicators = []
                for indicator in rag_indicators:
                    if indicator.lower() in full_response.lower():
                        found_indicators.append(indicator)
                
                uses_rag = len(found_indicators) > 0
                
                print(f"Найдены RAG индикаторы: {found_indicators}")
                print(f"Использует RAG: {'✅ ДА' if uses_rag else '❌ НЕТ'}")
                print(f"Соответствует ожиданиям: {'✅' if uses_rag == expected_rag else '❌'}")
                
                # Показываем первые 300 символов ответа
                print(f"Начало ответа: {full_response[:300]}...")
                
                return uses_rag
            else:
                print("❌ Ответ не получен!")
                return False
                
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

async def run_comprehensive_test():
    """Запускает комплексное тестирование промптов 777 и 888"""
    
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ RAG ДЛЯ ПРОМПТОВ 777 И 888")
    print("=" * 60)
    
    # Тест 1: Промпт 777 с релевантным вопросом (должен использовать RAG)
    result1 = await test_prompt_with_rag_indicators(
        prompt_id=777,
        question="Как развиваться в карьере разработчика?",
        role="Python разработчик",
        specialization="Backend",
        expected_rag=True
    )
    
    # Тест 2: Промпт 777 с нерелевантным вопросом (НЕ должен использовать RAG)
    result2 = await test_prompt_with_rag_indicators(
        prompt_id=777,
        question="Какая погода завтра?",
        role="Python разработчик", 
        specialization="Backend",
        expected_rag=False
    )
    
    # Тест 3: Промпт 888 с релевантным вопросом (должен использовать RAG)
    result3 = await test_prompt_with_rag_indicators(
        prompt_id=888,
        question="Расскажи про навыки лидерства",
        role="Лид",
        specialization="Управление командой",
        context='[{"role": "user", "content": "Мы говорили про развитие команды"}]',
        expected_rag=True
    )
    
    # Тест 4: Промпт 888 с нерелевантным вопросом (НЕ должен использовать RAG)
    result4 = await test_prompt_with_rag_indicators(
        prompt_id=888,
        question="Рецепт борща",
        role="Лид",
        specialization="Управление командой",
        context='[{"role": "user", "content": "Говорили о еде"}]',
        expected_rag=False
    )
    
    # Тест 5: Промпт 777 с вопросом про матрицу компетенций (должен использовать RAG)
    result5 = await test_prompt_with_rag_indicators(
        prompt_id=777,
        question="Что такое матрица компетенций?",
        role="Стажер",
        specialization="Аналитик",
        expected_rag=True
    )
    
    # Тест 6: Промпт 888 с вопросом про онбординг (должен использовать RAG)
    result6 = await test_prompt_with_rag_indicators(
        prompt_id=888,
        question="Как проводить онбординг новых сотрудников?",
        role="Лид",
        specialization="Управление персоналом",
        context='[{"role": "user", "content": "Обсуждали процессы найма"}]',
        expected_rag=True
    )
    
    # Подводим итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    tests = [
        ("777 + релевантный вопрос", result1, True),
        ("777 + нерелевантный вопрос", result2, False), 
        ("888 + релевантный вопрос", result3, True),
        ("888 + нерелевантный вопрос", result4, False),
        ("777 + матрица компетенций", result5, True),
        ("888 + онбординг", result6, True)
    ]
    
    passed = 0
    for test_name, actual_result, expected_result in tests:
        status = "✅ ПРОШЕЛ" if actual_result == expected_result else "❌ ПРОВАЛИЛСЯ"
        print(f"{test_name}: {status}")
        if actual_result == expected_result:
            passed += 1
    
    print(f"\nРезультат: {passed}/{len(tests)} тестов прошли успешно")
    
    if passed == len(tests):
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! RAG работает корректно для промптов 777 и 888")
    else:
        print("⚠️  Некоторые тесты провалились. Требуется доработка логики.")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test()) 