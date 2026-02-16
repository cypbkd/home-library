---
inclusion: always
---

# Book Library AWS Deployment Guide

This guide provides essential information for deploying and managing the Book Library application on AWS using a serverless architecture.

## Architecture Overview

**Serverless Stack:**
- **Lambda Functions**: Flask app (API) + Background worker (metadata fetching)
- **API Gateway**: HTTP API endpoint
- **DynamoDB**: 3 tables (Users, Books, UserBooks)
- **SQS**: Async task queue
- **S3**: Deployment artifacts + optional static hosting

**Deployed Application:**
- Region: us-west-2
- API Endpoint: https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com
- Stack Name: BookLibrary-dev

## Quick Deployment

```bash
# 1. Set environment variables
export AWS_REGION=us-west-2
export SECRET_KEY=$(openssl rand -base64 32)
echo "Save SECRET_KEY: $SECRET_KEY"

# 2. Deploy
cd home-library/aws
./deploy.sh dev

# 3. Get API endpoint
aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --region $AWS_REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# 4. Test
curl https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com/health
```

## Critical Deployment Issues & Solutions

### 1. Lambda Reserved Environment Variables
**Issue**: CloudFormation fails with "AWS_REGION is a reserved key"
**Solution**: Never set `AWS_REGION` in Lambda environment variables - Lambda provides it automatically
**Code**: Use `os.environ.get('AWS_REGION')` without default value

### 2. CloudWatch Log Groups
**Issue**: "Not authorized to perform: logs:CreateLogGroup"
**Solution**: Remove log group resources from CloudFormation - Lambda creates them automatically
**Status**: Fixed in current template

### 3. S3 Bucket Naming
**Issue**: Bucket conflicts and "already exists" errors
**Solution**: Use region-specific names: `book-library-deployment-{region}-{account-id}`
**Status**: Fixed in deploy script

### 4. Binary Dependencies (Pillow/pyzbar)
**Issue**: "cannot import name '_imaging' from 'PIL'"
**Root Cause**: Pillow compiled for macOS, not Amazon Linux 2
**Solution**: Removed from requirements - barcode scanning temporarily disabled
**Future**: Use Lambda layer with pre-compiled Pillow or Docker build

### 5. Lambda Package Structure
**Issue**: "No module named 'flask'"
**Solution**: Install dependencies at root of zip, not in subdirectory
**Fixed**: `pip install -t build/` not `pip install -t build/python/`

## File Structure

```
home-library/aws/
├── app_lambda.py              # Flask app for Lambda
├── lambda_handler.py          # API Gateway integration
├── dynamodb_models.py         # DynamoDB data layer
├── tasks_lambda.py            # SQS background tasks
├── cloudformation-template.yaml  # Infrastructure
├── deploy.sh                  # Deployment script
├── requirements-lambda.txt    # Python dependencies
└── ai-steering/              # This documentation
```

## Key Resources

### DynamoDB Tables
- `BookLibrary-Users-dev` - User accounts with GSI on email/username
- `BookLibrary-Books-dev` - Book catalog with GSI on ISBN
- `BookLibrary-UserBooks-dev` - User-book relationships with GSI on user_id

### Lambda Functions
- `BookLibrary-API-dev` - Main API (512MB, 30s timeout)
- `BookLibrary-MetadataWorker-dev` - Background worker (256MB, 5min timeout)

### Other Resources
- API Gateway: HTTP API with CORS enabled
- SQS Queue: `BookLibrary-Metadata-dev`
- S3 Buckets: Deployment artifacts + auto-generated static hosting

## Management Commands

### View Logs
```bash
# API logs
aws logs tail /aws/lambda/BookLibrary-API-dev --region us-west-2 --follow

# Worker logs
aws logs tail /aws/lambda/BookLibrary-MetadataWorker-dev --region us-west-2 --follow

# Filter errors
aws logs tail /aws/lambda/BookLibrary-API-dev --region us-west-2 --filter-pattern "ERROR"
```

