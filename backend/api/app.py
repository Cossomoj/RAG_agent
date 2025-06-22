@app.route('/api/history/<user_id>', methods=['GET'])
def get_history(user_id):
    """Получение истории диалогов пользователя"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Ошибка подключения к БД"}), 500
            
        cursor = conn.cursor()
        cursor.execute(
            """SELECT message, role, time FROM Message_history 
               WHERE user_id = ? 
               ORDER BY time ASC 
               LIMIT 100""",
            (user_id,)
        )
        
        messages = cursor.fetchall()
        conn.close()
        
        # Группируем сообщения в пары (user -> assistant)
        history = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            if msg["role"] == "user":
                question = msg["message"]
                timestamp = msg["time"]
                answer = ""
                # Ищем ближайший следующий ответ ассистента
                j = i + 1
                while j < len(messages):
                    next_msg = messages[j]
                    if next_msg["role"] == "assistant":
                        answer = next_msg["message"]
                        break
                    j += 1
                history.append({
                    "id": len(history),
                    "question": question,
                    "answer": answer,
                    "timestamp": timestamp,
                    "role": "user",
                    "specialization": ""
                })
            i += 1
        return jsonify(history)
        
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        return jsonify({"error": "Ошибка получения истории"}), 500 