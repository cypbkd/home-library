#!/bin/bash

# Script to deploy static website files to S3
# This uploads HTML templates and any static assets

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." && pwd )"

ENVIRONMENT=${1:-dev}
REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
BUCKET_NAME="book-library-static-${ENVIRONMENT}-${AWS_ACCOUNT_ID}"

echo "========================================="
echo "Deploying Static Website to S3"
echo "========================================="
echo "Bucket: ${BUCKET_NAME}"
echo "Region: ${REGION}"
echo "========================================="

# Create temporary directory for static files
STATIC_DIR="${SCRIPT_DIR}/static-build"
rm -rf "${STATIC_DIR}"
mkdir -p "${STATIC_DIR}"

# Copy templates (these will be served by Lambda, but keeping for reference)
echo "Preparing static files..."
cp -r "${PROJECT_ROOT}/templates" "${STATIC_DIR}/"

# Create a simple index.html for the S3 bucket root
cat > "${STATIC_DIR}/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Library</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }
        .container {
            background: #f5f5f5;
            padding: 40px;
            border-radius: 10px;
        }
        h1 { color: #333; }
        p { color: #666; }
        a {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
        a:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Book Library</h1>
        <p>Welcome to your personal book library application!</p>
        <p>This application is powered by AWS Lambda, API Gateway, and DynamoDB.</p>
        <a href="#" id="apiLink">Go to Application</a>
    </div>
    <script>
        // Update this with your API Gateway endpoint after deployment
        document.getElementById('apiLink').href = 'API_ENDPOINT_PLACEHOLDER';
    </script>
</body>
</html>
EOF

# Create error page
cat > "${STATIC_DIR}/error.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - Book Library</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }
        h1 { color: #dc3545; }
        p { color: #666; }
    </style>
</head>
<body>
    <h1>⚠️ Error</h1>
    <p>Something went wrong. Please try again later.</p>
</body>
</html>
EOF

echo "Uploading files to S3..."
aws s3 sync "${STATIC_DIR}" s3://${BUCKET_NAME}/ \
  --region ${REGION} \
  --delete \
  --cache-control "max-age=3600"

echo "Setting content types..."
aws s3 cp s3://${BUCKET_NAME}/ s3://${BUCKET_NAME}/ \
  --recursive \
  --exclude "*" \
  --include "*.html" \
  --content-type "text/html" \
  --metadata-directive REPLACE \
  --region ${REGION}

WEBSITE_URL="http://${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com"

echo "========================================="
echo "Static Website Deployment Complete!"
echo "========================================="
echo "Website URL: ${WEBSITE_URL}"
echo "========================================="

# Cleanup
rm -rf "${STATIC_DIR}"

echo "Deployment artifacts cleaned up."