### Update Code Only
```bash
cd home-library/aws
rm -rf build && mkdir build
python3 -m pip install -r requirements-lambda.txt -t build --quiet
cp *.py build/ && cp -r ../templates build/
cd build && zip -r ../lambda-package.zip . -q && cd ..

aws s3 cp lambda-package.zip s3://book-library-deployment-us-west-2-841425310647/lambda-package-dev.zip --region us-west-2

aws lambda update-function-code --function-name BookLibrary-API-dev \
  --s3-bucket book-library-deployment-us-west-2-841425310647 \
  --s3-key lambda-package-dev.zip --region us-west-2

aws lambda update-function-code --function-name BookLibrary-MetadataWorker-dev \
  --s3-bucket book-library-deployment-us-west-2-841425310647 \
  --s3-key lambda-package-dev.zip --region us-west-2
```

### Check Status
```bash
# Stack status
aws cloudformation describe-stacks --stack-name BookLibrary-dev --region us-west-2 --query 'Stacks[0].StackStatus'

# DynamoDB tables
aws dynamodb list-tables --region us-west-2 | grep BookLibrary

# Lambda functions
aws lambda list-functions --region us-west-2 --query 'Functions[?starts_with(FunctionName, `BookLibrary`)].FunctionName'
```

### Delete Everything
```bash
# Delete stack
aws cloudformation delete-stack --stack-name BookLibrary-dev --region us-west-2

# Wait for completion
aws cloudformation wait stack-delete-complete --stack-name BookLibrary-dev --region us-west-2

# Delete S3 buckets
aws s3 rb s3://book-library-deployment-us-west-2-841425310647 --force --region us-west-2
```

## Troubleshooting

### Lambda Returns 502 Error
1. Check CloudWatch logs for errors
2. Verify Lambda has correct environment variables
3. Check IAM role permissions
4. Ensure dependencies installed correctly

### DynamoDB Access Denied
```bash
# Check IAM role
aws iam get-role-policy --role-name BookLibrary-Lambda-dev --policy-name DynamoDBAccess --region us-west-2
```

### SQS Messages Not Processing
```bash
# Check event source mapping
aws lambda list-event-source-mappings --function-name BookLibrary-MetadataWorker-dev --region us-west-2

# Check queue
aws sqs get-queue-attributes --queue-url https://sqs.us-west-2.amazonaws.com/841425310647/BookLibrary-Metadata-dev --attribute-names All --region us-west-2
```

### Stack Rollback Failed
```bash
# Force delete
aws cloudformation delete-stack --stack-name BookLibrary-dev --region us-west-2

# If still stuck, manually delete resources then retry
```

## Current Limitations

- ❌ **Barcode scanning disabled** - Requires Pillow compiled for Amazon Linux 2
  - Manual ISBN entry still works
  - Future: Add Lambda layer with pre-compiled Pillow

## Cost Estimate

**Free Tier Coverage:**
- Lambda: 1M requests/month FREE
- DynamoDB: 25GB storage FREE
- API Gateway: 1M requests/month FREE
- SQS: 1M requests/month FREE

**Expected Cost**: $2-5/month for low usage

## Security Notes

- Passwords hashed with PBKDF2-SHA256
- HTTPS only (API Gateway)
- IAM role-based access
- Session cookies with secure flags
- No hardcoded credentials

## Key Differences from Local

| Feature | Local | AWS |
|---------|-------|-----|
| Database | SQLite | DynamoDB |
| Background Tasks | Threading | SQS + Lambda |
| Barcode Scanning | ✅ Pillow | ❌ Disabled |
| Scaling | Single process | Auto-scaling |
| Cost | Free | ~$2-5/month |

## Testing

```bash
# Health check
curl https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com/health
# Expected: {"status":"healthy"}

# Home page
curl https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com/home

# In browser
open https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com/home
```

## Important Notes

1. **Save SECRET_KEY** - Required for redeployments
2. **Region matters** - All commands need `--region us-west-2`
3. **Binary deps** - Must be compiled for Amazon Linux 2
4. **Log groups** - Lambda creates automatically, don't create in CloudFormation
5. **Reserved vars** - Never set AWS_REGION in Lambda environment
6. **Bucket names** - Must include region identifier

## Quick Reference

```bash
# Environment setup
export AWS_REGION=us-west-2
export SECRET_KEY="Ha38lr5PtAw3FYZDGvbCR/1IaA2C7xLwHx7PJJ0C4sg="

# Deploy
cd home-library/aws && ./deploy.sh dev

# Test
curl https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com/health

# Logs
aws logs tail /aws/lambda/BookLibrary-API-dev --region us-west-2 --follow

# Status
aws cloudformation describe-stacks --stack-name BookLibrary-dev --region us-west-2
```
