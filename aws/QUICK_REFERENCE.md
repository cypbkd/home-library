# Quick Reference Card

## 🚀 Deployment Commands

```bash
# First time deployment
cd home-library/aws
export SECRET_KEY=$(openssl rand -base64 32)
./deploy.sh dev

# Update deployment
./deploy.sh dev

# Deploy to production
./deploy.sh prod

# Update configuration only
./update-stack.sh dev

# Deploy static website
./deploy-static.sh dev
```

## 📊 Monitoring Commands

```bash
# View API logs (live)
aws logs tail /aws/lambda/BookLibrary-API-dev --follow

# View worker logs (live)
aws logs tail /aws/lambda/BookLibrary-MetadataWorker-dev --follow

# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# Check DynamoDB tables
aws dynamodb list-tables | grep BookLibrary

# Scan users table
aws dynamodb scan --table-name BookLibrary-Users-dev --max-items 5

# Check SQS queue
aws sqs get-queue-attributes \
  --queue-url $(aws cloudformation describe-stacks \
    --stack-name BookLibrary-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`MetadataQueueURL`].OutputValue' \
    --output text) \
  --attribute-names All
```

## 🧪 Testing Commands

```bash
# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Test health check
curl ${API_ENDPOINT}/health

# Test home page
curl ${API_ENDPOINT}/home

# Test in browser
open ${API_ENDPOINT}/home

# Local testing
python test-local.py
```

## 🗑️ Cleanup Commands

```bash
# Delete stack
aws cloudformation delete-stack --stack-name BookLibrary-dev

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name BookLibrary-dev

# Delete S3 buckets
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 rb s3://book-library-static-dev-${ACCOUNT_ID} --force
aws s3 rb s3://book-library-deployment-${ACCOUNT_ID} --force
```

## 📋 Stack Information

```bash
# List all stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --query 'Stacks[0].Outputs'

# Get stack status
aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --query 'Stacks[0].StackStatus' \
  --output text

# View stack events
aws cloudformation describe-stack-events \
  --stack-name BookLibrary-dev \
  --max-items 10
```

## 🔧 Lambda Management

```bash
# List Lambda functions
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `BookLibrary`)].FunctionName'

# Get function configuration
aws lambda get-function-configuration \
  --function-name BookLibrary-API-dev

# Update function code
aws lambda update-function-code \
  --function-name BookLibrary-API-dev \
  --s3-bucket book-library-deployment-${ACCOUNT_ID} \
  --s3-key lambda-package-dev.zip

# Invoke function manually
aws lambda invoke \
  --function-name BookLibrary-API-dev \
  --payload '{"test": "data"}' \
  response.json
```

## 💾 DynamoDB Operations

```bash
# Describe table
aws dynamodb describe-table --table-name BookLibrary-Users-dev

# Count items
aws dynamodb scan --table-name BookLibrary-Users-dev --select COUNT

# Get item
aws dynamodb get-item \
  --table-name BookLibrary-Users-dev \
  --key '{"user_id":{"S":"your-user-id"}}'

# Query by email
aws dynamodb query \
  --table-name BookLibrary-Users-dev \
  --index-name email-index \
  --key-condition-expression "email = :email" \
  --expression-attribute-values '{":email":{"S":"test@example.com"}}'

# Backup table
aws dynamodb create-backup \
  --table-name BookLibrary-Users-dev \
  --backup-name Users-backup-$(date +%Y%m%d)
```

## 📈 CloudWatch Metrics

```bash
# Get Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=BookLibrary-API-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Get Lambda errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=BookLibrary-API-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Get DynamoDB consumed capacity
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=BookLibrary-Users-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## 🔐 Security Commands

```bash
# Get IAM role
aws iam get-role --role-name BookLibrary-Lambda-dev

# List role policies
aws iam list-role-policies --role-name BookLibrary-Lambda-dev

# Get role policy
aws iam get-role-policy \
  --role-name BookLibrary-Lambda-dev \
  --policy-name DynamoDBAccess

# Enable DynamoDB encryption
aws dynamodb update-table \
  --table-name BookLibrary-Users-dev \
  --sse-specification Enabled=true,SSEType=KMS
```

## 💰 Cost Tracking

```bash
# Get current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://<(echo '{
    "Tags": {
      "Key": "Application",
      "Values": ["BookLibrary"]
    }
  }')

