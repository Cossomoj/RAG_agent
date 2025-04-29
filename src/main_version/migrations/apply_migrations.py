import sqlite3
import os
from datetime import datetime

def apply_migrations():
    """Применяет все SQL-миграции из текущей директории."""
    db_path = '/app/src/main_version/AI_agent.db'
    migrations_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Создаем таблицу для отслеживания примененных миграций, если её нет
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS applied_migrations (
            migration_name TEXT PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Получаем список всех SQL-файлов в директории
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith('.sql')])
        
        # Получаем список уже примененных миграций
        cursor.execute('SELECT migration_name FROM applied_migrations')
        applied = {row[0] for row in cursor.fetchall()}
        
        # Применяем новые миграции
        for migration_file in migration_files:
            if migration_file not in applied:
                print(f"Применяется миграция: {migration_file}")
                
                # Читаем и выполняем SQL-скрипт
                with open(os.path.join(migrations_dir, migration_file), 'r') as f:
                    sql = f.read()
                    cursor.executescript(sql)
                
                # Отмечаем миграцию как примененную
                cursor.execute(
                    'INSERT INTO applied_migrations (migration_name) VALUES (?)',
                    (migration_file,)
                )
                print(f"Миграция {migration_file} успешно применена")
        
        # Сохраняем изменения
        conn.commit()
        print("Все миграции успешно применены")
        
    except Exception as e:
        print(f"Ошибка при применении миграций: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migrations() 