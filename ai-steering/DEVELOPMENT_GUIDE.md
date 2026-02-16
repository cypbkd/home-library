# Book Library Development Guide

This is the detailed technical guide for development, deployment, and operations.

## 1. System Overview

Book Library supports two execution modes.

Local mode:
- Flask application (`app.py`)
- SQLite via SQLAlchemy (`models.py`)
- Background task behavior in local process (`tasks.py`)

AWS mode:
- API Gateway (HTTP API)
- Lambda API handler (`lambda_handler.py` + `app_lambda.py`)
- DynamoDB data layer (`dynamodb_models.py`)
- SQS-driven metadata worker (`tasks_lambda.py`)

## 2. Repository Structure

Main application:
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/app.py`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/models.py`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/tasks.py`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/templates/`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/tests/`

AWS deployment:
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/infra/aws/cloudformation-template.yaml`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/scripts/aws/deploy.sh`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/scripts/aws/update-stack.sh`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/scripts/aws/deploy-static.sh`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/app/aws_lambda/lambda_handler.py`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/app/aws_lambda/app_lambda.py`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/app/aws_lambda/dynamodb_models.py`
- `/Users/bruce/Documents/Projects/HomeLibrary/home-library/app/aws_lambda/tasks_lambda.py`

## 3. Architecture and Data Model

### 3.1 Request Path (AWS)

1. Client sends HTTPS request to API Gateway.
2. API Gateway invokes `BookLibrary-API-{env}` Lambda.
3. Flask route executes in Lambda runtime.
4. Data is read/written in DynamoDB.
5. Metadata work is queued to SQS when needed.
6. Worker Lambda consumes queue and updates records.

### 3.2 DynamoDB Tables

- `BookLibrary-Users-{env}`
  - User identity and login fields
  - Secondary indexes for email/username lookup
- `BookLibrary-Books-{env}`
  - Book metadata keyed for ISBN/book lookup
- `BookLibrary-UserBooks-{env}`
  - Per-user book relations (status, rating, sync state)

### 3.3 Security Model

- Password hashes, never plaintext
- HTTPS-only public API endpoint
- IAM role permissions scoped to required services
- Session cookies with secure settings

## 4. Local Development Workflow

Prerequisites:
- Python 3.8+
- `pip`

Setup:

```bash
cd /Users/bruce/Documents/Projects/HomeLibrary/home-library
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Database migration:

```bash
flask db upgrade
```

Run:

```bash
flask run
```

Tests:

```bash
./venv/bin/python -m pytest -q
```

## 5. AWS Deployment Workflow

### 5.1 Pre-Deployment Checks

- AWS CLI is installed and authenticated (`aws sts get-caller-identity`)
- Region selected (default used in docs: `us-west-2`)
- `SECRET_KEY` generated and saved

### 5.2 Deploy

```bash
cd /Users/bruce/Documents/Projects/HomeLibrary/home-library
export AWS_REGION=us-west-2
export SECRET_KEY=$(openssl rand -base64 32)
./scripts/aws/deploy.sh dev
```

### 5.3 Verify

```bash
aws cloudformation describe-stacks --stack-name BookLibrary-dev --region us-west-2 --query 'Stacks[0].StackStatus'
aws lambda list-functions --region us-west-2 --query 'Functions[?starts_with(FunctionName, `BookLibrary`)].FunctionName'
aws dynamodb list-tables --region us-west-2 | grep BookLibrary
```

### 5.4 Smoke Tests

```bash
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name BookLibrary-dev \
  --region us-west-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

