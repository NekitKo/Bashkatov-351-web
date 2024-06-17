from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix='/auth')

def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Нужна аутентифицакия для доступа на страницу'
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)
    login_manager.init_app(app)

def load_user(id_user):
    user = db.session.execute(db.select(User).filter_by(id=id_user)).scalar()
    return user
                                                            
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        if login and password:
            user = db.session.execute(db.select(User).filter_by(login=login)).scalar()
            if user and user.check_password(password):
                login_user(user)
                flash('Успешный вход в аккаунт', 'success')
                next = request.args.get('next')
                return redirect(next or url_for('index'))
        flash('Введен неверный логин и/или пароль', 'danger')
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def check_rights(action):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Чтобы это сделать, вам нужно войти в аккаунт", "warning")
                return redirect(url_for("login"))
            if current_user.can(action):
                return func(*args, **kwargs)
            else:
                flash("На это у вас нет прав;)", "danger")
                return redirect(url_for("index"))
        return wrapper
    return decorator
