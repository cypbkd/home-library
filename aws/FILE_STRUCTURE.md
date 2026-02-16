# AWS Deployment File Structure

## Complete File Tree

```
home-library/aws/
│
├── 📄 Core Application Files
│   ├── app_lambda.py              # Flask app adapted for Lambda (main application)
│   ├── lambda_handler.py          # Lambda entry point (API Gateway integration)
│   ├── dynamodb_models.py         # DynamoDB data access layer
│   └── tasks_lambda.py            # SQS-based background tasks
│
├── 🏗️ Infrastructure
│   └── cloudformation-template.yaml  # Complete AWS infrastructure definition
│
├── 🚀 Deployment Scripts
│   ├── deploy.sh                  # Main deployment script (executable)
│   ├── deploy-static.sh           # Deploy static files to S3 (executable)
│   ├── update-stack.sh            # Update CloudFormation parameters (executable)
│   └── test-local.py              # Local testing script
│
├── 📚 Documentation
│   ├── README.md                  # Complete deployment guide
│   ├── QUICK_START.md             # 5-step quick start guide
│   ├── ARCHITECTURE.md            # System architecture and design
│   ├── DEPLOYMENT_CHECKLIST.md    # Step-by-step deployment checklist
│   ├── MIGRATION_GUIDE.md         # SQLite to DynamoDB migration
│   ├── DIFFERENCES.md             # Local vs AWS comparison
│   └── FILE_STRUCTURE.md          # This file
│
└── ⚙️ Configuration
    ├── requirements-lambda.txt    # Python dependencies for Lambda
    └── .gitignore                 # Git ignore patterns
```

## File Purposes

### Core Application Files (4 files)

#### app_lambda.py (350+ lines)
- Flask application adapted for AWS Lambda
- All routes and business logic
- User authentication with Flask-Login
- Book management (CRUD operations)
- ISBN barcode scanning
- DynamoDB integration

#### lambda_handler.py (150+ lines)
- AWS Lambda entry point
- Converts API Gateway events to WSGI format
- Handles both API Gateway v1 and v2 formats
- Routes requests to Flask app
- Converts Flask responses back to API Gateway format

#### dynamodb_models.py (250+ lines)
- DynamoDB data access layer
- Replaces SQLAlchemy ORM
- Three model classes:
  - DynamoDBUser (user management)
  - DynamoDBBook (book management)
  - DynamoDBUserBook (user-book relationships)
- CRUD operations for all models
- Query operations using GSIs

#### tasks_lambda.py (100+ lines)
- Background task processing
- SQS message handling
- Metadata fetching from Google Books API
- Updates DynamoDB with book information
- Error handling and retry logic

### Infrastructure (1 file)

#### cloudformation-template.yaml (500+ lines)
Complete AWS infrastructure definition including:
- 3 DynamoDB tables with GSIs
- 2 Lambda functions
- 1 API Gateway (HTTP API)
- 1 SQS queue + dead letter queue
- 1 S3 bucket for static hosting
- IAM roles and policies
- CloudWatch log groups
- All necessary permissions

### Deployment Scripts (4 files)

#### deploy.sh (100+ lines)
Main deployment automation:
- Installs Python dependencies
- Packages Lambda functions
- Uploads to S3
- Deploys CloudFormation stack
- Updates Lambda function code
- Displays deployment outputs

#### deploy-static.sh (80+ lines)
Static website deployment:
- Prepares static files
- Creates index.html and error.html
- Uploads to S3 bucket
- Sets proper content types
- Configures website hosting

#### update-stack.sh (50+ lines)
Quick parameter updates:
- Updates environment variables
- Changes configuration
- No code redeployment needed
- Interactive prompts

#### test-local.py (150+ lines)
Local testing framework:
- Simulates API Gateway events
- Tests Lambda handler locally
- Validates endpoints
- Debugging tool

### Documentation (7 files)

#### README.md (400+ lines)
Complete deployment documentation:
- Prerequisites and setup
- Deployment steps
- Testing procedures
- Monitoring and logging
- Troubleshooting guide
- Cost optimization
- Security considerations

#### QUICK_START.md (200+ lines)
Fast deployment guide:
- 5-step deployment process
- Prerequisites check
- Testing commands
- Common issues
- Next steps

#### ARCHITECTURE.md (600+ lines)
System architecture documentation:
- Architecture diagrams
- Component descriptions
- Data flow diagrams
- Security architecture
- Scalability design
- Cost estimation
- Monitoring strategy

#### DEPLOYMENT_CHECKLIST.md (400+ lines)
Comprehensive deployment checklist:
- Pre-deployment tasks
- Deployment steps
- Post-deployment verification
- Security hardening
- Monitoring setup
- Production considerations
- Rollback procedures

#### MIGRATION_GUIDE.md (500+ lines)
Data migration documentation:
- SQLite to DynamoDB migration
- Migration script (included)
- Step-by-step process
- Data transformation
- Verification procedures
- Rollback plan

#### DIFFERENCES.md (600+ lines)
Local vs AWS comparison:
- Architecture differences
- Code changes
- Database schema changes
- Query differences
- Performance comparison
- Cost comparison
- When to use each