curl "$API_ENDPOINT/health"
curl "$API_ENDPOINT/home"
```

Latest verified run (February 16, 2026):
- Local tests: `./venv/bin/python -m pytest -q` -> `16 passed`
- Deployed API endpoint: `https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com`
- Live checks:
  - `GET /health` returned `200` and `{"status":"healthy"}`
  - `GET /home` returned `200`
  - `GET /login` returned `200`

## 6. Operations Runbook

Logs:

```bash
aws logs tail /aws/lambda/BookLibrary-API-dev --region us-west-2 --follow
aws logs tail /aws/lambda/BookLibrary-MetadataWorker-dev --region us-west-2 --follow
```

Queue health:

```bash
aws lambda list-event-source-mappings --function-name BookLibrary-MetadataWorker-dev --region us-west-2
```

Stack events:

```bash
aws cloudformation describe-stack-events --stack-name BookLibrary-dev --region us-west-2
```

Rollback:

```bash
aws cloudformation delete-stack --stack-name BookLibrary-dev --region us-west-2
aws cloudformation wait stack-delete-complete --stack-name BookLibrary-dev --region us-west-2
```

## 7. Troubleshooting

`Unable to locate credentials`:
- Run `aws configure` and validate with `aws sts get-caller-identity`.

`Stack already exists`:
- Delete the old stack or deploy to a different environment name.

Lambda `502`:
- Inspect API Lambda CloudWatch logs first.
- Verify dependencies are in the package root.
- Confirm environment variables are correct.

`AccessDenied` on DynamoDB/SQS/Logs:
- Check IAM role policies for `BookLibrary-Lambda-{env}`.

Login succeeds but user is immediately unauthenticated on next request:
- Cause: API Gateway HTTP API v2 sends cookies via top-level `event.cookies`, not only `headers.cookie`.
- Fix: in `app/aws_lambda/lambda_handler.py` (`handle_http_api_v2`), map `event.cookies` to `environ['HTTP_COOKIE']`.
- Verify: login returns `Set-Cookie`, then `/books` responds `200` (not redirect to `/login`).
- Also ensure `SECRET_KEY` is stable across redeploys; changing it invalidates existing sessions.

## 8. Migration: SQLite to DynamoDB

Recommended path:
1. Backup SQLite (`instance/site.db`).
2. Deploy AWS stack so DynamoDB tables exist.
3. Install migration dependencies.
4. Run migration script against source DB.
5. Validate item counts and functional login/book access.

Validation checks:
- User count parity
- User-book relation count parity
- Spot-check several users and ratings/status values

Rollback options:
- Keep local SQLite as source of truth until validation passes.
- If required, clear migrated DynamoDB data and rerun migration.

## 9. Local vs AWS Behavior

Main differences:
- Database: SQLAlchemy/SQLite vs DynamoDB
- Async model: in-process/threading vs SQS + worker Lambda
- Entry point: Flask process vs Lambda adapter
- Scaling: single host vs automatic serverless scaling
- Cost: local infra cost vs AWS metered cost

Current feature gap:
- Barcode scanning remains disabled in Lambda package due to binary dependencies.

## 10. Cost, Reliability, and Security Guidance

Expected cost:
- Low usage: roughly `$2-5/month`
- Higher usage scales with API Gateway, Lambda duration, DynamoDB R/W, and SQS usage

Reliability recommendations:
- Add CloudWatch alarms for Lambda errors and DLQ depth
- Track API `5XXError` and p95 latency
- Enable backup and restore testing for DynamoDB

Security recommendations:
- Move sensitive values to AWS Secrets Manager for production
- Rotate secrets on a schedule
- Restrict IAM policies to least privilege
- Review auth/session settings before production rollout

## 11. Production Readiness Checklist

- Infrastructure deploys cleanly without manual console fixes
- Health and basic user flows pass after deployment
- Monitoring alarms are configured and tested
- Backup and restore path is documented and tested
- Secrets are externally managed (not shell history)
- Cost budget alarms are configured
- Runbook owner and on-call escalation path are defined

## 12. Contribution Notes

- Keep this guide and `README.md` in sync when process changes.
- Add tests for behavior changes (`/tests` folder).
- Prefer small, reviewable PRs with clear migration/deployment impact notes.
