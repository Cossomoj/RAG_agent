def add_prompt():
    required_fields = ['question_id']  # добавьте другие обязательные поля
    
    for field in required_fields:
        if field not in request.form or not request.form[field].strip():
            return f"Ошибка: поле '{field}' обязательно для заполнения", 400
    
    question_id = request.form['question_id']
    
    if not question_id:
        return "Ошибка: question_id не предоставлен", 400 