#### FILE_STRUCTURE.md
This file - explains the file structure

### Configuration (2 files)

#### requirements-lambda.txt
Python dependencies for Lambda:
- Flask==3.0.0
- Flask-Login==0.6.3
- Werkzeug==3.0.1
- Pillow==10.1.0
- pyzbar==0.1.9
- requests==2.31.0
- boto3==1.34.0

#### .gitignore
Ignore patterns for:
- Build artifacts (build/, *.zip)
- Python cache (__pycache__/)
- Environment files (.env)
- AWS artifacts (.aws-sam/)
- IDE files (.vscode/, .idea/)
- OS files (.DS_Store)

## File Sizes (Approximate)

| File | Lines | Size | Purpose |
|------|-------|------|---------|
| app_lambda.py | 350 | 12 KB | Main application |
| lambda_handler.py | 150 | 6 KB | Lambda entry |
| dynamodb_models.py | 250 | 10 KB | Data layer |
| tasks_lambda.py | 100 | 4 KB | Background tasks |
| cloudformation-template.yaml | 500 | 18 KB | Infrastructure |
| deploy.sh | 100 | 4 KB | Deployment |
| README.md | 400 | 15 KB | Documentation |
| ARCHITECTURE.md | 600 | 25 KB | Architecture |
| DEPLOYMENT_CHECKLIST.md | 400 | 18 KB | Checklist |
| MIGRATION_GUIDE.md | 500 | 22 KB | Migration |
| DIFFERENCES.md | 600 | 28 KB | Comparison |
| QUICK_START.md | 200 | 8 KB | Quick guide |

**Total**: ~4,150 lines of code and documentation

## Dependencies

### Runtime Dependencies (Lambda)
- Flask (web framework)
- Flask-Login (authentication)
- Werkzeug (WSGI utilities)
- Pillow (image processing)
- pyzbar (barcode scanning)
- requests (HTTP client)
- boto3 (AWS SDK)

### Development Dependencies
- AWS CLI (deployment)
- Python 3.11+ (runtime)
- OpenSSL (secret generation)

### AWS Services Used
- Lambda (compute)
- API Gateway (HTTP API)
- DynamoDB (database)
- SQS (message queue)
- S3 (static hosting)
- IAM (permissions)
- CloudWatch (logging)
- CloudFormation (infrastructure)

## Deployment Artifacts (Generated)

These files are created during deployment:

```
build/                          # Build directory (temporary)
├── python/                     # Python dependencies
├── dynamodb_models.py          # Copied application files
├── app_lambda.py
├── lambda_handler.py
├── tasks_lambda.py
└── templates/                  # HTML templates

lambda-package.zip              # Lambda deployment package (~50 MB)

static-build/                   # Static website files (temporary)
├── index.html
├── error.html
└── templates/
```

These are automatically cleaned up after deployment.

## Usage Patterns

### First Time Deployment
1. Read QUICK_START.md
2. Run deploy.sh
3. Test deployment
4. Read ARCHITECTURE.md

### Regular Updates
1. Modify code
2. Run deploy.sh
3. Monitor logs

### Configuration Changes
1. Run update-stack.sh
2. Enter new values

### Data Migration
1. Read MIGRATION_GUIDE.md
2. Run migration script
3. Verify data

### Troubleshooting
1. Check CloudWatch logs
2. Review DEPLOYMENT_CHECKLIST.md
3. Check AWS console

## File Relationships

```
deploy.sh
    ├── reads: requirements-lambda.txt
    ├── packages: app_lambda.py, lambda_handler.py, dynamodb_models.py, tasks_lambda.py
    ├── uses: cloudformation-template.yaml
    └── creates: lambda-package.zip

cloudformation-template.yaml
    ├── creates: DynamoDB tables
    ├── creates: Lambda functions
    ├── creates: API Gateway
    └── creates: SQS queue

lambda_handler.py
    └── imports: app_lambda.py

app_lambda.py
    ├── imports: dynamodb_models.py
    └── imports: tasks_lambda.py

tasks_lambda.py
    └── imports: dynamodb_models.py
```

## Getting Started

1. **Start here**: QUICK_START.md
2. **Understand system**: ARCHITECTURE.md
3. **Deploy**: Run deploy.sh
4. **Verify**: Follow DEPLOYMENT_CHECKLIST.md
5. **Migrate data**: MIGRATION_GUIDE.md (if needed)
6. **Compare**: DIFFERENCES.md (understand changes)

## Maintenance

### Regular Tasks
- Review CloudWatch logs
- Update dependencies in requirements-lambda.txt
- Update Lambda runtime version
- Review and optimize costs

### Updates
- Modify code files
- Run deploy.sh to redeploy
- Test thoroughly
- Monitor for issues

### Monitoring
- Check CloudWatch dashboards
- Review Lambda metrics
- Monitor DynamoDB capacity
- Check SQS queue depth

---

**Total Project Size**: ~170 KB (code + documentation)
**Deployment Time**: 5-10 minutes
**Maintenance**: Minimal (serverless)
