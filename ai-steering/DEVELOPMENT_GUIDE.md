---
inclusion: always
---

# Book Library Development Guide

Complete technical reference for developing and deploying the Book Library application.

## Project Overview

Flask-based web application for managing personal book collections with AWS serverless deployment.

**Features:**
- User authentication (register/login)
- Book management (CRUD operations)
- Reading status tracking (to-read, reading, read)
- Book ratings (1-5 stars)
- Async metadata fetching from Google Books API
- ISBN barcode scanning (local only - disabled in AWS)

## Local Development

### Setup
```bash
# Clone and setup
cd book_library_app
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run
flask run
# Access: http://127.0.0.1:5000/
```

### Local Stack
- **Database**: SQLite (instance/site.db)
- **ORM**: SQLAlchemy
- **Background**: Threading
- **Dependencies**: Flask, SQLAlchemy, Pillow, pyzbar

## AWS Deployment Architecture

### Serverless Components

**Compute:**
- Lambda API Handler (512MB, 30s timeout) - Flask app
- Lambda Metadata Worker (256MB, 5min timeout) - Background tasks

**Storage:**
- DynamoDB Users table (user_id PK, email/username GSI)
- DynamoDB Books table (book_id PK, isbn GSI)
- DynamoDB UserBooks table (user_book_id PK, user_id/book_id GSI)

**Integration:**
- API Gateway HTTP API (CORS enabled)
- SQS Queue (metadata processing)
- S3 Buckets (deployment + static hosting)

**Security:**
- IAM Role (DynamoDB + SQS + CloudWatch permissions)

### Data Flow

1. **User Request** → API Gateway → Lambda API Handler
2. **Add Book** → Create DynamoDB records → Send SQS message
3. **SQS Message** → Trigger Lambda Worker → Fetch metadata → Update DynamoDB
4. **Response** → Lambda → API Gateway → User

## Code Structure

### Local Files
```
home-library/
├── app.py                 # Main Flask app
├── models.py              # SQLAlchemy models
├── extensions.py          # Flask extensions
├── config.py              # Configuration
├── tasks.py               # Background tasks
├── templates/             # Jinja2 templates
├── instance/site.db       # SQLite database
└── requirements.txt       # Dependencies
```

### AWS Files
```
home-library/aws/
├── app_lambda.py              # Flask app adapted for Lambda
├── lambda_handler.py          # API Gateway event handler
├── dynamodb_models.py         # DynamoDB operations (replaces SQLAlchemy)
├── tasks_lambda.py            # SQS-based tasks (replaces threading)
├── cloudformation-template.yaml  # Infrastructure as code
├── deploy.sh                  # Deployment automation
├── requirements-lambda.txt    # Lambda dependencies (no Pillow)
└── templates/                 # Copied from parent
```

## Database Migration: SQLite → DynamoDB

### Schema Transformation

**SQLite (Relational):**
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Auto-increment
    username = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120), unique=True)
```

**DynamoDB (NoSQL):**
```python
{
    'user_id': 'uuid-string',  # UUID instead of integer
    'username': 'john',
    'email': 'john@example.com',
    'password_hash': 'hashed...',
    'created_at': '2026-02-15T04:56:25Z'  # ISO 8601
}
```

### Key Differences

| Aspect | SQLite | DynamoDB |
|--------|--------|----------|
| Primary Key | Auto-increment integer | UUID string |
| Relationships | Foreign keys | GSI queries |
| Joins | SQL JOIN | Manual (fetch separately) |
| Queries | SQL | Key/GSI queries |
| Transactions | ACID | Eventually consistent |
| Numbers | INTEGER | Decimal (for ratings) |

### Query Examples

**Get user by email:**
```python
# SQLite
user = User.query.filter_by(email=email).first()

# DynamoDB
response = table.query(
    IndexName='email-index',
    KeyConditionExpression=Key('email').eq(email)
)
user = response['Items'][0] if response['Items'] else None
```

**Get user's books:**
```python
# SQLite (automatic join)
user_books = UserBook.query.filter_by(user_id=user.id).all()
for ub in user_books:
    print(ub.book_item.title)  # Relationship

# DynamoDB (manual join)
user_books = DynamoDBUserBook.get_user_books(user_id)
for ub in user_books:
    book = DynamoDBBook.get_by_id(ub['book_id'])  # Separate query
    print(book['title'])
```

## Background Task Migration

### Local (Threading)
```python
import threading

thread = threading.Thread(
    target=fetch_book_metadata,
    args=(app, user_book_id)
)
thread.daemon = True
thread.start()
```

### AWS (SQS)
```python
import boto3

