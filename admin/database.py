import sqlite3
from datetime import datetime
import os

DATABASE_URL = "src/main_version/AI_agent.db"

class DatabaseOperations:
    def __init__(self, db_path=DATABASE_URL):
        # Преобразуем относительный путь в абсолютный
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', db_path))
        print(f"Подключение к базе данных: {self.db_path}")  # Отладочная информация
        # Проверяем существование файла базы данных
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"База данных не найдена по пути: {self.db_path}")

    def get_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Это позволит получать результаты в виде словарей
            return conn
        except sqlite3.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            raise

    def get_all_prompts(self):
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM Prompts ORDER BY created_at DESC')
                prompts = [dict(row) for row in cursor.fetchall()]
                print(f"Получено промптов: {len(prompts)}")  # Отладочная информация
                return prompts
        except sqlite3.Error as e:
            print(f"Ошибка при получении промптов: {e}")
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
                valid_sort_columns = ['user_id', 'username', 'user_fullname', 'create_time', 'last_activity', 'message_count', 'reminders_count']
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
                    COUNT(DISTINCT r.id_rem) as reminders_count
                FROM Users u
                LEFT JOIN Message_history m ON u.user_id = m.user_id
                LEFT JOIN Reminder r ON u.user_id = r.user_id
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
                            'role': msg[0],
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
            print(f"Ошибка при получении пользователей: {e}")
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
                        MAX(m.time) as last_activity,
                        COUNT(DISTINCT r.id_rem) as reminders_count
                    FROM Users u
                    LEFT JOIN Message_history m ON u.user_id = m.user_id
                    LEFT JOIN Reminder r ON u.user_id = r.user_id
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
                        'role': msg[0],
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
            print(f"Ошибка при получении деталей пользователя: {e}")
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
                        'username': row[1] or 'Не указано',
                        'user_fullname': row[2] or 'Не указано',
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
                
                # Статистика по ролям
                cursor.execute("""
                    SELECT Role, COUNT(*) as count
                    FROM Users 
                    WHERE Role IS NOT NULL
                    GROUP BY Role
                    ORDER BY count DESC
                """)
                roles = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
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
            print(f"Ошибка при получении статистики: {e}")
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