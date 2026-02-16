# AWS Deployment Checklist

Use this checklist to ensure a smooth deployment of the Book Library application to AWS.

## Pre-Deployment

### AWS Account Setup
- [ ] AWS account created and active
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Verify account ID: `aws sts get-caller-identity`
- [ ] Sufficient permissions for CloudFormation, Lambda, DynamoDB, API Gateway, S3, IAM

### Local Environment
- [ ] Python 3.11 installed (`python3 --version`)
- [ ] pip installed and updated (`pip --version`)
- [ ] Git installed (for version control)
- [ ] OpenSSL installed (for generating secret keys)

### Configuration
- [ ] Generate SECRET_KEY: `openssl rand -base64 32`
- [ ] (Optional) Obtain Google Books API key
- [ ] Choose AWS region (default: us-east-1)
- [ ] Choose environment name (dev/staging/prod)

## Deployment Steps

### 1. Initial Infrastructure Deployment
- [ ] Navigate to aws directory: `cd home-library/aws`
- [ ] Make deploy script executable: `chmod +x deploy.sh`
- [ ] Set environment variables:
  ```bash
  export AWS_REGION=us-east-1
  export SECRET_KEY=your_generated_secret_key
  export GOOGLE_BOOKS_API_KEY=your_api_key  # Optional
  ```
- [ ] Run deployment: `./deploy.sh dev`
- [ ] Wait for CloudFormation stack creation (5-10 minutes)
- [ ] Verify stack status: `aws cloudformation describe-stacks --stack-name BookLibrary-dev`

### 2. Verify Resources Created
- [ ] DynamoDB tables created:
  - [ ] BookLibrary-Users-dev
  - [ ] BookLibrary-Books-dev
  - [ ] BookLibrary-UserBooks-dev
- [ ] Lambda functions deployed:
  - [ ] BookLibrary-API-dev
  - [ ] BookLibrary-MetadataWorker-dev
- [ ] API Gateway created and configured
- [ ] SQS queue created: BookLibrary-Metadata-dev
- [ ] S3 bucket created: book-library-static-dev-{account-id}
- [ ] IAM role created: BookLibrary-Lambda-dev
- [ ] CloudWatch log groups created

### 3. Get Deployment Outputs
- [ ] Get API endpoint:
  ```bash
  aws cloudformation describe-stacks \
    --stack-name BookLibrary-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text
  ```
- [ ] Save API endpoint for testing
- [ ] Get S3 website URL (if using static hosting)

### 4. Test Deployment
- [ ] Test health endpoint: `curl {API_ENDPOINT}/health`
- [ ] Test home page: `curl {API_ENDPOINT}/home`
- [ ] Test user registration via API or web interface
- [ ] Test user login
- [ ] Test adding a book
- [ ] Test viewing books list
- [ ] Test editing a book
- [ ] Test deleting a book
- [ ] Verify metadata worker processes SQS messages

### 5. Monitor and Verify
- [ ] Check Lambda logs:
  ```bash
  aws logs tail /aws/lambda/BookLibrary-API-dev --follow
  ```
- [ ] Check DynamoDB tables have data:
  ```bash
  aws dynamodb scan --table-name BookLibrary-Users-dev --max-items 5
  ```
- [ ] Check SQS queue metrics in AWS Console
- [ ] Verify no errors in CloudWatch logs

## Post-Deployment

### Security Hardening
- [ ] Move SECRET_KEY to AWS Secrets Manager (production)
- [ ] Configure CORS for specific domains (not wildcard)
- [ ] Enable DynamoDB encryption at rest
- [ ] Enable SQS encryption
- [ ] Review IAM role permissions (principle of least privilege)
- [ ] Enable CloudTrail for audit logging
- [ ] Set up AWS WAF for API Gateway (production)

### Monitoring Setup
- [ ] Create CloudWatch dashboard for key metrics
- [ ] Set up CloudWatch alarms:
  - [ ] Lambda errors
  - [ ] Lambda duration > 25s
  - [ ] DynamoDB throttling
  - [ ] SQS dead letter queue messages
  - [ ] API Gateway 5xx errors
- [ ] Configure SNS topic for alarm notifications
- [ ] Set up log retention policies

### Cost Optimization
- [ ] Review DynamoDB on-demand vs provisioned capacity
- [ ] Set up AWS Budgets alert
- [ ] Enable S3 lifecycle policies for old logs
- [ ] Review Lambda memory allocation
- [ ] Consider API Gateway caching for production

### Documentation
- [ ] Document API endpoint URL
- [ ] Document environment variables
- [ ] Update team wiki/documentation
- [ ] Create runbook for common operations
- [ ] Document rollback procedure

## Production Deployment

### Additional Steps for Production
- [ ] Use separate AWS account or strict IAM boundaries
- [ ] Enable DynamoDB point-in-time recovery
- [ ] Set up DynamoDB backups
- [ ] Configure CloudFront for S3 static hosting
- [ ] Use custom domain with Route 53
- [ ] Enable SSL/TLS with ACM certificate
- [ ] Set up multi-region deployment (if needed)
- [ ] Configure VPC for Lambda functions
- [ ] Enable X-Ray tracing
- [ ] Set up CI/CD pipeline (GitHub Actions, CodePipeline)
- [ ] Perform load testing
- [ ] Create disaster recovery plan

## Rollback Plan

If deployment fails or issues arise:

### Quick Rollback
- [ ] Revert Lambda function code:
  ```bash
  aws lambda update-function-code \
    --function-name BookLibrary-API-dev \
    --s3-bucket book-library-deployment-{account-id} \
    --s3-key lambda-package-dev-previous.zip
  ```

### Full Rollback
- [ ] Delete CloudFormation stack:
  ```bash
  aws cloudformation delete-stack --stack-name BookLibrary-dev
  ```
- [ ] Restore DynamoDB tables from backup (if needed)
- [ ] Redeploy previous version

## Troubleshooting

### Common Issues
- [ ] Lambda timeout: Increase timeout in CloudFormation template
- [ ] DynamoDB access denied: Check IAM role permissions
- [ ] API Gateway 502: Check Lambda logs for errors
- [ ] SQS messages not processing: Verify event source mapping
- [ ] CORS errors: Update CORS configuration in CloudFormation

### Support Resources
- [ ] AWS Support (if you have a support plan)
- [ ] AWS Documentation
- [ ] Stack Overflow
- [ ] AWS re:Post community

## Maintenance

### Regular Tasks
- [ ] Review CloudWatch logs weekly
- [ ] Check AWS costs monthly
- [ ] Update Lambda runtime when new versions available
- [ ] Review and rotate secrets quarterly
- [ ] Update dependencies for security patches
- [ ] Review and optimize DynamoDB indexes
- [ ] Clean up old CloudWatch logs

### Updates
- [ ] Test updates in dev environment first
- [ ] Use blue-green deployment for production
- [ ] Keep previous Lambda versions for quick rollback
- [ ] Document all changes in CHANGELOG

---

## Sign-off

Deployment completed by: _______________
Date: _______________
Environment: _______________
Stack Name: _______________
API Endpoint: _______________

Notes:
_______________________________________________
_______________________________________________
_______________________________________________
