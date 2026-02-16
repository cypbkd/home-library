#!/bin/bash

# Deployment script for Book Library AWS Lambda application
# This script packages the Lambda functions and deploys the CloudFormation stack

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." && pwd )"

# Configuration
ENVIRONMENT=${1:-dev}
STACK_NAME="BookLibrary-${ENVIRONMENT}"
REGION=${AWS_REGION:-us-east-1}
SECRET_KEY=${SECRET_KEY:-$(openssl rand -base64 32)}
GOOGLE_BOOKS_API_KEY=${GOOGLE_BOOKS_API_KEY:-""}

echo "========================================="
echo "Book Library AWS Deployment"
echo "========================================="
echo "Environment: ${ENVIRONMENT}"
echo "Stack Name: ${STACK_NAME}"
echo "Region: ${REGION}"
echo "Working Directory: ${SCRIPT_DIR}"
echo "Project Root: ${PROJECT_ROOT}"
echo "========================================="

# Create build directory
BUILD_DIR="${SCRIPT_DIR}/build"
LAMBDA_PACKAGE="${SCRIPT_DIR}/lambda-package.zip"
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

echo "Step 1: Installing Python dependencies..."
python3 -m pip install -r "${PROJECT_ROOT}/infra/aws/requirements-lambda.txt" -t "${BUILD_DIR}" --quiet

echo "Step 2: Copying application code..."
cp "${PROJECT_ROOT}/app/aws_lambda/dynamodb_models.py" "${BUILD_DIR}/"
cp "${PROJECT_ROOT}/app/aws_lambda/app_lambda.py" "${BUILD_DIR}/"
cp "${PROJECT_ROOT}/app/aws_lambda/lambda_handler.py" "${BUILD_DIR}/"
cp "${PROJECT_ROOT}/app/aws_lambda/tasks_lambda.py" "${BUILD_DIR}/"

echo "Step 3: Copying templates..."
cp -r "${PROJECT_ROOT}/templates" "${BUILD_DIR}/"

echo "Step 4: Creating Lambda deployment package..."
(
  cd "${BUILD_DIR}"
  zip -r "${LAMBDA_PACKAGE}" . -q
)

echo "Step 5: Uploading Lambda package to S3..."
# Create S3 bucket for deployment artifacts if it doesn't exist
DEPLOYMENT_BUCKET="book-library-deployment-${REGION}-${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
aws s3 mb s3://${DEPLOYMENT_BUCKET} --region ${REGION} 2>/dev/null || true

# Upload Lambda package
aws s3 cp "${LAMBDA_PACKAGE}" s3://${DEPLOYMENT_BUCKET}/lambda-package-${ENVIRONMENT}.zip --region ${REGION}

echo "Step 6: Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file "${PROJECT_ROOT}/infra/aws/cloudformation-template.yaml" \
  --stack-name ${STACK_NAME} \
  --parameter-overrides \
    Environment=${ENVIRONMENT} \
    SecretKey=${SECRET_KEY} \
    GoogleBooksAPIKey=${GOOGLE_BOOKS_API_KEY} \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ${REGION}

echo "Step 7: Updating Lambda function code..."
API_FUNCTION_NAME="BookLibrary-API-${ENVIRONMENT}"
WORKER_FUNCTION_NAME="BookLibrary-MetadataWorker-${ENVIRONMENT}"

# Update deployment bucket name to match what we used
DEPLOYMENT_BUCKET="book-library-deployment-${REGION}-${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"

aws lambda update-function-code \
  --function-name ${API_FUNCTION_NAME} \
  --s3-bucket ${DEPLOYMENT_BUCKET} \
  --s3-key lambda-package-${ENVIRONMENT}.zip \
  --region ${REGION}

aws lambda update-function-code \
  --function-name ${WORKER_FUNCTION_NAME} \
  --s3-bucket ${DEPLOYMENT_BUCKET} \
  --s3-key lambda-package-${ENVIRONMENT}.zip \
  --region ${REGION}

echo "Step 8: Getting stack outputs..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name ${STACK_NAME} \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --region ${REGION})

STATIC_WEBSITE_URL=$(aws cloudformation describe-stacks \
  --stack-name ${STACK_NAME} \
  --query 'Stacks[0].Outputs[?OutputKey==`StaticWebsiteURL`].OutputValue' \
  --output text \
  --region ${REGION})

echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo "API Endpoint: ${API_ENDPOINT}"
echo "Static Website URL: ${STATIC_WEBSITE_URL}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update your frontend to use the API endpoint: ${API_ENDPOINT}"
echo "2. Deploy static files to S3 bucket"
echo "3. Test the application"
echo ""

# Cleanup
rm -rf "${BUILD_DIR}"
rm -f "${LAMBDA_PACKAGE}"

echo "Deployment artifacts cleaned up."
