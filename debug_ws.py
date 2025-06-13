#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import websockets
import json

async def test_rag_websocket():
    """Тестируем WebSocket соединение с RAG сервисом точно как это делает бот"""
    uri = "ws://127.0.0.1:8000/ws"
    
    try:
        print("🔌 Подключаемся к RAG сервису...")
        async with websockets.connect(uri) as websocket:
            print("✅ Подключение установлено!")
            
            # Отправляем данные точно как бот
            question = "как меня зовут"
            role = "Обычный пользователь"
            specialization = "Не указана" 
            question_id = "888"
            context_str = "[]"  # Пустой контекст для теста
            count = "1"
            
            print("📤 Отправляем данные...")
            await websocket.send(question)
            await websocket.send(role)
            await websocket.send(specialization)
            await websocket.send(question_id)
            await websocket.send(context_str)
            await websocket.send(count)
            print(f"   Вопрос: {question}")
            print(f"   Роль: {role}")
            print(f"   Специализация: {specialization}")
            print(f"   ID: {question_id}")
            print(f"   Контекст: {context_str}")
            print(f"   Счетчик: {count}")
            
            print("⏳ Ожидаем ответ...")
            answer_parts = []
            empty_count = 0
            
            try:
                while empty_count < 5:  # Ограничиваем количество попыток
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        if response:
                            print(f"📥 Получена часть ответа: '{response}'")
                            answer_parts.append(response)
                            empty_count = 0
                        else:
                            empty_count += 1
                            print(f"⚠️ Пустой ответ #{empty_count}")
                    except asyncio.TimeoutError:
                        print("⏰ Таймаут ожидания")
                        break
                        
            except websockets.exceptions.ConnectionClosed:
                print("🔌 Соединение закрыто сервером")
                
            print(f"\n📋 Итого получено частей ответа: {len(answer_parts)}")
            if answer_parts:
                full_answer = "".join(answer_parts)
                print(f"💬 Полный ответ: '{full_answer}'")
            else:
                print("❌ Ответ не получен")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_websocket()) 