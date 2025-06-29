#!/usr/bin/env python3
"""
Скрипт валидации конфигурации RAG Agent
Проверяет корректность config.yaml файла
"""

import yaml
import os
import sys
from pathlib import Path

def validate_config(config_path="config.yaml"):
    """Валидация конфигурационного файла"""
    
    print("🔍 Валидация конфигурации RAG Agent...")
    
    # Проверка существования файла
    if not os.path.exists(config_path):
        print(f"❌ Файл конфигурации не найден: {config_path}")
        return False
    
    try:
        # Загрузка YAML
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ YAML файл загружен успешно")
        
        # Проверка обязательных секций
        required_sections = ['app', 'paths', 'network', 'admin']
        missing_sections = []
        
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Отсутствуют обязательные секции: {', '.join(missing_sections)}")
            return False
        
        print("✅ Все обязательные секции присутствуют")
        
        # Проверка путей
        print("\n📁 Проверка путей:")
        paths_config = config.get('paths', {})
        
        # Проверяем пути к директориям
        for path_name, path_value in paths_config.items():
            if path_name.endswith('_dir'):
                full_path = Path(path_value)
                if full_path.exists():
                    print(f"   ✅ {path_name}: {path_value}")
                else:
                    print(f"   ⚠️  {path_name}: {path_value} (не существует, будет создан)")
        
        # Проверяем файлы
        for path_name, path_value in paths_config.items():
            if not path_name.endswith('_dir'):
                full_path = Path(path_value)
                if full_path.exists():
                    size = full_path.stat().st_size
                    print(f"   ✅ {path_name}: {path_value} ({size} байт)")
                else:
                    print(f"   ❌ {path_name}: {path_value} (не найден)")
        
        # Проверка сетевых настроек
        print("\n🔌 Проверка сетевых настроек:")
        network_config = config.get('network', {})
        
        for service_name, service_config in network_config.items():
            if isinstance(service_config, dict) and 'port' in service_config:
                port = service_config['port']
                host = service_config.get('host', 'localhost')
                
                # Проверяем, что порт в допустимом диапазоне
                if 1 <= port <= 65535:
                    print(f"   ✅ {service_name}: {host}:{port}")
                else:
                    print(f"   ❌ {service_name}: недопустимый порт {port}")
        
        # Проверка настроек админа
        print("\n👤 Проверка настроек админа:")
        admin_config = config.get('admin', {})
        
        if 'username' in admin_config and admin_config['username']:
            print(f"   ✅ Логин: {admin_config['username']}")
        else:
            print("   ❌ Логин админа не задан")
        
        if 'password' in admin_config and admin_config['password']:
            print(f"   ✅ Пароль: {'*' * len(admin_config['password'])}")
        else:
            print("   ❌ Пароль админа не задан")
        
        # Проверка настроек логирования
        if 'logging' in config:
            print("\n📋 Проверка настроек логирования:")
            logging_config = config['logging']
            
            level = logging_config.get('level', 'INFO')
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if level in valid_levels:
                print(f"   ✅ Уровень логирования: {level}")
            else:
                print(f"   ❌ Недопустимый уровень логирования: {level}")
        
        # Проверка настроек безопасности
        if 'security' in config:
            print("\n🔒 Проверка настроек безопасности:")
            security_config = config['security']
            
            if security_config.get('rate_limiting_enabled'):
                max_requests = security_config.get('max_requests_per_minute', 60)
                print(f"   ⚠️  Rate limiting включен: {max_requests} запросов/мин")
            else:
                print("   ℹ️  Rate limiting отключен (подходит для development)")
        
        print(f"\n🎉 Валидация конфигурации завершена успешно!")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ Ошибка парсинга YAML: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def create_missing_dirs(config_path="config.yaml"):
    """Создание отсутствующих директорий"""
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        paths_config = config.get('paths', {})
        
        print("\n📁 Создание недостающих директорий:")
        for path_name, path_value in paths_config.items():
            if path_name.endswith('_dir'):
                full_path = Path(path_value)
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                    print(f"   ✅ Создана директория: {path_value}")
    
    except Exception as e:
        print(f"❌ Ошибка создания директорий: {e}")

if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    
    success = validate_config(config_file)
    
    if success:
        create_missing_dirs(config_file)
        sys.exit(0)
    else:
        sys.exit(1) 