import asyncio
import websockets

async def test_888_detailed():
    uri = "ws://localhost:8000/ws"
    
    print("=== ДЕТАЛЬНЫЙ ТЕСТ ПРОМПТА 888 ===")
    print("Вопрос: Расскажи про навыки лидерства")
    print("Роль: Лид")
    print("Специализация: Управление командой")
    print()
    
    try:
        async with websockets.connect(uri) as websocket:
            # Отправляем данные
            await websocket.send("Расскажи про навыки лидерства")
            await websocket.send("Лид")
            await websocket.send("Управление командой")
            await websocket.send("888")
            await websocket.send('[{"role": "user", "content": "Мы говорили про развитие команды"}]')
            await websocket.send("1")
            
            print("Данные отправлены, получаем ответ...")
            
            # Собираем ответ
            response_chunks = []
            chunk_count = 0
            
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    chunk_count += 1
                    response_chunks.append(response)
                    print(f"Chunk {chunk_count}: {response[:80]}...")
                    
                    if chunk_count > 30:
                        break
                        
            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                print("Соединение завершено")
            
            if response_chunks:
                full_response = "".join(response_chunks)
                print(f"\n📄 ПОЛНЫЙ ОТВЕТ ({len(full_response)} символов):")
                print("=" * 60)
                print(full_response)
                print("=" * 60)
                
                # Ищем индикаторы RAG
                rag_indicators = [
                    "матрица компетенций", "junior", "middle", "senior", "lead",
                    "софт-скиллы", "хард-скиллы", "грейд", "компетенция", "компетенций",
                    "наставничество", "онбординг", "1-2-1", "ипр", "менторинг",
                    "backlog", "roadmap", "стейкхолдер", "po", "pm",
                    "архитектура", "микросервис", "монолит", "python", "django"
                ]
                
                found_indicators = []
                for indicator in rag_indicators:
                    if indicator.lower() in full_response.lower():
                        found_indicators.append(indicator)
                
                print(f"\n🔍 АНАЛИЗ СОДЕРЖАНИЯ:")
                print(f"Найдены RAG индикаторы: {found_indicators}")
                print(f"Количество индикаторов: {len(found_indicators)}")
                
                # Проверяем упоминания из корпоративной базы знаний
                corporate_terms = [
                    "корпоративн", "документ", "база знаний", "политик", "процедур",
                    "стандарт", "регламент", "методолог", "фреймворк"
                ]
                
                found_corporate = []
                for term in corporate_terms:
                    if term.lower() in full_response.lower():
                        found_corporate.append(term)
                
                print(f"Корпоративные термины: {found_corporate}")
                
                # Оценка использования RAG
                if len(found_indicators) > 0 or len(found_corporate) > 0:
                    print("✅ ВЕРОЯТНО ИСПОЛЬЗУЕТ RAG")
                else:
                    print("❌ ВЕРОЯТНО НЕ ИСПОЛЬЗУЕТ RAG")
                    
            else:
                print("❌ Ответ не получен!")
                
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_888_detailed()) 