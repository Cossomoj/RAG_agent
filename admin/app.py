from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from functools import wraps
import os
import sys
from datetime import datetime

# Импортируем DatabaseOperations из локального файла
from database import DatabaseOperations
from rag_manager import RAGDocumentManager

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Замените на реальный секретный ключ
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Инициализация базы данных и менеджеров
db = DatabaseOperations()
rag_manager = RAGDocumentManager()

# Добавляем простой маршрут для проверки доступности сервера
@app.route('/ping')
def ping():
    response = Response('pong')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# Фильтр для форматирования даты
@app.template_filter('datetime')
def format_datetime(value):
    if not value:
        return ''
    if isinstance(value, str):
        try:
            # Пытаемся распарсить строку даты
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    try:
        # Если это timestamp
        return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return str(value)

# Декоратор для проверки аутентификации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Маршруты аутентификации
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Здесь должна быть проверка учетных данных
        if username == "admin_tg_bot" and password == "135beton531":  # Замените на реальную проверку
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Неверные учетные данные')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Главная страница
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Маршруты для работы с промптами
@app.route('/prompts')
@login_required
def prompts():
    all_prompts = db.get_all_prompts()
    print("Полученные промпты:", all_prompts)  # Отладочная информация
    if all_prompts is None:
        all_prompts = []  # Если нет промптов, используем пустой список
    return render_template('prompts.html', prompts=all_prompts)

@app.route('/prompts/add', methods=['GET', 'POST'])
@login_required
def add_prompt():
    if request.method == 'POST':
        question_text = request.form['question_text']
        prompt_template = request.form['prompt_template']
        db.add_prompt(question_text, prompt_template)
        flash('Промпт успешно добавлен')
        return redirect(url_for('prompts'))
    return render_template('add_prompt.html')

# Добавляем новые маршруты для промптов
@app.route('/prompts/<int:prompt_id>', methods=['DELETE'])
@login_required
def delete_prompt(prompt_id):
    try:
        db.delete_prompt(prompt_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/prompts/<int:prompt_id>', methods=['GET', 'POST'])
@login_required
def edit_prompt(prompt_id):
    if request.method == 'POST':
        question_text = request.form['question_text']
        prompt_template = request.form['prompt_template']
        try:
            db.update_prompt(prompt_id, question_text, prompt_template)
            flash('Промпт успешно обновлен')
            return redirect(url_for('prompts'))
        except Exception as e:
            flash(f'Ошибка при обновлении промпта: {str(e)}')
            return redirect(url_for('prompts'))
    
    prompt = db.get_prompt(prompt_id)
    if prompt:
        return jsonify(prompt)
    return jsonify({'error': 'Промпт не найден'}), 404

# Маршруты для работы с RAG документами
@app.route('/documents')
@login_required
def documents():
    all_documents = rag_manager.get_all_documents()
    return render_template('documents.html', documents=all_documents)

@app.route('/documents/<pack>/<filename>', methods=['GET'])
@login_required
def get_document(pack, filename):
    try:
        content = rag_manager.get_document_content(filename, pack)
        return content
    except Exception as e:
        return str(e), 404

@app.route('/documents/<pack>/<filename>', methods=['DELETE'])
@login_required
def delete_document(pack, filename):
    try:
        rag_manager.delete_document(filename, pack)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/documents/add', methods=['POST'])
@login_required
def add_document():
    if 'file' not in request.files:
        flash('Не выбран файл')
        return redirect(url_for('documents'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Не выбран файл')
        return redirect(url_for('documents'))
    
    pack_name = request.form.get('pack_name')
    if not pack_name:
        flash('Не выбран пакет')
        return redirect(url_for('documents'))
    
    try:
        content = file.read().decode('utf-8')
        rag_manager.add_document(content, file.filename, pack_name)
        flash('Документ успешно добавлен')
    except Exception as e:
        flash(f'Ошибка при добавлении документа: {str(e)}')
    
    return redirect(url_for('documents'))

# Маршруты для работы с пользователями
@app.route('/users')
@login_required
def users():
    all_users = db.get_all_users()
    return render_template('users.html', users=all_users)

@app.route('/users/<int:user_id>')
@login_required
def user_details(user_id):
    user = db.get_user_details(user_id)
    if user:
        return jsonify(user)
    return jsonify({'error': 'Пользователь не найден'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8002) 