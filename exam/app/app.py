from flask import Flask, render_template, send_from_directory, redirect, url_for, flash, request
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
from auth import bp as auth_bp, init_login_manager
from book import bp as book_bp
from models import db, Genre, Book, GenresofBooks
from tools import FilterofBooks
from flask_login import login_required, current_user, AnonymousUserMixin, LoginManager, login_user, logout_user
from models import Book
from tools import SaveCover
from models import db, User

app = Flask(__name__)
application = app
app.config.from_pyfile('config.py')

db.init_app(app)
migrate = Migrate(app, db)

init_login_manager(app)


app.register_blueprint(auth_bp)
app.register_blueprint(book_bp)


@app.route('/')
def index():
    genres = db.session.execute(db.select(Genre)).scalars()
    book = db.session.execute(db.select(Book)).scalars()
    return render_template(
        'index.html',
        genres=genres,
        books=book
    )

@app.route('/books')
def books():
    genres = db.session.execute(db.select(Genre)).scalars()
    return render_template(
        'book/books.html',
        genres=genres
        )

@app.route('/create', methods=['POST'])
@login_required
def create():
    return 0

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        if login and password:
            user = db.session.execute(db.select(User).filter_by(login=login)).scalar()
            if user and user.check_password(password):
                login_user(user)
                flash('Аутентификация прошла успешно', 'success')
                next = request.args.get('next')
                return redirect(next or url_for('index'))
        flash('Введен неверный логин или пароль', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))