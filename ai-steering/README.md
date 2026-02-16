# Book Library Documentation

This folder is the single source of truth for project documentation.

- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/ai-steering/README.md`: operational quick reference and project status
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/ai-steering/DEVELOPMENT_GUIDE.md`: full technical guide

## Project Summary

Book Library is a Flask web app for personal book tracking.

Core capabilities:
- User registration/login/logout
- Add/edit/delete/list books
- Reading status (`to-read`, `reading`, `read`)
- Ratings (`1-5`)
- Metadata sync by ISBN

Deployment models:
- Local: Flask + SQLite + SQLAlchemy
- AWS: API Gateway + Lambda + DynamoDB + SQS

## Current Progress

Completed:
- Local application features implemented
- Serverless AWS adaptation implemented (`app_lambda.py`, `lambda_handler.py`, DynamoDB models, SQS worker)
- Infrastructure-as-code and deployment scripts implemented
- AWS files reorganized by concern:
  - App code: `app/aws_lambda/`
  - Infra: `infra/aws/`
  - Scripts: `scripts/aws/`
  - AWS tests: `tests/aws/`

Known limitation:
- Barcode scanning is disabled in Lambda packaging until binary dependencies are provided for Amazon Linux 2.

## Latest Validation (February 16, 2026)

- Local tests: `./venv/bin/python -m pytest -q` -> `16 passed`
- Live deploy: `./scripts/aws/deploy.sh dev` completed successfully in `us-west-2`
- Live API checks passed:
  - `GET /health` -> `200` with `{"status":"healthy"}`
  - `GET /home` -> `200`
  - `GET /login` -> `200`

## Quick Start (Local)

```bash
cd /Users/bruce/Documents/Projects/HomeLibrary/home-library
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
flask run
```

App URL: `http://127.0.0.1:5000`

## Quick Deploy (AWS)

```bash
export AWS_REGION=us-west-2
export SECRET_KEY=$(openssl rand -base64 32)

cd /Users/bruce/Documents/Projects/HomeLibrary/home-library
./scripts/aws/deploy.sh dev
```

Get endpoint:

```bash
aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --region us-west-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

Health check:

```bash
curl "$(aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --region us-west-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)/health"
```

## Operations Quick Reference

Logs:

```bash
aws logs tail /aws/lambda/BookLibrary-API-dev --region us-west-2 --follow
aws logs tail /aws/lambda/BookLibrary-MetadataWorker-dev --region us-west-2 --follow
```

Stack status:

```bash
aws cloudformation describe-stacks --stack-name BookLibrary-dev --region us-west-2 --query 'Stacks[0].StackStatus'
```

Update code:

```bash
cd /Users/bruce/Documents/Projects/HomeLibrary/home-library
./scripts/aws/deploy.sh dev
```

Cleanup:

```bash
aws cloudformation delete-stack --stack-name BookLibrary-dev --region us-west-2
aws cloudformation wait stack-delete-complete --stack-name BookLibrary-dev --region us-west-2
```

## Critical Notes

- Do not set `AWS_REGION` as a Lambda environment variable (reserved by AWS).
- Lambda creates its CloudWatch log groups automatically.
- Lambda binary dependencies must be compiled for Amazon Linux 2.
- Save and reuse `SECRET_KEY` for stable session behavior across redeployments. If this value changes, all existing user sessions are invalidated.
- For API Gateway HTTP API v2, session cookies must be read from `event.cookies` and mapped to WSGI `HTTP_COOKIE` in `app/aws_lambda/lambda_handler.py` (already implemented).

## Cost and Security Snapshot

Expected low-usage cost: about `$2-5/month`.

Security baseline in place:
- Password hashing (PBKDF2-SHA256)
- HTTPS via API Gateway
- IAM role-based AWS access
- Secure session cookie settings

## Where to Find Deep Details

Use `/Users/bruce/Documents/Projects/HomeLibrary/home-library/ai-steering/DEVELOPMENT_GUIDE.md` for:
- Architecture and data flows
- Full file map
- Deployment checklist
- Troubleshooting runbook
- SQLite to DynamoDB migration procedure
- Local vs AWS behavior differences