sqs = boto3.client('sqs')
sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody=json.dumps({'user_book_id': user_book_id})
)
# Separate Lambda worker processes messages
```

## Deployment Process

### CloudFormation Template Structure

```yaml
Resources:
  # DynamoDB Tables (3)
  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions: [user_id, email, username]
      GlobalSecondaryIndexes: [email-index, username-index]
  
  # Lambda Functions (2)
  ApiLambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      Runtime: python3.11
      Handler: lambda_handler.lambda_handler
      Environment:
        Variables:
          SECRET_KEY: !Ref SecretKey
          USERS_TABLE: !Ref UsersTable
          # Note: AWS_REGION NOT set (Lambda provides automatically)
  
  # API Gateway
  ApiGateway:
    Type: AWS::ApiGatewayV2::Api
    Properties:
      ProtocolType: HTTP
      CorsConfiguration: {AllowOrigins: ['*']}
  
  # SQS Queue
  MetadataQueue:
    Type: AWS::SQS::Queue
    Properties:
      VisibilityTimeout: 300
      RedrivePolicy: {deadLetterTargetArn, maxReceiveCount: 3}
  
  # IAM Role
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      Policies: [DynamoDBAccess, SQSAccess]
  
  # Note: CloudWatch log groups NOT created (Lambda does automatically)
```

### Deploy Script Flow

```bash
#!/bin/bash
# 1. Install dependencies at root level (not python/ subdirectory)
python3 -m pip install -r requirements-lambda.txt -t build/

# 2. Copy application code
cp *.py build/
cp -r ../templates build/

# 3. Create zip package
cd build && zip -r ../lambda-package.zip . && cd ..

# 4. Upload to S3 (region-specific bucket)
aws s3 cp lambda-package.zip s3://book-library-deployment-${REGION}-${ACCOUNT_ID}/

# 5. Deploy CloudFormation stack
aws cloudformation deploy --template-file cloudformation-template.yaml

# 6. Update Lambda code
aws lambda update-function-code --s3-bucket ... --s3-key ...
```

## Critical Implementation Details

### 1. Lambda Environment Variables

**NEVER set these (Lambda-reserved):**
- AWS_REGION
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_SESSION_TOKEN

**Correct usage:**
```python
# Lambda automatically provides AWS_REGION
region = os.environ.get('AWS_REGION')  # No default needed
dynamodb = boto3.resource('dynamodb', region_name=region)
```

### 2. Lambda Package Structure

**Correct:**
```
lambda-package.zip
├── flask/
├── boto3/
├── app_lambda.py
├── lambda_handler.py
└── templates/
```

**Incorrect:**
```
lambda-package.zip
└── python/
    ├── flask/
    ├── boto3/
    └── ...
```

### 3. Binary Dependencies

**Problem:** Pillow/pyzbar compiled for macOS won't work in Lambda (Amazon Linux 2)

**Solutions:**

**Option 1: Remove (Current)**
```txt
# requirements-lambda.txt
Flask==3.0.0
Flask-Login==0.6.3
# Pillow==10.1.0  # REMOVED
# pyzbar==0.1.9   # REMOVED
```

**Option 2: Docker Build (Future)**
```bash
docker run --rm -v $(pwd):/var/task \
  public.ecr.aws/lambda/python:3.11 \
  pip install Pillow -t /var/task/build
```

**Option 3: Lambda Layer (Recommended)**
```yaml
# Use pre-built layer
Layers:
  - arn:aws:lambda:us-west-2:770693421928:layer:Klayers-p311-Pillow:1
```

### 4. CloudWatch Log Groups

**Don't create explicitly:**
```yaml
# REMOVE THIS from CloudFormation
ApiLambdaLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: !Sub '/aws/lambda/${ApiLambdaFunction}'
```

**Why:** Lambda creates log groups automatically on first invocation. Creating them explicitly requires `logs:CreateLogGroup` permission which may not be available.

### 5. S3 Bucket Naming

**Problem:** Bucket names are globally unique

**Solution:**
```bash
# Include region in name
BUCKET="book-library-deployment-${REGION}-${ACCOUNT_ID}"

# Or let CloudFormation auto-generate
StaticWebsiteBucket:
  Type: AWS::S3::Bucket
  # No BucketName property - auto-generated
```

## Testing

### Local Testing
```bash
# Run tests
pytest

# Test specific file
pytest tests/test_authentication.py

# Run Flask app
flask run
```

### AWS Testing
```bash
# Health check
curl https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com/health

# Test with data
curl -X POST https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com/register \
  -d "username=test&email=test@example.com&password=Test123!&confirm_password=Test123!"

# Check logs
aws logs tail /aws/lambda/BookLibrary-API-dev --region us-west-2 --follow

# Invoke Lambda directly
aws lambda invoke --function-name BookLibrary-API-dev \
  --payload '{"test":"data"}' response.json --region us-west-2
```

## Monitoring & Debugging

### CloudWatch Metrics
```bash
# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=BookLibrary-API-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-west-2

