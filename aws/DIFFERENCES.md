# Local vs AWS Deployment Differences

This document outlines the key differences between the local Flask application and the AWS serverless deployment.

## Architecture Comparison

### Local Development
```
User Browser
    ↓
Flask Dev Server (localhost:5000)
    ↓
SQLAlchemy ORM
    ↓
SQLite Database (instance/site.db)
    ↓
Background Thread (metadata fetch)
```

### AWS Production
```
User Browser
    ↓
API Gateway (HTTPS)
    ↓
Lambda Function (Flask app)
    ↓
DynamoDB (NoSQL)
    ↓
SQS Queue → Lambda Worker (metadata fetch)
```

## Code Changes

### 1. Database Layer

#### Local (SQLAlchemy)
```python
from flask_sqlalchemy import SQLAlchemy
from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    
user = User.query.filter_by(email=email).first()
db.session.add(user)
db.session.commit()
```

#### AWS (DynamoDB)
```python
import boto3
from dynamodb_models import DynamoDBUser

dynamodb = boto3.resource('dynamodb')

user = DynamoDBUser.get_by_email(email)
DynamoDBUser.create(username, email, password)
```

### 2. Background Tasks

#### Local (Threading)
```python
import threading

thread = threading.Thread(target=fetch_book_metadata, args=(app, user_book_id))
thread.daemon = True
thread.start()
```

#### AWS (SQS)
```python
import boto3

sqs = boto3.client('sqs')
sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody=json.dumps({'user_book_id': user_book_id})
)
```

### 3. Application Entry Point

#### Local (app.py)
```python
from flask import Flask
from extensions import db, login_manager

app = Flask(__name__)
db.init_app(app)
login_manager.init_app(app)

if __name__ == '__main__':
    app.run(debug=True)
```

#### AWS (lambda_handler.py)
```python
from app_lambda import app

def lambda_handler(event, context):
    # Convert API Gateway event to WSGI
    environ = create_wsgi_environ(event)
    response = app.full_dispatch_request()
    return convert_to_api_gateway_response(response)
```

### 4. Configuration

#### Local (config.py)
```python
class Config:
    SECRET_KEY = 'a_very_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
```

#### AWS (Environment Variables)
```python
import os

SECRET_KEY = os.environ['SECRET_KEY']
USERS_TABLE = os.environ['USERS_TABLE']
BOOKS_TABLE = os.environ['BOOKS_TABLE']
```

## File Structure Comparison

### Local Files
```
home-library/
├── app.py                 # Main Flask app
├── models.py              # SQLAlchemy models
├── extensions.py          # Flask extensions
├── config.py              # Configuration
├── tasks.py               # Background tasks
├── requirements.txt       # Dependencies
└── instance/
    └── site.db           # SQLite database
```

### AWS Files
```
home-library/aws/
├── app_lambda.py          # Flask app for Lambda
├── lambda_handler.py      # Lambda entry point
├── dynamodb_models.py     # DynamoDB operations
├── tasks_lambda.py        # SQS-based tasks
├── requirements-lambda.txt # Lambda dependencies
├── cloudformation-template.yaml # Infrastructure
└── deploy.sh              # Deployment script
```

## Feature Differences

| Feature | Local | AWS |
|---------|-------|-----|
| **Database** | SQLite (file-based) | DynamoDB (managed NoSQL) |
| **ORM** | SQLAlchemy | Boto3 (AWS SDK) |
| **Background Tasks** | Threading | SQS + Lambda |
| **Sessions** | File-based | Cookie-based |
| **Static Files** | Flask serves | S3 (optional) |
| **Scaling** | Single process | Auto-scaling |
| **Cost** | Free | ~$2-5/month |
| **Deployment** | `flask run` | CloudFormation |
| **Monitoring** | Console logs | CloudWatch |
| **Backup** | Manual file copy | Automatic (DynamoDB) |

## Database Schema Differences

### Primary Keys

#### Local (SQLite)
```python
id = db.Column(db.Integer, primary_key=True)
# Auto-incrementing: 1, 2, 3, 4...
```

#### AWS (DynamoDB)
```python
user_id = str(uuid.uuid4())
# UUID: "550e8400-e29b-41d4-a716-446655440000"
```

### Relationships

#### Local (SQLAlchemy)
```python
class User(db.Model):
    user_books = db.relationship('UserBook', backref='owner')

class UserBook(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
```

#### AWS (DynamoDB)
```python
# No foreign keys - use Global Secondary Indexes
# Query UserBooks by user_id using GSI
response = table.query(
    IndexName='user-index',
    KeyConditionExpression=Key('user_id').eq(user_id)
)
```

### Data Types

| SQLite | DynamoDB | Notes |
|--------|----------|-------|
| INTEGER | Number (Decimal) | DynamoDB uses Decimal for numbers |
| TEXT | String | Same |
| DATETIME | String (ISO 8601) | Store as "2024-01-15T10:30:00Z" |
| BOOLEAN | Boolean | Same |
| NULL | None | Same |

## Query Differences

### Get User by Email

#### Local (SQLAlchemy)
```python
user = User.query.filter_by(email=email).first()
```

