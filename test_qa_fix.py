#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import websockets
import time

async def test_qa_specialist():
    """
    Тест для проверки исправления проблемы с тестировщиками.
    Должен получить ответ специфичный для QA, а не для аналитиков.
    """
    uri = "ws://localhost:8001/ws"
    
    try:
        print("🔄 Подключение к RAG сервису...")
        async with websockets.connect(uri) as websocket:
            print("✅ Подключение успешно!")
            
            # Формируем запрос для QA специалиста
            request_data = {
                "question": "Что я могу ожидать от своего PO/PM?",
                "role": "Специалист", 
                "specialization": "Тестировщик",
                "user_id": "test_qa_user",
                "question_id": 1,
                "dialogue_context": "[]"
            }
            
            print(f"📤 Отправляем запрос: {request_data}")
            await websocket.send(json.dumps(request_data))
            
            print("📥 Получаем ответ:")
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
                        print(f"\n\n✅ Получен полный ответ ({len(full_response)} символов)")
                        break
                    elif data.get("type") == "error":
                        print(f"\n❌ Ошибка: {data.get('content')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("\n⏰ Таймаут при получении ответа")
                    break
            
            # Анализ ответа
            print("\n" + "="*60)
            print("🔍 АНАЛИЗ ОТВЕТА:")
            
            qa_keywords = ['тестиров', 'качест', 'qa', 'баг', 'тест', 'критери', 'стратег']
            analyst_keywords = ['аналит', 'требован', 'документац', 'бизнес-процесс']
            
            qa_score = sum(1 for keyword in qa_keywords if keyword in full_response.lower())
            analyst_score = sum(1 for keyword in analyst_keywords if keyword in full_response.lower())
            
            print(f"📊 QA-специфичные термины найдено: {qa_score}")
            print(f"📊 Аналитические термины найдено: {analyst_score}")
            
            if qa_score > analyst_score:
                print("✅ УСПЕХ: Ответ ориентирован на QA-специалиста!")
            elif analyst_score > qa_score:
                print("❌ ПРОБЛЕМА: Ответ все еще ориентирован на аналитика!")
            else:
                print("⚠️  НЕОПРЕДЕЛЕННО: Ответ содержит общие термины")
                
            return full_response
            
    except ConnectionRefusedError:
        print("❌ Не удалось подключиться к RAG сервису")
        print("Убедитесь, что сервис запущен на localhost:8001")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

async def main():
    print("🚀 Тест исправления проблемы с QA-специалистами")
    print("="*60)
    
    # Ждем немного для инициализации сервиса
    print("⏳ Ожидание инициализации RAG сервиса (30 сек)...")
    await asyncio.sleep(30)
    
    response = await test_qa_specialist()
    
    if response:
        print("\n✅ Тест завершен!")
    else:
        print("\n❌ Тест не удался - проверьте RAG сервис")

if __name__ == "__main__":
    asyncio.run(main()) 