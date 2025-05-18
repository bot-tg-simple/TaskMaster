from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from models import db, User, Task, Subtask
from alice import alice
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Регистрируем blueprint для Алисы
app.register_blueprint(alice)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Главная страница, редирект на дашборд если пользователь авторизован
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

#Страница регистрации нового пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        session.pop('_flashes', None)
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'error')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Регистрация успешна! Добро пожаловать в TaskMaster', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('register.html')

#Страница входа в систему
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session.pop('_flashes', None)
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
            
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

#Выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

#Личный кабинет пользователя со списком всех задач
@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    return render_template('dashboard.html', tasks=tasks, now=datetime.now())

#Создание новой задачи
@app.route('/task/new', methods=['GET', 'POST'])
@login_required
def new_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        deadline = request.form.get('deadline')
        priority = request.form.get('priority')
        category = request.form.get('category')
        
        task = Task(
            title=title,
            description=description,
            deadline=datetime.strptime(deadline, '%Y-%m-%d') if deadline else None,
            priority=priority,
            category=category,
            user_id=current_user.id
        )
        
        db.session.add(task)
        db.session.commit()
        
        return redirect(url_for('dashboard'))
        
    return render_template('new_task.html')

#Просмотр детальной информации о задаче
@app.route('/task/<int:task_id>')
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return redirect(url_for('dashboard'))
    return render_template('view_task.html', task=task)

#Редактирование существующей задачи
@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        deadline = request.form.get('deadline')
        task.deadline = datetime.strptime(deadline, '%Y-%m-%d') if deadline else None
        task.priority = request.form.get('priority')
        task.category = request.form.get('category')
        task.status = request.form.get('status')
        
        db.session.commit()
        return redirect(url_for('view_task', task_id=task.id))
        
    return render_template('edit_task.html', task=task, now=datetime.now().strftime('%Y-%m-%d'))

#Удаление задачи
@app.route('/task/<int:task_id>/delete')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return redirect(url_for('dashboard'))
        
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('dashboard'))

#Добавление подзадачи к существующей задаче
@app.route('/task/<int:task_id>/subtask/add', methods=['POST'])
@login_required
def add_subtask(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    
    title = request.form.get('title')
    if title:
        subtask = Subtask(title=title, task_id=task_id)
        db.session.add(subtask)
        db.session.commit()
        flash('Подзадача добавлена', 'success')
    
    return redirect(url_for('edit_task', task_id=task_id))

#Удаление подзадачи
@app.route('/subtask/<int:subtask_id>/delete', methods=['POST'])
@login_required
def delete_subtask(subtask_id):
    subtask = Subtask.query.get_or_404(subtask_id)
    task = Task.query.get_or_404(subtask.task_id)
    
    if task.user_id != current_user.id:
        abort(403)
    
    db.session.delete(subtask)
    db.session.commit()
    flash('Подзадача удалена', 'success')
    
    return redirect(url_for('edit_task', task_id=task.task_id))

#Отметка подзадачи как выполненной/невыполненной
@app.route('/subtask/<int:subtask_id>/toggle')
@login_required
def toggle_subtask(subtask_id):
    subtask = Subtask.query.get_or_404(subtask_id)
    if subtask.task.user_id != current_user.id:
        return redirect(url_for('dashboard'))
        
    subtask.completed = not subtask.completed
    db.session.commit()
    return redirect(url_for('view_task', task_id=subtask.task_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
