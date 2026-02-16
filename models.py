from datetime import datetime, timezone
from flask_login import UserMixin
from extensions import db # Import db from extensions


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    user_books = db.relationship('UserBook', backref='owner', lazy=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(100), nullable=True)
    cover_image_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    user_books = db.relationship('UserBook', backref='book_item', lazy=True)

    def __repr__(self):
        return f"Book('{self.title}', '{self.author}')"

class UserBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), nullable=False, default='to-read')
    rating = db.Column(db.Integer, nullable=True)
    sync_status = db.Column(db.String(50), nullable=False, default='PENDING_SYNC')

    def __repr__(self):
        return f"UserBook('{self.owner.username}', '{self.book_item.title}', '{self.status}')"