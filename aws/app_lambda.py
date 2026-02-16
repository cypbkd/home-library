"""
Flask application adapted for AWS Lambda with DynamoDB.
This is the main application file for serverless deployment.
"""
from flask import Flask, render_template, request, url_for, flash, redirect, session, jsonify
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin
import os
import base64
# from io import BytesIO
# from PIL import Image
# from pyzbar.pyzbar import decode
from datetime import datetime, timezone
import json
from decimal import Decimal

# Import DynamoDB models
from dynamodb_models import DynamoDBUser, DynamoDBBook, DynamoDBUserBook
from tasks_lambda import fetch_book_metadata_async

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True only if using custom domain with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    """Flask-Login User wrapper for DynamoDB user"""
    def __init__(self, user_data):
        self.id = user_data['user_id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.user_data = user_data


@login_manager.user_loader
def load_user(user_id):
    """Load user from DynamoDB"""
    print(f"[DEBUG] load_user called with user_id: {user_id}")
    print(f"[DEBUG] USERS_TABLE env: {os.environ.get('USERS_TABLE')}")
    user_data = DynamoDBUser.get_by_id(user_id)
    print(f"[DEBUG] User data retrieved: {user_data is not None}")
    if user_data:
        return User(user_data)
    return None


# Helper function to convert Decimal to int/float for JSON serialization
def decimal_to_number(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


@app.route("/")
@app.route("/home")
def home():
    from flask import request as flask_request
    print(f"[DEBUG] Home route - current_user.is_authenticated: {current_user.is_authenticated}")
    print(f"[DEBUG] Session contents: {dict(session)}")
    print(f"[DEBUG] Request cookies: {flask_request.cookies}")
    print(f"[DEBUG] Request headers Cookie: {flask_request.headers.get('Cookie', 'NO COOKIE')}")
    if current_user.is_authenticated:
        print(f"[DEBUG] User ID: {current_user.id}")
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

        # Check if user exists
        if DynamoDBUser.get_by_email(email) or DynamoDBUser.get_by_username(username):
            flash('Username or Email already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # Create user
        user_data = DynamoDBUser.create(username, email, password)
        if user_data:
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error creating account. Please try again.', 'danger')
    
    return render_template('register.html', title='Register')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user_data = DynamoDBUser.get_by_email(email)
        if user_data and DynamoDBUser.check_password(user_data, password):
            user = User(user_data)
            login_user(user)
            print(f"[DEBUG] User logged in: {user.id}")
            print(f"[DEBUG] Session after login: {dict(session)}")
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
    # Get all user books
    user_books_data = DynamoDBUserBook.get_user_books(current_user.id)
    
    # Enrich with book details
    user_books = []
    for ub in user_books_data:
        book_data = DynamoDBBook.get_by_id(ub['book_id'])
        if book_data:
            # Create a combined object for template
            combined = {
                'id': ub['user_book_id'],
                'user_id': ub['user_id'],
                'book_id': ub['book_id'],
                'status': ub['status'],
                'rating': decimal_to_number(ub.get('rating')),
                'sync_status': ub['sync_status'],
                'date_added': ub['date_added'],
                'book_item': book_data
            }
            user_books.append(combined)
    
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

        # Get or create book
        book = DynamoDBBook.get_by_isbn(isbn)
        if not book:
            book = DynamoDBBook.create(isbn, title, author, genre, cover_image_url, description)

        # Check if user already has this book
        existing = DynamoDBUserBook.get(current_user.id, book['book_id'])
        if existing:
            flash('You have already added this book to your library.', 'warning')
            return redirect(url_for('books'))

        # Create user-book relationship
        rating_int = int(rating) if rating else None
        user_book = DynamoDBUserBook.create(
            current_user.id, 
            book['book_id'], 
            status, 
            rating_int, 
            'PENDING'
        )

        if user_book:
            # Trigger async metadata fetch
            fetch_book_metadata_async(user_book['user_book_id'])
            flash(f'Book "{title}" added to your library! Metadata will be fetched in the background.', 'success')
        else:
            flash('Error adding book to library.', 'danger')
        
        return redirect(url_for('books'))
    
    return render_template('add_book.html', title='Add Book')


@app.route("/edit_book/<string:user_book_id>", methods=['GET', 'POST'])
@login_required
def edit_book(user_book_id):
    user_book = DynamoDBUserBook.get_by_id(user_book_id)
    
    if not user_book or user_book['user_id'] != current_user.id:
        flash('You are not authorized to edit this book.', 'danger')
        return redirect(url_for('books'))

    book = DynamoDBBook.get_by_id(user_book['book_id'])

    if request.method == 'POST':
        # Update book details
        DynamoDBBook.update(
            book['book_id'],
            title=request.form['title'],
            author=request.form['author'],
            genre=request.form.get('genre'),
            description=request.form.get('description'),
            cover_image_url=request.form.get('cover_image_url')
        )

        # Update user-book relationship
        rating = request.form.get('rating')
        DynamoDBUserBook.update(
            user_book_id,
            status=request.form.get('status'),
            rating=int(rating) if rating else None,
            sync_status='SYNCED'
        )

        flash('Your book has been updated!', 'success')
        return redirect(url_for('books'))

    # Convert Decimal to int for template
    user_book['rating'] = decimal_to_number(user_book.get('rating'))
    
    return render_template('edit_book.html', title='Edit Book', user_book=user_book, book=book)


@app.route("/delete_book/<string:user_book_id>", methods=['POST'])
@login_required
def delete_book(user_book_id):
    user_book = DynamoDBUserBook.get_by_id(user_book_id)
    
    if not user_book or user_book['user_id'] != current_user.id:
        flash('You are not authorized to delete this book.', 'danger')
        return redirect(url_for('books'))
    
    DynamoDBUserBook.delete(user_book_id)
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('books'))


@app.route('/scan_isbn', methods=['POST'])
@login_required
def scan_isbn():
    # Barcode scanning temporarily disabled - requires Pillow compiled for Lambda
    return jsonify({'success': False, 'message': 'Barcode scanning not available in Lambda deployment yet'}), 501


# Health check endpoint
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # For local testing only
    app.run(debug=True)
