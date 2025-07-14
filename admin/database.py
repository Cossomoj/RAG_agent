import sqlite3
from datetime import datetime
import os

DATABASE_URL = "src/main_version/AI_agent.db"

class DatabaseOperations:
    def __init__(self, db_path=DATABASE_URL):
        # Преобразуем относительный путь в абсолютный
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', db_path))

        # Проверяем существование файла базы данных
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"База данных не найдена по пути: {self.db_path}")

    def get_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Это позволит получать результаты в виде словарей
            return conn
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Ошибка подключения к базе данных: {e}")

    def get_all_prompts(self):
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM Prompts ORDER BY created_at DESC')
                prompts = [dict(row) for row in cursor.fetchall()]
                return prompts
        except sqlite3.Error as e:
            return []

    def add_prompt(self, question_id, question_text, prompt_template):
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO Prompts (question_id, question_text, prompt_template) VALUES (?, ?, ?)',
                (question_id, question_text, prompt_template)
            )
            conn.commit()
            return cursor.lastrowid

    def get_prompt(self, prompt_id):
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM Prompts WHERE question_id = ?', (prompt_id,))
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None

    def update_prompt(self, old_prompt_id, new_question_id, question_text, prompt_template):
        with self.get_db() as conn:
            cursor = conn.cursor()
            
            # Если ID изменился, нужно проверить, что новый ID не занят
            if old_prompt_id != new_question_id:
                cursor.execute('SELECT 1 FROM Prompts WHERE question_id = ?', (new_question_id,))
                if cursor.fetchone():
                    raise ValueError(f"Промпт с ID {new_question_id} уже существует")
                
                # Удаляем старую запись и создаем новую
                cursor.execute('DELETE FROM Prompts WHERE question_id = ?', (old_prompt_id,))
                cursor.execute(
                    'INSERT INTO Prompts (question_id, question_text, prompt_template) VALUES (?, ?, ?)',
                    (new_question_id, question_text, prompt_template)
                )
            else:
                # Просто обновляем существующую запись
                cursor.execute(
                    'UPDATE Prompts SET question_text = ?, prompt_template = ? WHERE question_id = ?',
                    (question_text, prompt_template, old_prompt_id)
                )
            
            conn.commit()
            if cursor.rowcount == 0 and old_prompt_id == new_question_id:
                raise ValueError(f"Промпт с ID {old_prompt_id} не найден")

    def delete_prompt(self, prompt_id):
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Prompts WHERE question_id = ?', (prompt_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Промпт с ID {prompt_id} не найден")

    def get_all_users(self, page=1, per_page=10, sort_by='last_activity', sort_order='desc'):
        """Получение списка всех пользователей с их статистикой, пагинацией и сортировкой"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                
                # Валидация параметров сортировки
                valid_sort_columns = ['user_id', 'username', 'user_fullname', 'create_time', 'last_activity', 'message_count', 'reminder_status']
                if sort_by not in valid_sort_columns:
                    sort_by = 'last_activity'
                
                if sort_order.lower() not in ['asc', 'desc']:
                    sort_order = 'desc'
                
                # Основной запрос с сортировкой
                query = f"""
                SELECT 
                    u.user_id,
                    u.username,
                    u.user_fullname,
                    u.create_time,
                    COUNT(DISTINCT m.message) as message_count,
                    MAX(m.time) as last_activity,
                    u.reminder as reminder_status
                FROM Users u
                LEFT JOIN Message_history m ON u.user_id = m.user_id
                GROUP BY u.user_id
                ORDER BY {sort_by} {sort_order.upper()}
                LIMIT ? OFFSET ?
                """
                
                offset = (page - 1) * per_page
                cursor.execute(query, (per_page, offset))
                columns = [description[0] for description in cursor.description]
                users = []
                
                for row in cursor.fetchall():
                    user_dict = dict(zip(columns, row))
                    # Получаем последние сообщения пользователя
                    cursor.execute("""
                        SELECT role, message, time
                        FROM Message_history
                        WHERE user_id = ?
                        ORDER BY time DESC
                        LIMIT 5
                    """, (user_dict['user_id'],))
                    user_dict['recent_messages'] = [
                        {
                            'role': msg[0],  # Это поле role в Message_history (user/assistant), не Role пользователя
                            'message': msg[1],
                            'time': msg[2]
                        }
                        for msg in cursor.fetchall()
                    ]
                    users.append(user_dict)
                
                # Получаем общее количество пользователей для пагинации
                cursor.execute("SELECT COUNT(*) FROM Users")
                total_users = cursor.fetchone()[0]
                
                return {
                    'users': users,
                    'total': total_users,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_users + per_page - 1) // per_page,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                }
                
        except sqlite3.Error as e:
            return {
                'users': [],
                'total': 0,
                'page': 1,
                'per_page': per_page,
                'total_pages': 0,
                'sort_by': sort_by,
                'sort_order': sort_order
            }

    def get_user_details(self, user_id):
        """Получение детальной информации о пользователе"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                # Основная информация о пользователе
                cursor.execute("""
                    SELECT 
                        u.*,
                        COUNT(DISTINCT m.message) as message_count,
                        MAX(m.time) as last_activity
                    FROM Users u
                    LEFT JOIN Message_history m ON u.user_id = m.user_id
                    WHERE u.user_id = ?
                    GROUP BY u.user_id
                """, (user_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                columns = [description[0] for description in cursor.description]
                user_details = dict(zip(columns, row))

                # Получаем все сообщения пользователя
                cursor.execute("""
                    SELECT role, message, time
                    FROM Message_history
                    WHERE user_id = ?
                    ORDER BY time DESC
                """, (user_id,))
                user_details['messages'] = [
                    {
                        'role': msg[0],  # Это поле role в Message_history (user/assistant), не Role пользователя
                        'message': msg[1],
                        'time': msg[2]
                    }
                    for msg in cursor.fetchall()
                ]

                # Получаем все напоминания пользователя
                cursor.execute("""
                    SELECT id_rem, reminder_text, reminder_time
                    FROM Reminder
                    WHERE user_id = ?
                    ORDER BY reminder_time DESC
                """, (user_id,))
                user_details['reminders'] = [
                    {
                        'id': rem[0],
                        'text': rem[1],
                        'time': rem[2]
                    }
                    for rem in cursor.fetchall()
                ]

                return user_details
        except sqlite3.Error as e:
            return None

    def get_statistics(self, days=30):
        """Получение статистики за указанное количество дней"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                
                # Общие метрики
                cursor.execute("SELECT COUNT(*) FROM Users")
                total_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM Message_history")
                total_messages = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM Reminder")
                total_reminders = cursor.fetchone()[0]
                
                # Новые пользователи за период
                cursor.execute("""
                    SELECT COUNT(*) FROM Users 
                    WHERE create_time >= datetime('now', '-{} days')
                """.format(days))
                new_users = cursor.fetchone()[0]
                
                # Активные пользователи за период (отправившие сообщения)
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM Message_history 
                    WHERE time >= datetime('now', '-{} days')
                """.format(days))
                active_users = cursor.fetchone()[0]
                
                # Регистрации по дням за период
                cursor.execute("""
                    SELECT DATE(create_time) as date, COUNT(*) as count
                    FROM Users 
                    WHERE create_time >= datetime('now', '-{} days')
                    GROUP BY DATE(create_time)
                    ORDER BY date
                """.format(days))
                registrations_by_day = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                # Сообщения по дням за период
                cursor.execute("""
                    SELECT DATE(time) as date, COUNT(*) as count
                    FROM Message_history 
                    WHERE time >= datetime('now', '-{} days') AND role = 'user'
                    GROUP BY DATE(time)
                    ORDER BY date
                """.format(days))
                messages_by_day = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                # Топ активных пользователей за период
                cursor.execute("""
                    SELECT u.user_id, u.username, u.user_fullname, COUNT(m.message) as message_count
                    FROM Users u
                    LEFT JOIN Message_history m ON u.user_id = m.user_id 
                    WHERE m.time >= datetime('now', '-{} days') AND m.role = 'user'
                    GROUP BY u.user_id
                    ORDER BY message_count DESC
                    LIMIT 10
                """.format(days))
                top_users = [
                    {
                        'user_id': row[0],
                        'username': row[1] if (row[1] and row[1] != 'не указан' and row[1].strip()) else 'Не указано',
                        'user_fullname': row[2] if (row[2] and row[2].strip()) else 'Не указано',
                        'message_count': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
                # Статистика по специализациям
                cursor.execute("""
                    SELECT Specialization, COUNT(*) as count
                    FROM Users 
                    WHERE Specialization IS NOT NULL
                    GROUP BY Specialization
                    ORDER BY count DESC
                """)
                specializations = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                # Статистика по ролям (убрана, так как поле Role удалено)
                roles = []
                
                return {
                    'total_users': total_users,
                    'total_messages': total_messages,
                    'total_reminders': total_reminders,
                    'new_users': new_users,
                    'active_users': active_users,
                    'registrations_by_day': registrations_by_day,
                    'messages_by_day': messages_by_day,
                    'top_users': top_users,
                    'specializations': specializations,
                    'roles': roles,
                    'period_days': days
                }
                
        except sqlite3.Error as e:
            return {
                'total_users': 0,
                'total_messages': 0,
                'total_reminders': 0,
                'new_users': 0,
                'active_users': 0,
                'registrations_by_day': [],
                'messages_by_day': [],
                'top_users': [],
                'specializations': [],
                'roles': [],
                'period_days': days
            }
    
    def get_all_questions(self, page=1, per_page=20, category=None):
        """Получение списка всех вопросов с пагинацией и фильтрацией"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                
                # Базовый запрос
                base_query = """
                SELECT q.*, p.prompt_template, v.display_name as vector_store_display
                FROM Questions q
                LEFT JOIN Prompts p ON q.prompt_id = p.question_id
                LEFT JOIN VectorStores v ON q.vector_store = v.name
                """
                
                # Добавляем фильтр по тегу если нужно
                where_clause = ""
                params = []
                if category:
                    where_clause = "WHERE q.category = ?"
                    params.append(category)
                
                # Считаем общее количество
                count_query = f"SELECT COUNT(*) FROM Questions q {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # Получаем вопросы с пагинацией
                query = f"{base_query} {where_clause} ORDER BY q.order_position, q.id LIMIT ? OFFSET ?"
                params.extend([per_page, (page - 1) * per_page])
                cursor.execute(query, params)
                
                questions = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'questions': questions,
                    'total': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
                
        except sqlite3.Error as e:
            return {
                'questions': [],
                'total': 0,
                'page': 1,
                'per_page': per_page,
                'total_pages': 0
            }
    
    def get_question(self, callback_data):
        """Получение одного вопроса по callback_data"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.*, p.prompt_template
                FROM Questions q
                LEFT JOIN Prompts p ON q.prompt_id = p.question_id
                WHERE q.callback_data = ?
            """, (callback_data,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def add_question(self, callback_data, question_text, question_id, category=None, 
                    specialization=None, vector_store='auto', prompt_id=None, 
                    is_active=True, order_position=None):
        """Добавление нового вопроса (убран параметр role)"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                
                # Если order_position не указан, ставим в конец
                if order_position is None:
                    cursor.execute("SELECT MAX(order_position) FROM Questions")
                    max_pos = cursor.fetchone()[0] or 0
                    order_position = max_pos + 10
                
                cursor.execute("""
                    INSERT INTO Questions 
                    (callback_data, question_text, question_id, category, 
                     specialization, vector_store, prompt_id, is_active, order_position)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    callback_data, question_text, question_id, category,
                    specialization, vector_store, prompt_id, is_active, order_position
                ))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise
    
    def update_question(self, old_callback_data, **kwargs):
        """Обновление существующего вопроса"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                
                # Строим запрос на обновление
                set_parts = []
                values = []
                
                for key, value in kwargs.items():
                    if key in ['callback_data', 'question_text', 'question_id', 'category', 
                              'specialization', 'vector_store', 'prompt_id', 
                              'is_active', 'order_position']:
                        set_parts.append(f"{key} = ?")
                        values.append(value)
                
                if not set_parts:
                    return False
                
                values.append(old_callback_data)
                
                cursor.execute(f"""
                    UPDATE Questions 
                    SET {', '.join(set_parts)}, updated_at = CURRENT_TIMESTAMP
                    WHERE callback_data = ?
                """, values)
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            raise
    
    def delete_question(self, callback_data):
        """Удаление вопроса"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Questions WHERE callback_data = ?", (callback_data,))
            conn.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Вопрос с callback_data {callback_data} не найден")
    
    def get_all_vector_stores(self):
        """Получение списка всех векторных хранилищ"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM VectorStores ORDER BY id")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            return []
    
    def get_question_categories(self):
        """Получение списка всех тегов вопросов"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT category, COUNT(*) as count 
                    FROM Questions 
                    WHERE category IS NOT NULL 
                    GROUP BY category 
                    ORDER BY category
                """)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            return []
    
    def reload_questions_cache(self):
        """Отправляет команду боту на перезагрузку кеша вопросов"""
        try:
            import requests
            response = requests.post('http://127.0.0.1:8007/reload-questions')
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)} 

    def init_system_settings(self):
        """Инициализация таблицы системных настроек"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS SystemSettings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        setting_key TEXT UNIQUE NOT NULL,
                        setting_value TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Добавляем настройки по умолчанию если их нет
                default_settings = [
                    ('reminder_schedule_day', '4', 'День недели для отправки регулярных сообщений (0=понедельник, 4=пятница)'),
                    ('reminder_schedule_time', '19:00', 'Время отправки регулярных сообщений (в формате HH:MM)'),
                    ('reminder_timezone', 'Europe/Moscow', 'Часовой пояс для расписания')
                ]
                
                for key, value, description in default_settings:
                    cursor.execute("""
                        INSERT OR IGNORE INTO SystemSettings (setting_key, setting_value, description)
                        VALUES (?, ?, ?)
                    """, (key, value, description))
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            return False

    def get_system_setting(self, setting_key, default_value=None):
        """Получение значения системной настройки"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT setting_value FROM SystemSettings 
                    WHERE setting_key = ?
                """, (setting_key,))
                row = cursor.fetchone()
                if row:
                    return row[0]
                return default_value
        except sqlite3.Error as e:
            return default_value

    def update_system_setting(self, setting_key, setting_value):
        """Обновление системной настройки"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO SystemSettings (setting_key, setting_value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (setting_key, setting_value))
                conn.commit()
                return True
        except sqlite3.Error as e:
            return False

    def get_reminder_schedule(self):
        """Получение настроек расписания регулярных сообщений"""
        try:
            # Инициализируем настройки если их нет
            self.init_system_settings()
            
            schedule = {
                'day': int(self.get_system_setting('reminder_schedule_day', '4')),  # По умолчанию пятница
                'time': self.get_system_setting('reminder_schedule_time', '19:00'),  # По умолчанию 19:00
                'timezone': self.get_system_setting('reminder_timezone', 'Europe/Moscow')
            }
            return schedule
        except Exception as e:
            # Возвращаем значения по умолчанию
            return {
                'day': 4,  # Пятница
                'time': '19:00',
                'timezone': 'Europe/Moscow'
            }

    def update_reminder_schedule(self, day, time, timezone='Europe/Moscow'):
        """Обновление настроек расписания регулярных сообщений"""
        try:
            # Валидация
            if not (0 <= day <= 6):
                raise ValueError("День недели должен быть от 0 (понедельник) до 6 (воскресенье)")
            
            # Проверяем формат времени
            time_parts = time.split(':')
            if len(time_parts) != 2:
                raise ValueError("Время должно быть в формате HH:MM")
            
            hour, minute = int(time_parts[0]), int(time_parts[1])
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError("Некорректное время")
            
            # Инициализируем настройки если их нет
            self.init_system_settings()
            
            # Обновляем настройки
            success = True
            success &= self.update_system_setting('reminder_schedule_day', str(day))
            success &= self.update_system_setting('reminder_schedule_time', time)
            success &= self.update_system_setting('reminder_timezone', timezone)
            
            return success
        except Exception as e:
            return False

    def get_all_system_settings(self):
        """Получение всех системных настроек"""
        try:
            self.init_system_settings()
            
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT setting_key, setting_value, description, updated_at
                    FROM SystemSettings
                    ORDER BY setting_key
                """)
                
                settings = {}
                for row in cursor.fetchall():
                    settings[row[0]] = {
                        'value': row[1],
                        'description': row[2],
                        'updated_at': row[3]
                    }
                
                return settings
        except sqlite3.Error as e:
            return {} 
