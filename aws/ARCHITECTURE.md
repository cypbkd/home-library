# Book Library AWS Architecture

## Overview

The Book Library application uses a serverless architecture on AWS, providing scalability, cost-efficiency, and minimal operational overhead.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Internet                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Amazon S3 Bucket   │
              │  (Static Website)    │
              │  - HTML Templates    │
              │  - Static Assets     │
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   API Gateway        │
              │   (HTTP API)         │
              │  - CORS enabled      │
              │  - Route: $default   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   AWS Lambda         │
              │   (API Handler)      │
              │  - Flask app         │
              │  - User auth         │
              │  - Book management   │
              └──────┬───────┬───────┘
                     │       │
        ┌────────────┘       └────────────┐
        ▼                                  ▼
┌───────────────┐                  ┌──────────────┐
│   DynamoDB    │                  │     SQS      │
│               │                  │    Queue     │
│ ┌───────────┐ │                  │  (Metadata)  │
│ │   Users   │ │                  └──────┬───────┘
│ └───────────┘ │                         │
│ ┌───────────┐ │                         ▼
│ │   Books   │ │              ┌──────────────────┐
│ └───────────┘ │              │   AWS Lambda     │
│ ┌───────────┐ │              │ (Metadata Worker)│
│ │ UserBooks │ │              │ - Fetch book info│
│ └───────────┘ │              │ - Update DynamoDB│
└───────┬───────┘              └──────────────────┘
        │                                  │
        └──────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   CloudWatch Logs    │
              │  - API logs          │
              │  - Worker logs       │
              │  - Error tracking    │
              └──────────────────────┘
