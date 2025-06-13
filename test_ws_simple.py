#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import websockets
import json

async def test_websocket():
    """Простой тест WebSocket соединения с RAG сервисом"""
    uri = "ws://localhost:8765"
    
    try:
        print("🔌 Подключаемся к WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Подключение установлено!")
            
            # Тестовое сообщение
            test_message = {
                "question": "Привет, как дела?",
                "question_id": 888,
                "role": "Обычный пользователь", 
                "specialization": "Не указана",
                "dialogue_context": []
            }
            
            print(f"📤 Отправляем: {test_message}")
            await websocket.send(json.dumps(test_message, ensure_ascii=False))
            
            print("⏳ Ожидаем ответа...")
            response = await websocket.recv()
            print(f"📥 Получен ответ: {response}")
            
            if response.strip():
                print("✅ Сервис работает!")
            else: 
                print("⚠️ Получен пустой ответ")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 