from extension import db
from flask_login import UserMixin

user_books = db.Table('user_books',
    db.Column('user_id', db.Integer, db.ForeignKey('registered_users.id')),
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'))
)


class Books(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    download_count = db.Column(db.String(255), default=0)
    book_img = db.Column(db.String(255), nullable=False)

class Registered_Users(db.Model, UserMixin):
    __tablename__ = 'registered_users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    saved_books = db.relationship('Books', secondary=user_books, backref='users')
