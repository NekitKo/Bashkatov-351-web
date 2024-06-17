from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from app import db
from check_user import CheckUser
from functools import wraps

bp_auth = Blueprint('auth', __name__, url_prefix='/auth')

ID_ADMIN = 1

def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Для доступа необходимо аутентифицироваться'
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)


def check_rights(action):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = None
            if kwargs.get('id_user'):
                id_user = kwargs['id_user']
                user = load_user(id_user)
            if current_user.can(action, user):
                return func(*args, **kwargs)
            else:
                flash("У вас недостаточно прав, советую хотя бы аутентифицироваться", "danger")
                return redirect(url_for('index'))
        return wrapper
    return decorator


class User(UserMixin):
    def __init__(self, id_user, user_login, id_role):
        self.id = id_user
        self.login = user_login
        self.id_role = id_role
    def is_admin(self):
        return self.id_role == ID_ADMIN
    def can(self, action, record = None):
        check_user = CheckUser(record)
        method = getattr(check_user, action, None)
        if method:
            return method()
        return False


def load_user(id_user):
    query = 'SELECT * FROM users WHERE users.id=%s'
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query, (id_user,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(user.id, user.login, user.id_role)
    return None

@bp_auth.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        check = request.form.get('secretcheck') == 'on'
        query = 'SELECT * FROM users WHERE users.login=%s AND users.password_hash=SHA2(%s,256)'
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(query, (login, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            login_user(User(user.id, user.login, user.id_role), remember=check)
            param_url = request.args.get('next')
            flash('Вы успешно вошли!', 'success')
            return redirect(param_url or url_for('index'))
        flash('Ошибка входа!', 'danger')
    return render_template('login.html' )

@bp_auth.route('/logout', methods = ['GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))