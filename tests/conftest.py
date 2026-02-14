
import pytest
from book_library_app.app import create_app
from book_library_app.extensions import db
from book_library_app.models import User, Book, UserBook
from book_library_app.config import TestConfig

@pytest.fixture(scope='module')
def test_app():
    app = create_app(config_class=TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    return test_app.test_client()

@pytest.fixture(scope='function')
def init_database(test_app):
    with test_app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def new_user():
    user = User(username='testuser', email='test@example.com')
    user.set_password('testpassword')
    return user

@pytest.fixture(scope='function')
def new_book():
    book = Book(title='Test Book', author='Test Author', isbn='1234567890123')
    return book
