"""
DynamoDB models for the Book Library application.
Replaces SQLAlchemy models with DynamoDB operations using boto3.
"""
import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timezone
from decimal import Decimal
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION'))

# Table names from environment variables
USERS_TABLE = os.environ.get('USERS_TABLE', 'BookLibrary-Users')
BOOKS_TABLE = os.environ.get('BOOKS_TABLE', 'BookLibrary-Books')
USER_BOOKS_TABLE = os.environ.get('USER_BOOKS_TABLE', 'BookLibrary-UserBooks')


class DynamoDBUser:
    """User model for DynamoDB"""
    
    @staticmethod
    def create(username, email, password):
        """Create a new user"""
        table = dynamodb.Table(USERS_TABLE)
        
        # Check if user already exists
        if DynamoDBUser.get_by_email(email) or DynamoDBUser.get_by_username(username):
            return None
        
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        item = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        table.put_item(Item=item)
        return item
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        print(f"[DEBUG] DynamoDBUser.get_by_id called with: {user_id}")
        print(f"[DEBUG] Table name: {USERS_TABLE}")
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'user_id': user_id})
        item = response.get('Item')
        print(f"[DEBUG] DynamoDB response: {item is not None}")
        return item
    
    @staticmethod
    def get_by_email(email):
        """Get user by email using GSI"""
        table = dynamodb.Table(USERS_TABLE)
        response = table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )
        items = response.get('Items', [])
        return items[0] if items else None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username using GSI"""
        table = dynamodb.Table(USERS_TABLE)
        response = table.query(
            IndexName='username-index',
            KeyConditionExpression=Key('username').eq(username)
        )
        items = response.get('Items', [])
        return items[0] if items else None
    
    @staticmethod
    def check_password(user, password):
        """Verify password"""
        return check_password_hash(user['password_hash'], password)


class DynamoDBBook:
    """Book model for DynamoDB"""
    
    @staticmethod
    def create(isbn, title, author, genre=None, cover_image_url=None, description=None):
        """Create a new book"""
        table = dynamodb.Table(BOOKS_TABLE)
        
        # Check if book already exists
        existing = DynamoDBBook.get_by_isbn(isbn)
        if existing:
            return existing
        
        book_id = str(uuid.uuid4())
        
        item = {
            'book_id': book_id,
            'isbn': isbn,
            'title': title,
            'author': author,
            'genre': genre or 'Unknown',
            'cover_image_url': cover_image_url,
            'description': description,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        table.put_item(Item=item)
        return item
    
    @staticmethod
    def get_by_id(book_id):
        """Get book by ID"""
        table = dynamodb.Table(BOOKS_TABLE)
        response = table.get_item(Key={'book_id': book_id})
        return response.get('Item')
    
    @staticmethod
    def get_by_isbn(isbn):
        """Get book by ISBN using GSI"""
        table = dynamodb.Table(BOOKS_TABLE)
        response = table.query(
            IndexName='isbn-index',
            KeyConditionExpression=Key('isbn').eq(isbn)
        )
        items = response.get('Items', [])
        return items[0] if items else None
    
    @staticmethod
    def update(book_id, **kwargs):
        """Update book attributes"""
        table = dynamodb.Table(BOOKS_TABLE)
        
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for key, value in kwargs.items():
            if value is not None:
                update_expression += f"#{key} = :{key}, "
                expression_attribute_values[f":{key}"] = value
                expression_attribute_names[f"#{key}"] = key
        
        update_expression = update_expression.rstrip(", ")
        
        if expression_attribute_values:
            table.update_item(
                Key={'book_id': book_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ExpressionAttributeNames=expression_attribute_names
            )


class DynamoDBUserBook:
    """UserBook model for DynamoDB (many-to-many relationship)"""
    
    @staticmethod
    def create(user_id, book_id, status='to-read', rating=None, sync_status='PENDING'):
        """Create a new user-book relationship"""
        table = dynamodb.Table(USER_BOOKS_TABLE)
        
        # Check if relationship already exists
        existing = DynamoDBUserBook.get(user_id, book_id)
        if existing:
            return None
        
        user_book_id = str(uuid.uuid4())
        
        item = {
            'user_book_id': user_book_id,
            'user_id': user_id,
            'book_id': book_id,
            'status': status,
            'rating': Decimal(str(rating)) if rating else None,
            'sync_status': sync_status,
            'date_added': datetime.now(timezone.utc).isoformat()
        }
        
        table.put_item(Item=item)
        return item
    
    @staticmethod
    def get(user_id, book_id):
        """Get user-book relationship"""
        table = dynamodb.Table(USER_BOOKS_TABLE)
        response = table.query(
            IndexName='user-book-index',
            KeyConditionExpression=Key('user_id').eq(user_id) & Key('book_id').eq(book_id)
        )
        items = response.get('Items', [])
        return items[0] if items else None
    
    @staticmethod
    def get_by_id(user_book_id):
        """Get user-book by ID"""
        table = dynamodb.Table(USER_BOOKS_TABLE)
        response = table.get_item(Key={'user_book_id': user_book_id})
        return response.get('Item')
    
    @staticmethod
    def get_user_books(user_id):
        """Get all books for a user"""
        table = dynamodb.Table(USER_BOOKS_TABLE)
        response = table.query(
            IndexName='user-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        return response.get('Items', [])
    
    @staticmethod
    def update(user_book_id, **kwargs):
        """Update user-book attributes"""
        table = dynamodb.Table(USER_BOOKS_TABLE)
        
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for key, value in kwargs.items():
            if value is not None:
                if key == 'rating' and isinstance(value, int):
                    value = Decimal(str(value))
                update_expression += f"#{key} = :{key}, "
                expression_attribute_values[f":{key}"] = value
                expression_attribute_names[f"#{key}"] = key
        
        update_expression = update_expression.rstrip(", ")
        
        if expression_attribute_values:
            table.update_item(
                Key={'user_book_id': user_book_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ExpressionAttributeNames=expression_attribute_names
            )
    
    @staticmethod
    def delete(user_book_id):
        """Delete user-book relationship"""
        table = dynamodb.Table(USER_BOOKS_TABLE)
        table.delete_item(Key={'user_book_id': user_book_id})
