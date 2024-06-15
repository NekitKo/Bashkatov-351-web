from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, ForeignKey, DateTime, Text, Integer, MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql.types import YEAR
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

ID_ADMIN = 1
ID_MODERATOR = 2

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })


db = SQLAlchemy(model_class=Base)


class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

class User(Base, UserMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    last_name: Mapped[str] = mapped_column(String(256), nullable=False)
    first_name: Mapped[str] = mapped_column(String(256), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(256), nullable=True)
    id_roles: Mapped[int] = mapped_column(Integer, ForeignKey('roles.id'))

    def administrator(self) -> bool:
        return self.id_roles == ID_ADMIN

    def moderator(self) -> bool:
        return self.id_roles == ID_MODERATOR

    def capability(self, action: str) -> bool:
        if self.id_roles:
            if action == 'create':
                return self.administrator()
            elif action == 'edit':
                return self.administrator() or self.moderator()
            elif action == 'delete':
                return self.administrator()
            elif action == 'show':
                return True
        return False

    @property 
    def full_name(self): 
        return ' '.join([self.last_name, self.first_name, self.middle_name or '']) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Book(Base): 
    __tablename__ = 'books'

    id = mapped_column(Integer, primary_key=True) 
    name: Mapped[str] = mapped_column(String(100), nullable=False) 
    short_description: Mapped[str] = mapped_column(Text, nullable=False) 
    year_of_creation: Mapped[int] = mapped_column(YEAR, nullable=False)
    publish_company: Mapped[str] = mapped_column(String(100), nullable=False) 
    author: Mapped[str] = mapped_column(String(100), nullable=False) 
    page_amount: Mapped[int] = mapped_column(nullable=False) 
    rating_sum: Mapped[int] = mapped_column(default=0) 
    amount_of_rates: Mapped[int] = mapped_column(default=0) 
    id_cover: Mapped[int] = mapped_column(String(256), ForeignKey("covering.id", ondelete="RESTRICT")) 
 
    @property 
    def rating(self): 
        if self.amount_of_rates > 0: 
            return self.rating_sum / self.amount_of_rates 
        return 0

class Genre(Base):
    __tablename__ = 'genres'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)

class GenresofBooks(Base):
    __tablename__ = 'genresofbooks'

    id_book: Mapped[int] = mapped_column(Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    id_genre: Mapped[int] = mapped_column(Integer, ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True, nullable=False)


class Cover(Base):
    __tablename__ = 'covering'

    id: Mapped[int] = mapped_column(String(256), primary_key=True)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    file_type: Mapped[str] = mapped_column(String(256), nullable=False)
    md5_hash: Mapped[str] = mapped_column(String(256), nullable=False)


class Feedback(Base):
    __tablename__ = 'feedback'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_book: Mapped[int] = mapped_column(Integer, ForeignKey('books.id'), nullable=False)
    id_user: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    add_date: Mapped[datetime] = mapped_column(DateTime, default=db.func.current_timestamp(), nullable=False)



