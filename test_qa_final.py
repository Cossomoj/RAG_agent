#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import websockets

async def test_qa_fix():
    """
    Финальный тест исправления QA проблемы
    """
    uri = "ws://localhost:8001/ws"
    
    try:
        print("🔄 Подключение к RAG сервису...")
        async with websockets.connect(uri) as websocket:
            print("✅ Подключение успешно!")
            
            # Тест запрос для QA
            request_data = {
                "question": "Что я могу ожидать от своего PO/PM?",
                "role": "Специалист", 
                "specialization": "Тестировщик",
                "user_id": "test_qa_final",
                "question_id": 1,
                "dialogue_context": "[]"
            }
            
            print(f"📤 Отправляем запрос:")
            print(f"   Роль: {request_data['role']}")
            print(f"   Специализация: {request_data['specialization']}")
            print(f"   Вопрос: {request_data['question']}")
            
            await websocket.send(json.dumps(request_data))
            
            print("\n📥 Получаем ответ:")
            print("-" * 60)
            
            full_response = ""
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "chunk":
                        chunk = data.get("content", "")
                        full_response += chunk
                        print(chunk, end="", flush=True)
                    elif data.get("type") == "end":
                        print(f"\n" + "-" * 60)
                        print(f"✅ Получен полный ответ ({len(full_response)} символов)")
                        break
                    elif data.get("type") == "error":
                        print(f"❌ Ошибка: {data.get('content')}")
                        return None
                        
                except asyncio.TimeoutError:
                    print("⏰ Таймаут при получении ответа")
                    break
            
            # Анализ ответа
            print("\n" + "="*60)
            print("🔍 ФИНАЛЬНЫЙ АНАЛИЗ:")
            
            qa_keywords = ['тестиров', 'качест', 'qa', 'баг', 'тест', 'критери', 'стратег']
            analyst_keywords = ['аналитик', 'требован', 'документац', 'бизнес-процесс']
            
            # Подсчет упоминаний ролей
            qa_mentions = full_response.lower().count('тестировщик') + full_response.lower().count('qa')
            analyst_mentions = full_response.lower().count('аналитик')
            
            qa_score = sum(1 for keyword in qa_keywords if keyword in full_response.lower())
            analyst_score = sum(1 for keyword in analyst_keywords if keyword in full_response.lower())
            
            print(f"📊 Анализ содержимого:")
            print(f"   QA-термины: {qa_score}")
            print(f"   Аналитические термины: {analyst_score}")
            print(f"   Упоминания 'тестировщик/qa': {qa_mentions}")
            print(f"   Упоминания 'аналитик': {analyst_mentions}")
            
            # Проверка наличия слов "аналитик" в разных падежах
            analyst_variants = ['аналитик', 'аналитика', 'аналитики', 'аналитику', 'аналитиком']
            found_analyst_words = [word for word in analyst_variants if word in full_response.lower()]
            
            if found_analyst_words:
                print(f"❌ ПРОБЛЕМА НЕ РЕШЕНА!")
                print(f"   Найдены слова про аналитиков: {found_analyst_words}")
                print(f"   Система все еще выдает ответы для аналитиков вместо тестировщиков!")
                return False
            elif qa_score > 0 or qa_mentions > 0:
                print(f"✅ ПРОБЛЕМА РЕШЕНА!")
                print(f"   Ответ содержит QA/тестировщик-специфичные термины")
                print(f"   Нет упоминаний аналитиков")
                return True
            else:
                print(f"⚠️  НЕОПРЕДЕЛЕННЫЙ РЕЗУЛЬТАТ")
                print(f"   Ответ не содержит ни QA, ни аналитических терминов")
                return None
                
    except ConnectionRefusedError:
        print("❌ Не удалось подключиться к RAG сервису на localhost:8001")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

async def main():
    print("🚀 ФИНАЛЬНЫЙ ТЕСТ ИСПРАВЛЕНИЯ QA ПРОБЛЕМЫ")
    print("="*60)
    
    result = await test_qa_fix()
    
    if result is True:
        print("\n🎉 УСПЕХ! Проблема решена - тестировщики получают правильные ответы!")
    elif result is False:
        print("\n❌ ПРОБЛЕМА НЕ РЕШЕНА - требуется дополнительная отладка")
    else:
        print("\n❓ НЕОПРЕДЕЛЕННЫЙ РЕЗУЛЬТАТ - требуется ручная проверка")

if __name__ == "__main__":
    asyncio.run(main()) 