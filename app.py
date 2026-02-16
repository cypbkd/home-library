from flask import Flask, render_template, request, url_for, flash, redirect, session, jsonify, current_app
from flask_login import login_user, current_user, logout_user, login_required, UserMixin # Import necessary Flask-Login functions
from flask_migrate import Migrate
from config import Config
from datetime import datetime
import os
import base64
from io import BytesIO
try:
    from PIL import Image
    from pyzbar.pyzbar import decode
except ImportError:  # Optional in local/test environments without native zbar
    Image = None
    decode = None
import threading
from tasks import fetch_book_metadata
from extensions import db, login_manager # Import db and login_manager from extensions
from models import User, Book, UserBook # Import models after db and login_manager are initialized
from werkzeug.security import generate_password_hash, check_password_hash # Import for User model methods

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app) # Initialize db with the app
    migrate = Migrate(app, db)
    login_manager.init_app(app) # Initialize login_manager with the app
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.route("/")
    @app.route("/home")
    def home():
        return render_template('home.html', title='Home')

    @app.route("/register", methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if password != confirm_password:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('register'))

            user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
            if user_exists:
                flash('Username or Email already exists. Please choose a different one.', 'danger')
                return redirect(url_for('register'))

            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', title='Register')

    @app.route("/login", methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                flash('Login successful.', 'success')
                return redirect(next_page or url_for('home'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        return render_template('login.html', title='Login')

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('home'))

    @app.route("/books")
    @login_required
    def books():
        user_books = UserBook.query.filter_by(user_id=current_user.id).all()
        return render_template('books.html', title='My Books', books=user_books)

    @app.route("/add_book", methods=['GET', 'POST'])
    @login_required
    def add_book():
        if request.method == 'POST':
            isbn = request.form['isbn']
            title = request.form['title']
            author = request.form['author']
            genre = request.form.get('genre')
            cover_image_url = request.form.get('cover_image_url')
            description = request.form.get('description')
            status = request.form.get('status', 'to-read')
            rating = request.form.get('rating')

            book = Book.query.filter_by(isbn=isbn).first()
            if not book:
                book = Book(isbn=isbn, title=title, author=author, genre=genre,
                            cover_image_url=cover_image_url, description=description)
                db.session.add(book)
                db.session.commit()

            user_book_exists = UserBook.query.filter_by(user_id=current_user.id, book_id=book.id).first()
            if user_book_exists:
                flash('You have already added this book to your library.', 'warning')
                return redirect(url_for('books'))

            new_user_book = UserBook(user_id=current_user.id, book_id=book.id, status=status, sync_status='PENDING_SYNC')
            if rating:
                new_user_book.rating = int(rating)
            db.session.add(new_user_book)
            db.session.commit()

            if not current_app.config.get('TESTING'):
                thread = threading.Thread(target=fetch_book_metadata, args=(current_app._get_current_object(), new_user_book.id))
                thread.daemon = True
                thread.start()

            flash(f'Book "{title}" added to your library! Metadata will be fetched in the background.', 'success')
            return redirect(url_for('books'))
        return render_template('add_book.html', title='Add Book')

    @app.route("/manual_update_book/<int:user_book_id>", methods=['POST'])
    @login_required
    def manual_update_book(user_book_id):
        user_book = UserBook.query.get_or_404(user_book_id)
        if user_book.user_id != current_user.id:
            flash('You are not authorized to edit this book.', 'danger')
            return redirect(url_for('books'))

        book = Book.query.get_or_404(user_book.book_id)

        book.title = request.form['title']
        book.author = request.form['author']
        book.genre = request.form.get('genre')
        book.description = request.form.get('description')
        book.cover_image_url = request.form.get('cover_image_url')

        user_book.status = request.form.get('status')
        rating = request.form.get('rating')
        user_book.rating = int(rating) if rating else None
        user_book.sync_status = 'SYNCED' # Manually updated, so set to SYNCED

        db.session.commit()
        flash('Book details updated successfully!', 'success')
        return redirect(url_for('books'))

    @app.route("/edit_book/<int:user_book_id>", methods=['GET', 'POST'])
    @login_required
    def edit_book(user_book_id):
        user_book = UserBook.query.get_or_404(user_book_id)
        if user_book.user_id != current_user.id:
            flash('You are not authorized to edit this book.', 'danger')
            return redirect(url_for('books'))

        book = Book.query.get_or_404(user_book.book_id)

        if request.method == 'POST':
            book.title = request.form['title']
            book.author = request.form['author']
            book.genre = request.form.get('genre')
            book.description = request.form.get('description')
            book.cover_image_url = request.form.get('cover_image_url')

            user_book.status = request.form.get('status')
            rating = request.form.get('rating')
            user_book.rating = int(rating) if rating else None
            user_book.sync_status = 'SYNCED' # Assuming manual edit makes it synced

            db.session.commit()
            flash('Your book has been updated!', 'success')
            return redirect(url_for('books'))

        return render_template('edit_book.html', title='Edit Book', user_book=user_book, book=book)

    @app.route("/delete_book/<int:user_book_id>", methods=['POST'])
    @login_required
    def delete_book(user_book_id):
        user_book = UserBook.query.get_or_404(user_book_id)
        if user_book.user_id != current_user.id:
            flash('You are not authorized to delete this book.', 'danger')
            return redirect(url_for('books'))
        
        db.session.delete(user_book)
        db.session.commit()
        flash('Book deleted successfully!', 'success')
        return redirect(url_for('books'))

    @app.route('/scan_isbn', methods=['POST'])
    @login_required # Ensure user is logged in to add books
    def scan_isbn():
        if Image is None or decode is None:
            return jsonify({'success': False, 'message': 'Barcode scanning dependencies are not installed.'}), 503

        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'success': False, 'message': 'No image data provided.'}), 400

        image_data = data['image']
        if ';base64,' in image_data:
            header, encoded = image_data.split(';base64,', 1)
        else:
            encoded = image_data

        try:
            decoded_image = base64.b64decode(encoded)
            image = Image.open(BytesIO(decoded_image))
            if image.mode != 'L':
                image = image.convert('L')
            barcodes = decode(image)

            for barcode in barcodes:
                try:
                    isbn = barcode.data.decode('utf-8')
                    isbn = isbn.replace('-', '')
                    if (len(isbn) == 10 and isbn.isdigit()) or \
                       (len(isbn) == 13 and isbn.isdigit()):

                        book = Book.query.filter_by(isbn=isbn).first()
                        if not book:
                            # Create a placeholder book if not found, metadata will be fetched later
                            book = Book(isbn=isbn, title='Fetching Title...', author='Fetching Author...')
                            db.session.add(book)
                            db.session.commit()

                        user_book = UserBook.query.filter_by(user_id=current_user.id, book_id=book.id).first()
                        if user_book:
                            return jsonify({'success': False, 'message': 'Book already in your library.', 'isbn': isbn}), 409

                        new_user_book = UserBook(user_id=current_user.id, book_id=book.id, status='to-read', sync_status='PENDING_SYNC')
                        db.session.add(new_user_book)
                        db.session.commit()

                        # Start background task to fetch metadata
                        if not current_app.config.get('TESTING'):
                            thread = threading.Thread(target=fetch_book_metadata, args=(current_app._get_current_object(), new_user_book.id))
                            thread.daemon = True
                            thread.start()

                        return jsonify({'success': True, 'isbn': isbn, 'message': 'Book added. Fetching metadata...'})
                except UnicodeDecodeError:
                    print(f"Could not decode barcode data: {barcode.data}")
                    continue

            return jsonify({'success': False, 'message': 'No valid ISBN barcode found.'}), 404

        except Exception as e:
            print(f"Error processing image for ISBN: {e}")
            return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
