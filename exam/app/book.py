from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from models import db, Genre, GenresofBooks,Feedback, Book, Cover
from tools import SaveCover
import bleach

bp = Blueprint('book', __name__, url_prefix='/book')


@bp.route('/new')
def new():
    genres = db.session.execute(db.select(Genre)).scalars()
    return render_template(
        'book/new.html',
        genres=genres
        )

@bp.route('/<int:id_book>/feedback')
def feedback(id_book):
    book = db.session.query(Book).get_or_404(id_book)
    genres = db.session.query(Genre).join(GenresofBooks).filter(GenresofBooks.id_book == book.id).all()
    feedback = db.session.query(Feedback).filter_by(id_book=id_book, id_user=current_user.id).first()
    feedbacks = db.session.query(Feedback).filter_by(id_book=id_book).order_by(Feedback.add_date.desc()).all()
    return render_template('book/feedback.html', book=book, genres=genres, feedback = feedback, feedbacks=feedbacks)

@bp.route('/create', methods=['POST'])
@login_required
def create():  
    if request.method == "POST":
        name = request.form['name']
        author = request.form['author']
        year_of_creation = request.form['created']
        publish_company = request.form['publish_company']
        page_amount = int(request.form['pagescount'])
        short_description = bleach.clean(request.form['short_description'])
        genres = request.form.getlist('genres')
        background_img = request.files['background_img']
        try:     
            save_cover = SaveCover(background_img)
            cover = save_cover.save()
            
            book = Book(
                name=name,
                author=author,
                year_of_creation=year_of_creation,
                publish_company=publish_company,
                page_amount=page_amount,
                short_description=short_description,
                id_cover=cover.id
            )
            db.session.add(book)
            db.session.flush()
            
            if not genres:
                flash('Выберите жанр', 'warning')
                return render_template('new.html', genres=db.session.query(Genre).all())
            
            for id_genre in genres:
                genre = db.session.query(Genre).get(id_genre)
                if genre:
                    genresofBooks = GenresofBooks(
                        id_book=book.id,
                        id_genre=id_genre
                    )
                db.session.add(genresofBooks)
            
            db.session.commit()
            flash('Книга успешно добавлена', 'success')
            return redirect(url_for('index'))
        
        except Exception as err:
            db.session.rollback()
            flash(f'Ошибка добавления книги в базу: {err}', 'danger')
            return render_template('book/new.html', genres=db.session.query(Genre).all())

@bp.route('/show/<int:id_book>', methods=['GET', 'POST'])
@login_required
def show(id_book):   
    book = db.session.query(Book).get_or_404(id_book)
    genres = db.session.query(Genre).join(GenresofBooks).filter(GenresofBooks.id_book == book.id).all()
    feedback = db.session.query(Feedback).filter_by(id_book=id_book, id_user=current_user.id).first()
    feedbacks = db.session.query(Feedback).filter_by(id_book=id_book).order_by(Feedback.add_date.desc()).all()

    return render_template('book/show.html', book=book, genres=genres, feedback = feedback, feedbacks=feedbacks)


@bp.route('/images/<id_cover>')
def cover(id_cover):
    img = db.get_or_404(Cover, id_cover)
    return send_from_directory(bp.config['UPLOAD_FOLDER'], img.filename)

@bp.route('/<int:id_book>', methods=['POST'])
@login_required
def add_review(id_book):
    text = bleach.clean(request.form["reviewBody"])
    rating = int(request.form["rating"])
    try:
        feedback = Feedback(
            rating=rating,
            text=text, 
            id_book=id_book, 
            id_user=current_user.id
            )

        book = db.get_or_404(Book, id_book)
        book.rating_sum += rating
        book.amount_of_rates += 1
        db.session.add(feedback)
        db.session.commit()
    except Exception as err:
        flash(f'Возникла ошибка при записи информации в базу данных. Пожалуйста, проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
    return redirect(url_for('book.show', id_book=book.id))


@bp.route('/edit/<int:id_book>', methods=["GET", "POST"])
@login_required
def edit(id_book):
    book = db.session.query(Book).get_or_404(id_book)
    commongenres = db.session.query(Genre).all()
    
    if request.method == "POST":
        try:
            book.name = request.form['name']
            book.author = request.form['author']
            book.year_of_creation = request.form['created']
            book.publish_company = request.form['publish_company']
            book.page_amount = int(request.form['pagescount'])
            book.short_description = bleach.clean(request.form['short_description'])
            genres = request.form.getlist('genres')
            db.session.query(GenresofBooks).filter_by(id_book=book.id).delete()

            if not genres:
                flash('Выберите жанр', 'warning')
                return render_template('edit.html', genres=db.session.query(Genre).all())
            
            for id_genre in genres:
                genre = db.session.query(Genre).get(id_genre)
                if genre:
                    genresofBooks = GenresofBooks(
                        id_book=book.id,
                        id_genre=id_genre
                    )
                db.session.add(genresofBooks)
            
            db.session.commit()
            flash('Книга успешно добавлена', 'success')
            return redirect(url_for('index'))
        
        except Exception as err:
            db.session.rollback()
            flash(f'Ошибка редактирования книги: {err}', 'danger')
            return render_template('book/edit.html', book=book, genres=commongenres)
    
    return render_template('book/edit.html', book=book, genres=commongenres)

@bp.route('/<int:id_book>/delete', methods=["GET", "POST"])
@login_required
def delete(id_book):
    book = db.session.execute(db.select(Book).filter_by(id=id_book)).scalars().first()
    cover = db.session.execute(db.select(Cover).filter_by(id=book.id_cover)).scalars().first()
    nameofcover = cover.filename
    try:
        db.session.query(Feedback).filter_by(id_book=book.id).delete()
        db.session.delete(book)
        db.session.delete(cover)
        db.session.commit()
        SaveCover.drop_skin(nameofcover)
    except SQLAlchemyError as err:
        flash(f'Ошибка удаление книги: {err}', 'danger')
        return redirect(url_for('index')) 
    
    return redirect(url_for('index'))