# Lambda errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=BookLibrary-API-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-west-2
```

### DynamoDB Monitoring
```bash
# Table status
aws dynamodb describe-table --table-name BookLibrary-Users-dev --region us-west-2

# Item count
aws dynamodb scan --table-name BookLibrary-Users-dev --select COUNT --region us-west-2

# Query by email
aws dynamodb query \
  --table-name BookLibrary-Users-dev \
  --index-name email-index \
  --key-condition-expression "email = :email" \
  --expression-attribute-values '{":email":{"S":"test@example.com"}}' \
  --region us-west-2
```

### SQS Monitoring
```bash
# Queue attributes
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-west-2.amazonaws.com/841425310647/BookLibrary-Metadata-dev \
  --attribute-names All \
  --region us-west-2

# Receive messages (for debugging)
aws sqs receive-message \
  --queue-url https://sqs.us-west-2.amazonaws.com/841425310647/BookLibrary-Metadata-dev \
  --max-number-of-messages 1 \
  --region us-west-2
```

## Common Development Tasks

### Add New Route
```python
# app_lambda.py
@app.route("/new_feature")
@login_required
def new_feature():
    # Your code
    return render_template('new_feature.html')
```

### Add DynamoDB Table
```yaml
# cloudformation-template.yaml
NewTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub 'BookLibrary-NewTable-${Environment}'
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: id
        AttributeType: S
    KeySchema:
      - AttributeName: id
        KeyType: HASH
```

### Update Lambda Configuration
```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name BookLibrary-API-dev \
  --timeout 60 \
  --region us-west-2

# Increase memory
aws lambda update-function-configuration \
  --function-name BookLibrary-API-dev \
  --memory-size 1024 \
  --region us-west-2

# Add environment variable
aws lambda update-function-configuration \
  --function-name BookLibrary-API-dev \
  --environment "Variables={SECRET_KEY=xxx,NEW_VAR=value}" \
  --region us-west-2
```

## Security Best Practices

1. **Secrets Management**
   - Use AWS Secrets Manager for production SECRET_KEY
   - Rotate secrets regularly
   - Never commit secrets to git

2. **IAM Permissions**
   - Use least privilege principle
   - Separate roles for different functions
   - Enable CloudTrail for audit logging

3. **API Security**
   - Configure CORS for specific domains (not wildcard)
   - Add rate limiting
   - Consider AWS WAF for production

4. **Data Protection**
   - Enable DynamoDB encryption at rest
   - Enable SQS encryption
   - Use HTTPS only (API Gateway enforces)

## Performance Optimization

1. **Lambda**
   - Use provisioned concurrency for consistent performance
   - Optimize cold start (minimize dependencies)
   - Increase memory for CPU-intensive tasks

2. **DynamoDB**
   - Use GSI for common queries
   - Consider provisioned capacity for predictable workloads
   - Enable DAX for caching (if needed)

3. **API Gateway**
   - Enable caching for GET requests
   - Use CloudFront for global distribution

## Cost Optimization

1. **Lambda**
   - Right-size memory allocation
   - Reduce timeout to minimum needed
   - Use ARM architecture (Graviton2) for 20% savings

2. **DynamoDB**
   - Use on-demand for unpredictable workloads
   - Switch to provisioned for steady traffic
   - Enable auto-scaling

3. **Monitoring**
   - Set up AWS Budgets alerts
   - Review Cost Explorer monthly
   - Delete unused resources

## Lessons Learned

1. **Lambda reserves environment variables** - Don't set AWS_REGION
2. **Lambda creates log groups** - Don't create in CloudFormation
3. **Binary dependencies need platform-specific builds** - Use Docker or layers
4. **S3 bucket names are global** - Include region identifier
5. **Package structure matters** - Dependencies at root, not subdirectory
6. **Stack rollbacks can fail** - Have manual cleanup procedures ready
7. **Save deployment credentials** - SECRET_KEY needed for updates

## Future Enhancements

1. **Barcode Scanning** - Add Lambda layer with Pillow
2. **Custom Domain** - Route 53 + API Gateway custom domain
3. **CloudFront** - CDN for static assets
4. **Cognito** - Managed user authentication
5. **Multi-region** - Global deployment with DynamoDB global tables
6. **CI/CD** - GitHub Actions or CodePipeline
7. **Monitoring** - CloudWatch dashboards and alarms
8. **Testing** - Automated integration tests

## Quick Reference

```bash
# Deploy
cd home-library/aws && ./deploy.sh dev

# Update code only
# (rebuild, upload, update Lambda - see README.md)

# View logs
aws logs tail /aws/lambda/BookLibrary-API-dev --region us-west-2 --follow

# Check status
aws cloudformation describe-stacks --stack-name BookLibrary-dev --region us-west-2

# Delete everything
aws cloudformation delete-stack --stack-name BookLibrary-dev --region us-west-2
```
