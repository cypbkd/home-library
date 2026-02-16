# AWS Deployment

This directory contains the AWS serverless deployment for the Book Library application.

## 📚 Documentation

All deployment documentation has been consolidated into the `ai-steering` folder:

- **[ai-steering/README.md](../ai-steering/README.md)** - Quick reference, deployment steps, troubleshooting
- **[ai-steering/DEVELOPMENT_GUIDE.md](../ai-steering/DEVELOPMENT_GUIDE.md)** - Technical deep dive, architecture, development guide

## 🚀 Quick Deploy

```bash
# Set environment
export AWS_REGION=us-west-2
export SECRET_KEY=$(openssl rand -base64 32)

# Deploy
cd home-library/aws
./deploy.sh dev

# Test
curl https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com/health
```

## 📁 Files

- `app_lambda.py` - Flask application for Lambda
- `lambda_handler.py` - API Gateway integration
- `dynamodb_models.py` - DynamoDB data layer
- `tasks_lambda.py` - SQS background tasks
- `cloudformation-template.yaml` - Infrastructure as code
- `deploy.sh` - Deployment script
- `deploy-static.sh` - Static website deployment
- `update-stack.sh` - Update CloudFormation parameters
- `test-local.py` - Local testing script
- `requirements-lambda.txt` - Python dependencies

## 🔗 Resources

**Deployed Application:**
- API Endpoint: https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com
- Region: us-west-2
- Stack: BookLibrary-dev

**AWS Resources:**
- DynamoDB: BookLibrary-Users-dev, BookLibrary-Books-dev, BookLibrary-UserBooks-dev
- Lambda: BookLibrary-API-dev, BookLibrary-MetadataWorker-dev
- SQS: BookLibrary-Metadata-dev
- S3: book-library-deployment-us-west-2-841425310647

For complete documentation, see the [ai-steering](../ai-steering/) folder.
