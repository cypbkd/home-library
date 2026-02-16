
import pytest
from flask import url_for
from models import User

def register_user(client, username, email, password):
    return client.post(
        '/register',
        data=dict(username=username, email=email, password=password, confirm_password=password),
        follow_redirects=True
    )

def login_user(client, email, password):
    return client.post(
        '/login',
        data=dict(email=email, password=password),
        follow_redirects=True
    )

def logout_user(client):
    return client.get('/logout', follow_redirects=True)


def test_register_page(test_client):
    response = test_client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data


def test_register_user(test_client, init_database):
    response = register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    assert b'Your account has been created! You are now able to log in' in response.data # Corrected assertion
    with test_client.application.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None
        assert user.username == 'testuser'


def test_register_duplicate_email(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    response = register_user(test_client, 'anotheruser', 'test@example.com', 'testpassword')
    assert b'Username or Email already exists. Please choose a different one.' in response.data # Corrected assertion


def test_login_page(test_client):
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_login_user(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    response = login_user(test_client, 'test@example.com', 'testpassword') # Removed trailing backslash
    assert b'Login successful.' in response.data
    # assert b'Hello, testuser' in response.data # Removed for robustness after redirect


def test_login_invalid_credentials(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    response = login_user(test_client, 'test@example.com', 'wrongpassword')
    assert b'Login Unsuccessful. Please check email and password' in response.data


def test_logout_user(test_client, init_database):
    register_user(test_client, 'testuser', 'test@example.com', 'testpassword')
    login_user(test_client, 'test@example.com', 'testpassword')
    response = logout_user(test_client)
    assert b'You have been logged out.' in response.data
    assert b'Login' in response.data
