# Quick Start Guide

Get your Book Library application running on AWS in under 15 minutes!

## Prerequisites Check

Run these commands to verify you have everything:

```bash
# Check AWS CLI
aws --version
# Expected: aws-cli/2.x.x or higher

# Check Python
python3 --version
# Expected: Python 3.11.x or higher

# Check AWS credentials
aws sts get-caller-identity
# Should return your AWS account details

# Check OpenSSL
openssl version
# Expected: OpenSSL 1.x or higher
```

## 5-Step Deployment

### Step 1: Generate Secret Key

```bash
export SECRET_KEY=$(openssl rand -base64 32)
echo "Your SECRET_KEY: $SECRET_KEY"
# Save this key somewhere safe!
```

### Step 2: Set AWS Region (Optional)

```bash
export AWS_REGION=us-east-1
# Change to your preferred region
```

### Step 3: Navigate to AWS Directory

```bash
cd home-library/aws
```

### Step 4: Deploy Everything

```bash
./deploy.sh dev
```

This will take 5-10 minutes. It will:
- Install Python dependencies
- Package Lambda functions
- Create DynamoDB tables
- Deploy Lambda functions
- Set up API Gateway
- Create SQS queue
- Create S3 bucket

### Step 5: Get Your API Endpoint

```bash
aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

Save this URL - it's your application endpoint!

## Test Your Deployment

### Test 1: Health Check

```bash
API_ENDPOINT="<your-api-endpoint-from-step-5>"
curl ${API_ENDPOINT}/health
```

Expected response: `{"status":"healthy"}`

### Test 2: Home Page

```bash
curl ${API_ENDPOINT}/home
```

Expected: HTML content

### Test 3: Register a User

```bash
curl -X POST ${API_ENDPOINT}/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&email=test@example.com&password=Test123!&confirm_password=Test123!"
```

### Test 4: View in Browser

Open your API endpoint in a browser:
```
https://<your-api-endpoint>/home
```

## What's Next?

### View Your Resources

```bash
# View DynamoDB tables
aws dynamodb list-tables

# View Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `BookLibrary`)].FunctionName'

# View logs
aws logs tail /aws/lambda/BookLibrary-API-dev --follow
```

### Add Your First Book

1. Open `https://<your-api-endpoint>/register` in browser
2. Create an account
3. Login
4. Click "Add Book"
5. Enter book details or scan ISBN

### Monitor Your Application

```bash
# View API Lambda logs
aws logs tail /aws/lambda/BookLibrary-API-dev --follow

# View Metadata Worker logs
aws logs tail /aws/lambda/BookLibrary-MetadataWorker-dev --follow

# Check DynamoDB tables
aws dynamodb scan --table-name BookLibrary-Users-dev --max-items 5
```

## Common Issues

### Issue: "Unable to locate credentials"
**Solution**: Run `aws configure` and enter your AWS credentials

### Issue: "Stack already exists"
**Solution**: Delete the existing stack first:
```bash
aws cloudformation delete-stack --stack-name BookLibrary-dev
aws cloudformation wait stack-delete-complete --stack-name BookLibrary-dev
```

### Issue: "Access Denied" errors
**Solution**: Ensure your AWS user has permissions for:
- CloudFormation
- Lambda
- DynamoDB
- API Gateway
- S3
- IAM
- SQS
- CloudWatch Logs

### Issue: Lambda function returns 502
**Solution**: Check Lambda logs:
```bash
aws logs tail /aws/lambda/BookLibrary-API-dev --follow
```

## Cost Information

With the free tier, your costs should be minimal:
- First 1M Lambda requests/month: FREE
- First 25 GB DynamoDB storage: FREE
- First 1M API Gateway requests/month: FREE
- First 1M SQS requests/month: FREE

Expected cost for low usage: $2-5/month

## Clean Up

To delete everything and stop charges:

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name BookLibrary-dev

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name BookLibrary-dev

# Delete S3 buckets (must be empty first)
aws s3 rb s3://book-library-static-dev-$(aws sts get-caller-identity --query Account --output text) --force
aws s3 rb s3://book-library-deployment-$(aws sts get-caller-identity --query Account --output text) --force
```

## Production Deployment

For production, use:

```bash
./deploy.sh prod
```

And follow the additional security steps in `DEPLOYMENT_CHECKLIST.md`.

## Getting Help

- Check `README.md` for detailed documentation
- Check `ARCHITECTURE.md` for system design
- Check `DEPLOYMENT_CHECKLIST.md` for complete deployment steps
- Check CloudWatch Logs for error messages
- Check AWS CloudFormation console for stack events

## Next Steps

1. ✅ Deployment complete
2. 📖 Read `ARCHITECTURE.md` to understand the system
3. 🔒 Review security settings in `DEPLOYMENT_CHECKLIST.md`
4. 📊 Set up monitoring and alarms
5. 🚀 Deploy to production when ready

---

**Congratulations!** Your Book Library is now running on AWS! 🎉
