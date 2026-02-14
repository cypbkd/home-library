
import pytest
from flask import url_for
from book_library_app.models import Book, UserBook, User # Changed back to absolute import
from book_library_app.tests.test_authentication import register_user, login_user # Corrected import

def add_book(client, title, author, isbn):
    return client.post(
        '/add_book',
        data=dict(title=title, author=author, isbn=isbn),
        follow_redirects=True
    )

def test_add_book_page_requires_login(test_client):
    response = test_client.get('/add_book', follow_redirects=True)
    assert b'Please log in to access this page.' in response.data


def test_add_new_book(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    login_user(test_client, 'test@example.com', 'testpassword')
    response = add_book(test_client, 'Test Book', 'Test Author', '1234567890123')
    assert b'added to your library!' in response.data # Corrected assertion
    with test_client.application.app_context():
        book = Book.query.filter_by(isbn='1234567890123').first()
        assert book is not None
        assert book.title == 'Test Book'


def test_add_duplicate_isbn(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    login_user(test_client, 'test@example.com', 'testpassword')
    add_book(test_client, 'Test Book 1', 'Test Author', '1234567890123')
    response = add_book(test_client, 'Test Book 2', 'Another Author', '1234567890123')
    assert b'You have already added this book to your library.' in response.data


def test_books_page(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    login_user(test_client, 'test@example.com', 'testpassword')
    add_book(test_client, 'Test Book', 'Test Author', '1234567890123')
    response = test_client.get('/books')
    assert response.status_code == 200
    assert b'Test Book' in response.data
    assert b'Test Author' in response.data


def test_edit_book_details(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    login_user(test_client, 'test@example.com', 'testpassword')
    add_book(test_client, 'Original Title', 'Original Author', '1112223334445')

    with test_client.application.app_context():
        book_to_edit = Book.query.filter_by(isbn='1112223334445').first()
        user = User.query.filter_by(email='test@example.com').first()
        user_book_to_edit = UserBook.query.filter_by(user_id=user.id, book_id=book_to_edit.id).first()
        assert user_book_to_edit is not None
        edit_response = test_client.post(
            f'/edit_book/{user_book_to_edit.id}',
            data=dict(title='Edited Title', author='Edited Author', isbn='1112223334445', status='read', rating=5),
            follow_redirects=True
        )
        assert b'Your book has been updated!' in edit_response.data

        updated_book = Book.query.filter_by(id=book_to_edit.id).first()
        assert updated_book.title == 'Edited Title'
        assert updated_book.author == 'Edited Author'

        updated_user_book = UserBook.query.filter_by(id=user_book_to_edit.id).first()
        assert updated_user_book.status == 'read'
        assert updated_user_book.rating == 5


def test_delete_book(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    login_user(test_client, 'test@example.com', 'testpassword')
    add_book(test_client, 'Book to Delete', 'Author to Delete', '9998887776665')

    with test_client.application.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        book_to_delete = Book.query.filter_by(isbn='9998887776665').first()
        user_book_to_delete = UserBook.query.filter_by(user_id=user.id, book_id=book_to_delete.id).first()
        assert user_book_to_delete is not None
        delete_response = test_client.post(
            f'/delete_book/{user_book_to_delete.id}',
            follow_redirects=True
        )
        assert b'Book deleted successfully!' in delete_response.data

        deleted_user_book = UserBook.query.filter_by(id=user_book_to_delete.id).first()
        assert deleted_user_book is None

        # Ensure the Book entry itself is NOT deleted if other users have it
        # For this test, since only one user, it would be deleted if not careful
        # For now, just assert the UserBook link is gone.


def test_user_book_sync_status(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    login_user(test_client, 'test@example.com', 'testpassword')
    add_book(test_client, 'Sync Test Book', 'Sync Author', '1231231231231')

    with test_client.application.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        book = Book.query.filter_by(isbn='1231231231231').first()
        user_book = UserBook.query.filter_by(user_id=user.id, book_id=book.id).first()
        assert user_book is not None
        assert user_book.sync_status == 'PENDING_SYNC' # Default status set in models.py

        # Simulate sync status update via manual update route
        edit_response = test_client.post(
            f'/manual_update_book/{user_book.id}',
            data=dict(title='Sync Test Book', author='Sync Author', genre='', description='', cover_image_url='', status='read', rating=4),
            follow_redirects=True
        )
        assert b'Book details updated successfully!' in edit_response.data

        updated_user_book = UserBook.query.filter_by(user_id=user.id, book_id=book.id).first()
        assert updated_user_book.sync_status == 'SYNCED'