#### AWS (DynamoDB)
```python
response = table.query(
    IndexName='email-index',
    KeyConditionExpression=Key('email').eq(email)
)
user = response['Items'][0] if response['Items'] else None
```

### Get All Books for User

#### Local (SQLAlchemy)
```python
user_books = UserBook.query.filter_by(user_id=current_user.id).all()
```

#### AWS (DynamoDB)
```python
response = table.query(
    IndexName='user-index',
    KeyConditionExpression=Key('user_id').eq(user_id)
)
user_books = response['Items']
```

### Join Operations

#### Local (SQLAlchemy)
```python
# Automatic joins via relationships
user_books = UserBook.query.filter_by(user_id=user_id).all()
for ub in user_books:
    print(ub.book_item.title)  # Automatic join
```

#### AWS (DynamoDB)
```python
# Manual joins - fetch separately
user_books = DynamoDBUserBook.get_user_books(user_id)
for ub in user_books:
    book = DynamoDBBook.get_by_id(ub['book_id'])  # Separate query
    print(book['title'])
```

## Dependencies Differences

### Local (requirements.txt)
```
Flask
Flask-SQLAlchemy
Flask-Login
Flask-Migrate
Werkzeug
Pillow
pyzbar
requests
```

### AWS (requirements-lambda.txt)
```
Flask
Flask-Login
Werkzeug
Pillow
pyzbar
requests
boto3  # AWS SDK (added)
# Removed: Flask-SQLAlchemy, Flask-Migrate
```

## Environment Variables

### Local
```bash
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///site.db  # Optional
```

### AWS
```bash
ENVIRONMENT=dev
SECRET_KEY=your_secret_key
USERS_TABLE=BookLibrary-Users-dev
BOOKS_TABLE=BookLibrary-Books-dev
USER_BOOKS_TABLE=BookLibrary-UserBooks-dev
METADATA_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/...
AWS_REGION=us-east-1
GOOGLE_BOOKS_API_KEY=optional_api_key
```

## Deployment Process

### Local
```bash
# One-time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade

# Run
flask run
```

### AWS
```bash
# One-time setup
cd aws
export SECRET_KEY=$(openssl rand -base64 32)

# Deploy
./deploy.sh dev

# Update
./deploy.sh dev  # Redeploy with changes
```

## Testing Differences

### Local Testing
```bash
# Run Flask app
flask run

# Test in browser
open http://localhost:5000

# Run tests
pytest
```

### AWS Testing
```bash
# Deploy first
./deploy.sh dev

# Get endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks ...)

# Test
curl ${API_ENDPOINT}/health

# View logs
aws logs tail /aws/lambda/BookLibrary-API-dev --follow
```

## Performance Characteristics

### Local
- **Latency**: 1-10ms (local)
- **Throughput**: ~100 concurrent users
- **Startup**: Instant
- **Cold start**: N/A

### AWS
- **Latency**: 50-200ms (network + Lambda)
- **Throughput**: Thousands of concurrent users
- **Startup**: 5-10 minutes (deployment)
- **Cold start**: 1-3 seconds (first request)

## Cost Comparison

### Local
- **Infrastructure**: $0 (your computer)
- **Database**: $0 (SQLite)
- **Scaling**: Limited by hardware
- **Maintenance**: Manual updates

### AWS
- **Infrastructure**: ~$2-5/month (low usage)
- **Database**: Pay per request
- **Scaling**: Automatic, unlimited
- **Maintenance**: Managed by AWS

## Migration Path

To migrate from local to AWS:

1. ✅ Deploy AWS infrastructure
2. ✅ Run migration script (see MIGRATION_GUIDE.md)
3. ✅ Test AWS deployment
4. ✅ Update DNS/URLs
5. ✅ Monitor for issues
6. ✅ Keep local backup for 30 days

## Advantages of Each

### Local Development
- ✅ Fast iteration
- ✅ Easy debugging
- ✅ No AWS costs
- ✅ Works offline
- ✅ Simple setup

### AWS Production
- ✅ Scales automatically
- ✅ High availability
- ✅ Managed infrastructure
- ✅ Global reach
- ✅ Professional deployment
- ✅ Automatic backups

## When to Use Each

### Use Local for:
- Development and testing
- Learning Flask
- Prototyping features
- Small personal projects
- Offline work

### Use AWS for:
- Production applications
- Multiple users
- High availability needs
- Professional projects
- Scalability requirements
- Team collaboration

## Hybrid Approach

You can use both:
1. Develop locally with SQLite
2. Test locally with DynamoDB (using LocalStack)
3. Deploy to AWS for production
4. Keep local version for quick testing

## Summary

The AWS deployment maintains the same functionality as the local version but uses cloud-native services for better scalability, reliability, and professional deployment. The main changes are:

1. **Database**: SQLite → DynamoDB
2. **Background tasks**: Threading → SQS
3. **Deployment**: Flask dev server → Lambda + API Gateway
4. **Scaling**: Single process → Auto-scaling
5. **Cost**: Free → ~$2-5/month

Both versions support the same features:
- User registration and authentication
- Book management (CRUD)
- ISBN barcode scanning
- Metadata fetching
- Reading status tracking
- Book ratings
