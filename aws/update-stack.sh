#!/bin/bash

# Quick update script for CloudFormation stack parameters only
# Use this when you need to update environment variables or configuration

set -e

ENVIRONMENT=${1:-dev}
STACK_NAME="BookLibrary-${ENVIRONMENT}"
REGION=${AWS_REGION:-us-east-1}

echo "========================================="
echo "Updating CloudFormation Stack Parameters"
echo "========================================="
echo "Stack: ${STACK_NAME}"
echo "Region: ${REGION}"
echo "========================================="

# Prompt for parameters
read -p "Enter SECRET_KEY (or press Enter to keep existing): " SECRET_KEY
read -p "Enter GOOGLE_BOOKS_API_KEY (or press Enter to keep existing): " GOOGLE_BOOKS_API_KEY

# Build parameter overrides
PARAMS="Environment=${ENVIRONMENT}"

if [ ! -z "$SECRET_KEY" ]; then
    PARAMS="${PARAMS} SecretKey=${SECRET_KEY}"
fi

if [ ! -z "$GOOGLE_BOOKS_API_KEY" ]; then
    PARAMS="${PARAMS} GoogleBooksAPIKey=${GOOGLE_BOOKS_API_KEY}"
fi

echo "Updating stack with parameters..."
aws cloudformation update-stack \
  --stack-name ${STACK_NAME} \
  --template-body file://cloudformation-template.yaml \
  --parameters ${PARAMS} \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ${REGION}

echo "Waiting for stack update to complete..."
aws cloudformation wait stack-update-complete \
  --stack-name ${STACK_NAME} \
  --region ${REGION}

echo "========================================="
echo "Stack update complete!"
echo "========================================="