```

## Components

### 1. API Gateway (HTTP API)
- **Purpose**: Entry point for all API requests
- **Type**: HTTP API (v2) - simpler and cheaper than REST API
- **Features**:
  - CORS configuration for cross-origin requests
  - Default route ($default) catches all paths
  - Lambda proxy integration
  - Automatic request/response transformation

### 2. Lambda Functions

#### API Handler (`BookLibrary-API-{env}`)
- **Runtime**: Python 3.11
- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Responsibilities**:
  - Handle HTTP requests via Flask
  - User authentication (register, login, logout)
  - Book CRUD operations
  - ISBN barcode scanning
  - Queue metadata fetch tasks to SQS
- **Environment Variables**:
  - `SECRET_KEY`: Flask session secret
  - `USERS_TABLE`: DynamoDB users table name
  - `BOOKS_TABLE`: DynamoDB books table name
  - `USER_BOOKS_TABLE`: DynamoDB user-books table name
  - `METADATA_QUEUE_URL`: SQS queue URL
  - `AWS_REGION`: AWS region
  - `GOOGLE_BOOKS_API_KEY`: Optional API key

#### Metadata Worker (`BookLibrary-MetadataWorker-{env}`)
- **Runtime**: Python 3.11
- **Memory**: 256 MB
- **Timeout**: 300 seconds (5 minutes)
- **Trigger**: SQS queue messages
- **Responsibilities**:
  - Fetch book metadata from Google Books API
  - Update book information in DynamoDB
  - Update sync status
- **Batch Size**: 10 messages per invocation

### 3. DynamoDB Tables

#### Users Table (`BookLibrary-Users-{env}`)
- **Primary Key**: `user_id` (String, UUID)
- **Attributes**:
  - `user_id`: Unique user identifier
  - `username`: User's username
  - `email`: User's email address
  - `password_hash`: Hashed password
  - `created_at`: Account creation timestamp
- **Global Secondary Indexes**:
  - `email-index`: Query by email (for login)
  - `username-index`: Query by username (for uniqueness check)
- **Billing**: On-demand (pay per request)

#### Books Table (`BookLibrary-Books-{env}`)
- **Primary Key**: `book_id` (String, UUID)
- **Attributes**:
  - `book_id`: Unique book identifier
  - `isbn`: ISBN-10 or ISBN-13
  - `title`: Book title
  - `author`: Book author(s)
  - `genre`: Book genre/category
  - `cover_image_url`: URL to cover image
  - `description`: Book description
  - `created_at`: Record creation timestamp
- **Global Secondary Indexes**:
  - `isbn-index`: Query by ISBN (for deduplication)
- **Billing**: On-demand

#### UserBooks Table (`BookLibrary-UserBooks-{env}`)
- **Primary Key**: `user_book_id` (String, UUID)
- **Attributes**:
  - `user_book_id`: Unique relationship identifier
  - `user_id`: Reference to user
  - `book_id`: Reference to book
  - `status`: Reading status (to-read, reading, read)
  - `rating`: User's rating (1-5)
  - `sync_status`: Metadata sync status (PENDING, SYNCED, FAILED)
  - `date_added`: When book was added to library
- **Global Secondary Indexes**:
  - `user-index`: Query all books for a user
  - `user-book-index`: Query specific user-book relationship
- **Billing**: On-demand

### 4. SQS Queue

#### Metadata Queue (`BookLibrary-Metadata-{env}`)
- **Purpose**: Asynchronous book metadata fetching
- **Visibility Timeout**: 300 seconds (matches Lambda timeout)
- **Message Retention**: 14 days
- **Dead Letter Queue**: Yes (after 3 failed attempts)
- **Long Polling**: 20 seconds
- **Message Format**:
  ```json
  {
    "user_book_id": "uuid-string"
  }
  ```

### 5. S3 Bucket

#### Static Website Bucket (`book-library-static-{env}-{account-id}`)
- **Purpose**: Host static website files (optional)
- **Features**:
  - Website hosting enabled
  - Public read access
  - Index document: index.html
  - Error document: error.html
- **Content**:
  - Landing page
  - Static assets (CSS, JS, images)
  - HTML templates (served by Lambda)

### 6. IAM Role

#### Lambda Execution Role (`BookLibrary-Lambda-{env}`)
- **Trusted Entity**: lambda.amazonaws.com
- **Managed Policies**:
  - `AWSLambdaBasicExecutionRole` (CloudWatch Logs)
- **Inline Policies**:
  - **DynamoDBAccess**: Full access to all three tables and indexes
  - **SQSAccess**: Send, receive, delete messages from metadata queue

### 7. CloudWatch Logs

#### Log Groups
- `/aws/lambda/BookLibrary-API-{env}`: API Lambda logs
- `/aws/lambda/BookLibrary-MetadataWorker-{env}`: Worker Lambda logs
- **Retention**: 7 days (configurable)

## Data Flow

### User Registration Flow
1. User submits registration form
2. API Gateway forwards to Lambda
3. Lambda validates input
4. Lambda checks for existing user in DynamoDB (email-index, username-index)
5. Lambda creates new user with hashed password
6. Lambda returns success response

### Add Book Flow
1. User submits book details (manual or ISBN scan)
2. API Gateway forwards to Lambda
3. Lambda checks if book exists (isbn-index)
4. Lambda creates book if new
5. Lambda creates user-book relationship with status='PENDING'
6. Lambda sends message to SQS queue
7. Lambda returns success response
8. SQS triggers Metadata Worker Lambda
9. Worker fetches metadata from Google Books API
10. Worker updates book and user-book records
11. Worker sets status='SYNCED' or 'FAILED'

### View Books Flow
1. User requests books list
2. API Gateway forwards to Lambda
3. Lambda queries UserBooks table (user-index)
4. Lambda enriches with book details from Books table
5. Lambda renders template with book list
6. Lambda returns HTML response

## Security

### Authentication
- Flask-Login session management
- Password hashing with PBKDF2-SHA256
- Session cookies with secure flags

### Authorization
- User ID verification for all book operations
- DynamoDB queries filtered by user_id

### Network Security
- HTTPS only (API Gateway)
- CORS configured for specific origins
- No public database access

### Data Protection
- Passwords hashed, never stored in plaintext
- DynamoDB encryption at rest (optional, recommended)
- CloudWatch Logs encryption

## Scalability

### Automatic Scaling
- **Lambda**: Scales automatically up to account limits
- **DynamoDB**: On-demand scaling handles any traffic
- **API Gateway**: Handles 10,000 requests/second by default
- **SQS**: Unlimited throughput

### Performance Optimization
- DynamoDB GSIs for fast queries
- Lambda warm starts with provisioned concurrency (optional)
- API Gateway caching (optional)
- CloudFront for S3 static content (optional)

## Cost Estimation

### Monthly Cost (Low Traffic - 1000 users, 10,000 requests)
- **Lambda**: ~$0.20 (free tier covers most)
- **DynamoDB**: ~$1.25 (on-demand, 25 WCU, 25 RCU)
- **API Gateway**: ~$0.10 (free tier covers most)
- **SQS**: ~$0.00 (free tier covers most)
- **S3**: ~$0.50 (storage + requests)
- **CloudWatch**: ~$0.50 (logs)
- **Total**: ~$2.55/month

### Monthly Cost (Medium Traffic - 10,000 users, 100,000 requests)
- **Lambda**: ~$5.00
- **DynamoDB**: ~$12.50
- **API Gateway**: ~$3.50
- **SQS**: ~$0.40
- **S3**: ~$1.00
- **CloudWatch**: ~$2.00
- **Total**: ~$24.40/month

## Monitoring and Observability

### Key Metrics
- Lambda invocations, duration, errors
- DynamoDB consumed capacity, throttles
- API Gateway request count, latency, errors
- SQS messages sent, received, deleted
- CloudWatch log errors

### Alarms (Recommended)
- Lambda error rate > 5%
- Lambda duration > 25 seconds
- DynamoDB throttling events
- SQS dead letter queue messages > 0
- API Gateway 5xx errors > 1%

## Disaster Recovery

### Backup Strategy
- DynamoDB point-in-time recovery (35 days)
- DynamoDB on-demand backups
- Lambda function versions
- CloudFormation stack templates in version control

### Recovery Time Objective (RTO)
- Infrastructure: 10-15 minutes (CloudFormation redeploy)
- Data: 5 minutes (DynamoDB restore)

### Recovery Point Objective (RPO)
- DynamoDB: 5 minutes (point-in-time recovery)

## Future Enhancements

### Potential Improvements
1. **CloudFront**: CDN for S3 static content
2. **Cognito**: Managed user authentication
3. **ElastiCache**: Session storage for better performance
4. **Step Functions**: Complex workflows
5. **EventBridge**: Event-driven architecture
6. **AppSync**: GraphQL API
7. **Multi-region**: High availability
8. **VPC**: Enhanced security
9. **X-Ray**: Distributed tracing
10. **WAF**: Web application firewall
