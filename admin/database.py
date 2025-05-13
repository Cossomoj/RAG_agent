import sqlite3
from datetime import datetime
import os

DATABASE_URL = "/app/src/main_version/AI_agent.db"

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

    def add_prompt(self, question_text, prompt_template):
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO Prompts (question_text, prompt_template) VALUES (?, ?)',
                (question_text, prompt_template)
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

    def update_prompt(self, prompt_id, question_text, prompt_template):
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE Prompts SET question_text = ?, prompt_template = ? WHERE question_id = ?',
                (question_text, prompt_template, prompt_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Промпт с ID {prompt_id} не найден")

    def delete_prompt(self, prompt_id):
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Prompts WHERE question_id = ?', (prompt_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise ValueError(f"Промпт с ID {prompt_id} не найден")

    def get_all_users(self):
        """Получение списка всех пользователей с их статистикой"""
        try:
            with self.get_db() as conn:
                cursor = conn.cursor()
                query = """
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
                ORDER BY last_activity DESC
                """
                cursor.execute(query)
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
                return users
        except sqlite3.Error as e:
            print(f"Ошибка при получении пользователей: {e}")
            return []

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