# Set up budget alert
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json
```

## 🔄 Migration Commands

```bash
# Run migration
python migrate_to_dynamodb.py

# Verify migration
aws dynamodb scan --table-name BookLibrary-Users-dev --select COUNT
aws dynamodb scan --table-name BookLibrary-Books-dev --select COUNT
aws dynamodb scan --table-name BookLibrary-UserBooks-dev --select COUNT
```

## 📦 Package Management

```bash
# Install dependencies locally
pip install -r requirements-lambda.txt

# Update dependencies
pip install --upgrade -r requirements-lambda.txt

# Create requirements file
pip freeze > requirements-lambda.txt

# Check for security vulnerabilities
pip install safety
safety check -r requirements-lambda.txt
```

## 🐛 Debugging

```bash
# Get recent errors from logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/BookLibrary-API-dev \
  --filter-pattern "ERROR" \
  --max-items 10

# Get Lambda function errors
aws lambda get-function \
  --function-name BookLibrary-API-dev \
  --query 'Configuration.LastUpdateStatus'

# Check API Gateway
aws apigatewayv2 get-apis \
  --query 'Items[?Name==`BookLibrary-API-dev`]'

# Test Lambda locally
python test-local.py
```

## 📝 Environment Variables

```bash
# Set for deployment
export AWS_REGION=us-east-1
export ENVIRONMENT=dev
export SECRET_KEY=$(openssl rand -base64 32)
export GOOGLE_BOOKS_API_KEY=your_api_key

# View Lambda environment variables
aws lambda get-function-configuration \
  --function-name BookLibrary-API-dev \
  --query 'Environment.Variables'

# Update Lambda environment variables
aws lambda update-function-configuration \
  --function-name BookLibrary-API-dev \
  --environment Variables="{SECRET_KEY=new_key,ENVIRONMENT=dev}"
```

## 🔗 Useful URLs

```bash
# Get all important URLs
echo "API Endpoint: $(aws cloudformation describe-stacks --stack-name BookLibrary-dev --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)"
echo "Static Website: $(aws cloudformation describe-stacks --stack-name BookLibrary-dev --query 'Stacks[0].Outputs[?OutputKey==`StaticWebsiteURL`].OutputValue' --output text)"
echo "CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#logsV2:log-groups"
echo "DynamoDB Tables: https://console.aws.amazon.com/dynamodbv2/home?region=${AWS_REGION}#tables"
echo "Lambda Functions: https://console.aws.amazon.com/lambda/home?region=${AWS_REGION}#/functions"
```

## 📚 Documentation Files

- **QUICK_START.md** - 5-step deployment guide
- **README.md** - Complete documentation
- **ARCHITECTURE.md** - System design
- **DEPLOYMENT_CHECKLIST.md** - Deployment steps
- **MIGRATION_GUIDE.md** - Data migration
- **DIFFERENCES.md** - Local vs AWS
- **FILE_STRUCTURE.md** - File organization

## 🆘 Emergency Procedures

### Application Down
```bash
# Check Lambda status
aws lambda get-function --function-name BookLibrary-API-dev

# Check recent errors
aws logs tail /aws/lambda/BookLibrary-API-dev --since 10m

# Rollback to previous version
aws lambda update-function-code \
  --function-name BookLibrary-API-dev \
  --s3-bucket book-library-deployment-${ACCOUNT_ID} \
  --s3-key lambda-package-dev-previous.zip
```

### High Costs
```bash
# Check current costs
aws ce get-cost-and-usage --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) --granularity DAILY --metrics BlendedCost

# Reduce DynamoDB capacity (if using provisioned)
aws dynamodb update-table \
  --table-name BookLibrary-Users-dev \
  --billing-mode PAY_PER_REQUEST

# Delete unused resources
./cleanup.sh
```

### Data Loss
```bash
# Restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name BookLibrary-Users-dev-restored \
  --backup-arn arn:aws:dynamodb:region:account:table/BookLibrary-Users-dev/backup/backup-name

# Enable point-in-time recovery
aws dynamodb update-continuous-backups \
  --table-name BookLibrary-Users-dev \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

---

**Pro Tip**: Save this file for quick reference during deployment and operations!
