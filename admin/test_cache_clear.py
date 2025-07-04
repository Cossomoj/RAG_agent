#!/usr/bin/env python3
"""
Тестовый скрипт для проверки очистки кеша через админку
"""

import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Конфигурация
TELEGRAM_BOT_URL = os.getenv('TELEGRAM_BOT_URL', 'http://localhost:8007')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:5000')
ADMIN_URL = os.getenv('ADMIN_URL', 'http://localhost:5003')

def test_service_health(url, name):
    """Проверяет доступность сервиса"""
    try:
        if 'bot' in name.lower():
            response = requests.get(f"{url}/ping", timeout=5)
        else:
            response = requests.get(f"{url}/api/health", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ {name} доступен ({url})")
            return True
        else:
            print(f"❌ {name} недоступен: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} недоступен: соединение отклонено ({url})")
        return False
    except Exception as e:
        print(f"❌ {name} недоступен: {e}")
        return False

def test_direct_cache_clear(url, name):
    """Тестирует прямую очистку кеша сервиса"""
    try:
        if 'bot' in name.lower():
            endpoint = f"{url}/clear-cache"
        else:
            endpoint = f"{url}/api/clear-cache"
            
        response = requests.post(endpoint, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ {name}: прямая очистка кеша успешна")
                return True
            else:
                print(f"❌ {name}: прямая очистка кеша неудачна: {data.get('error')}")
                return False
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: ошибка очистки кеша: {e}")
        return False

def test_admin_cache_clear():
    """Тестирует очистку кеша через админку"""
    try:
        # Создаем сессию для работы с cookies
        session = requests.Session()
        
        # Попробуем очистить кеш через админку
        # В реальности нужна аутентификация, но можем протестировать endpoint
        response = session.post(f"{ADMIN_URL}/system/clear-cache", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Админка: очистка кеша через админку успешна")
                print(f"   Сообщение: {data.get('message')}")
                return True
            else:
                print(f"⚠️  Админка: частичная очистка кеша")
                print(f"   Сообщение: {data.get('message', data.get('error'))}")
                return False
        elif response.status_code == 302:
            print(f"⚠️  Админка: требуется аутентификация (HTTP 302)")
            print(f"   Проверьте доступность админки в браузере")
            return False
        else:
            print(f"❌ Админка: HTTP {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Админка недоступна: соединение отклонено ({ADMIN_URL})")
        return False
    except Exception as e:
        print(f"❌ Админка: ошибка: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ОЧИСТКИ КЕША")
    print("=" * 50)
    print(f"Конфигурация:")
    print(f"  Телеграм бот: {TELEGRAM_BOT_URL}")
    print(f"  Мини-приложение: {WEBAPP_URL}")
    print(f"  Админка: {ADMIN_URL}")
    print("=" * 50)
    
    # 1. Проверяем доступность сервисов
    print("\n1️⃣ ПРОВЕРКА ДОСТУПНОСТИ СЕРВИСОВ")
    bot_ok = test_service_health(TELEGRAM_BOT_URL, "Телеграм бот")
    webapp_ok = test_service_health(WEBAPP_URL, "Мини-приложение")
    admin_ok = test_service_health(ADMIN_URL, "Админка")
    
    # 2. Тестируем прямую очистку кеша
    print("\n2️⃣ ПРЯМАЯ ОЧИСТКА КЕША")
    if bot_ok:
        test_direct_cache_clear(TELEGRAM_BOT_URL, "Телеграм бот")
    if webapp_ok:
        test_direct_cache_clear(WEBAPP_URL, "Мини-приложение")
    
    # 3. Тестируем очистку кеша через админку
    print("\n3️⃣ ОЧИСТКА КЕША ЧЕРЕЗ АДМИНКУ")
    if admin_ok:
        test_admin_cache_clear()
    else:
        print("❌ Пропускаем тест админки - сервис недоступен")
    
    # 4. Итоги и рекомендации
    print("\n" + "=" * 50)
    print("📋 ИТОГИ И РЕКОМЕНДАЦИИ")
    
    if not any([bot_ok, webapp_ok, admin_ok]):
        print("❌ Все сервисы недоступны!")
        print("🔧 Рекомендации:")
        print("   1. Проверьте, что сервисы запущены")
        print("   2. Проверьте правильность URL в .env файле")
        print("   3. Проверьте сетевое соединение")
        return False
    
    if bot_ok and webapp_ok and admin_ok:
        print("✅ Все сервисы доступны!")
        print("🔧 Для полной проверки:")
        print("   1. Войдите в админку через браузер")
        print("   2. Нажмите кнопку 'Очистить кеш'")
        print("   3. Проверьте логи админки")
    else:
        print("⚠️  Некоторые сервисы недоступны")
        if not bot_ok:
            print("   - Телеграм бот недоступен")
        if not webapp_ok:
            print("   - Мини-приложение недоступно")
        if not admin_ok:
            print("   - Админка недоступна")
    
    print("\n🔍 ДИАГНОСТИКА:")
    print("   Для проверки логов админки ищите строку:")
    print("   [ADMIN] Очистка кешей: TELEGRAM_BOT_URL=..., WEBAPP_URL=...")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 