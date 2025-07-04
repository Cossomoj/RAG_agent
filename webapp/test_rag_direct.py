#!/usr/bin/env python3
"""
Тестовый скрипт для проверки прямого обращения к RAG service в мини-приложении
"""

import requests
import json
import sys
import os

# Конфигурация
API_BASE_URL = "http://localhost:5000"  # URL мини-приложения
TEST_USER_ID = "test_user_123"

def test_api_endpoint(endpoint, data, description):
    """Тестирует API endpoint и выводит результат"""
    print(f"\n{'='*60}")
    print(f"ТЕСТ: {description}")
    print(f"Endpoint: {endpoint}")
    print(f"Данные: {json.dumps(data, ensure_ascii=False, indent=2)}")
    print('='*60)
    
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=60)
        
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ УСПЕХ!")
            print(f"Ответ (первые 200 символов): {result.get('answer', '')[:200]}...")
            if result.get('suggested_questions'):
                print(f"Предложенные вопросы: {len(result['suggested_questions'])}")
            return True
        else:
            print("❌ ОШИБКА!")
            print(f"Ответ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ТАЙМАУТ! Сервер не ответил в течение 60 секунд")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ОШИБКА СОЕДИНЕНИЯ! Проверьте, что мини-приложение запущено")
        return False
    except Exception as e:
        print(f"❌ НЕОЖИДАННАЯ ОШИБКА: {e}")
        return False

def test_health():
    """Проверяет доступность сервиса"""
    print("Проверяем доступность мини-приложения...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Мини-приложение доступно")
            return True
        else:
            print("❌ Мини-приложение недоступно")
            return False
    except:
        print("❌ Мини-приложение недоступно")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ПРЯМОГО ОБРАЩЕНИЯ К RAG SERVICE")
    print(f"API URL: {API_BASE_URL}")
    
    # Проверка доступности
    if not test_health():
        print("\n❌ Мини-приложение недоступно. Завершение тестирования.")
        sys.exit(1)
    
    success_count = 0
    total_tests = 0
    
    # Тест 1: Свободный ввод вопроса через /api/ask
    total_tests += 1
    if test_api_endpoint(
        "/api/ask",
        {
            "question": "Что такое SDLC?",
            "user_id": TEST_USER_ID,
            "role": "Специалист",
            "specialization": "Python",
            "question_id": 888,
            "vector_store": "auto"
        },
        "Свободный ввод вопроса (question_id=888)"
    ):
        success_count += 1
    
    # Тест 2: Библиотечный вопрос через /api/ask_library
    total_tests += 1
    if test_api_endpoint(
        "/api/ask_library",
        {
            "question": "Что такое SDLC",
            "user_id": TEST_USER_ID,
            "role": "Специалист",
            "specialization": "Python",
            "question_id": 23
        },
        "Библиотечный вопрос с кешированием (question_id=23)"
    ):
        success_count += 1
    
    # Тест 3: Вопрос с явным указанием vector_store
    total_tests += 1
    if test_api_endpoint(
        "/api/ask",
        {
            "question": "Какие есть лучшие практики разработки?",
            "user_id": TEST_USER_ID,
            "role": "Специалист",
            "specialization": "Python",
            "vector_store": "python"
        },
        "Вопрос с явным vector_store=python"
    ):
        success_count += 1
    
    # Тест 4: Вопрос для другой специализации
    total_tests += 1
    if test_api_endpoint(
        "/api/ask",
        {
            "question": "Как проводить тестирование?",
            "user_id": TEST_USER_ID,
            "role": "Специалист",
            "specialization": "Тестировщик",
            "vector_store": "qa"
        },
        "Вопрос для тестировщика с vector_store=qa"
    ):
        success_count += 1
    
    # Тест 5: Повторный библиотечный вопрос (должен вернуться из кеша)
    total_tests += 1
    if test_api_endpoint(
        "/api/ask_library",
        {
            "question": "Что такое SDLC",
            "user_id": TEST_USER_ID,
            "role": "Специалист", 
            "specialization": "Python",
            "question_id": 23
        },
        "Повторный библиотечный вопрос (из кеша)"
    ):
        success_count += 1
    
    # Итоги
    print(f"\n{'='*60}")
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print('='*60)
    print(f"Успешных тестов: {success_count}/{total_tests}")
    print(f"Процент успеха: {(success_count/total_tests*100):.1f}%")
    
    if success_count == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Прямое обращение к RAG service работает корректно")
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("🔍 Проверьте:")
        print("   - Запущен ли RAG service на указанном порту")
        print("   - Правильно ли настроены переменные окружения")
        print("   - Доступна ли база данных")
    
    return success_count == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 