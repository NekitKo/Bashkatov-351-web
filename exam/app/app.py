from flask import Flask, render_template, send_from_directory
from flask_migrate import Migrate
from auth import bp as auth_bp, init_login_manager
from book import bp as book_bp
from models import db, Genre, Book, Cover
from tools import FilterofBooks


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
    genres = db.session.execute(db.select(Genre)).scalars().all()
    books = db.session.execute(db.select(Book)).scalars().all()
    books = FilterofBooks().perform()
    pagination = db.paginate(books, per_page=10)
    books = pagination.items
    return render_template(
        'index.html',
        genres=genres,
        books=books,
        pagination=pagination
    )

@app.route('/images/<id_cover>')
def cover(id_cover):
    img = db.get_or_404(Cover, id_cover)
    return send_from_directory(app.config['UPLOAD_FOLDER'], img.filename)