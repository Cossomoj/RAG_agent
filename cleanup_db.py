#!/usr/bin/env python3
import sqlite3

def cleanup_database():
    print("🔄 Подключаемся к базе данных...")
    conn = sqlite3.connect("/app/src/main_version/AI_agent.db")
    cursor = conn.cursor()

    # Показываем количество пользователей до очистки
    cursor.execute("SELECT COUNT(*) FROM Users")
    initial_count = cursor.fetchone()[0]
    print(f"📊 Пользователей до очистки: {initial_count}")

    # Удаляем пользователей
    print("🗑️ Удаляем пользователей...")
    cursor.execute("DELETE FROM Users WHERE user_id != 999999999")
    users_deleted = cursor.rowcount
    print(f"👥 Удалено пользователей: {users_deleted}")

    # Удаляем историю сообщений
    print("💬 Удаляем историю сообщений...")
    cursor.execute("DELETE FROM Message_history WHERE user_id != 999999999")
    messages_deleted = cursor.rowcount
    print(f"📝 Удалено записей истории: {messages_deleted}")

    # Удаляем напоминания
    print("🔔 Удаляем напоминания...")
    cursor.execute("DELETE FROM Reminder WHERE user_id != 999999999")
    reminders_deleted = cursor.rowcount
    print(f"⏰ Удалено напоминаний: {reminders_deleted}")

    # Сохраняем изменения
    conn.commit()

    # Проверяем результат
    cursor.execute("SELECT COUNT(*) FROM Users")
    remaining_count = cursor.fetchone()[0]
    print(f"✅ Осталось пользователей: {remaining_count}")

    if remaining_count == 1:
        cursor.execute("SELECT user_id, username, user_fullname FROM Users")
        user = cursor.fetchone()
        print(f"👤 Оставшийся пользователь: ID={user[0]}, Username={user[1]}, Fullname={user[2]}")
    elif remaining_count == 0:
        print("❌ ОШИБКА: Не осталось ни одного пользователя!")
    elif remaining_count > 1:
        print(f"⚠️ ВНИМАНИЕ: Осталось {remaining_count} пользователей вместо одного!")

    conn.close()
    print("🎉 Очистка завершена!")

if __name__ == "__main__":
    cleanup_database() 