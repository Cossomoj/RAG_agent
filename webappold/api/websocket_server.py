import asyncio
import websockets
import json
import logging
import sys
import os

# Добавляем путь к основному проекту для импорта RAG сервиса
sys.path.append('/var/www/html/src/main_version')

try:
    from rag_service import RAGService
except ImportError:
    print("Не удалось импортировать RAG сервис. Используем заглушку.")
    RAGService = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRAGWebSocketServer:
    def __init__(self):
        self.rag_service = None
        if RAGService:
            try:
                self.rag_service = RAGService()
                logger.info("RAG сервис инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации RAG сервиса: {e}")
    
    async def handle_websocket(self, websocket, path):
        """Обработка WebSocket соединений"""
        logger.info(f"Новое WebSocket соединение: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    # Парсим входящее сообщение
                    data = json.loads(message)
                    question = data.get('question', '')
                    user_id = data.get('user_id', 'guest')
                    role = data.get('role', '')
                    specialization = data.get('specialization', '')
                    
                    logger.info(f"Получен вопрос от пользователя {user_id}: {question[:100]}...")
                    
                    # Обрабатываем запрос
                    response = await self.process_question(question, user_id, role, specialization)
                    
                    # Отправляем ответ
                    await websocket.send(json.dumps(response, ensure_ascii=False))
                    
                except json.JSONDecodeError:
                    error_response = {
                        "answer": "Ошибка: неверный формат сообщения",
                        "suggested_questions": []
                    }
                    await websocket.send(json.dumps(error_response, ensure_ascii=False))
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки сообщения: {e}")
                    error_response = {
                        "answer": "Извините, произошла ошибка при обработке вашего запроса.",
                        "suggested_questions": []
                    }
                    await websocket.send(json.dumps(error_response, ensure_ascii=False))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket соединение закрыто")
        except Exception as e:
            logger.error(f"Ошибка WebSocket: {e}")
    
    async def process_question(self, question, user_id, role, specialization):
        """Обработка вопроса пользователя"""
        try:
            if self.rag_service:
                # Используем настоящий RAG сервис
                answer = await self.rag_service.get_answer(question, role, specialization)
                suggested_questions = await self.rag_service.get_suggested_questions(question, answer)
            else:
                # Заглушка для тестирования
                answer = f"Это тестовый ответ на ваш вопрос: '{question}'\n\n"
                answer += f"Роль: {role}\nСпециализация: {specialization}\n\n"
                answer += "RAG сервис временно недоступен. Это демо-ответ для проверки работы мини-приложения."
                
                suggested_questions = [
                    "Как развиваться в выбранной роли?",
                    "Какие навыки нужно изучить?",
                    "Как составить план обучения?"
                ]
            
            return {
                "answer": answer,
                "suggested_questions": suggested_questions
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки вопроса: {e}")
            return {
                "answer": "Извините, произошла ошибка при обработке вашего вопроса. Попробуйте позже.",
                "suggested_questions": []
            }

def main():
    """Запуск WebSocket сервера"""
    server = SimpleRAGWebSocketServer()
    
    logger.info("Запуск WebSocket сервера на ws://localhost:8000")
    
    start_server = websockets.serve(
        server.handle_websocket,
        "localhost",
        8000,
        ping_interval=20,
        ping_timeout=10
    )
    
    asyncio.get_event_loop().run_until_complete(start_server)
    logger.info("WebSocket сервер запущен на порту 8000")
    
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Остановка WebSocket сервера")

if __name__ == "__main__":
    main() 