"""
Local testing script for Lambda functions.
Simulates API Gateway events and tests Lambda handler locally.
"""
import json
import sys
import os
from pathlib import Path

# Add Lambda source directory to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAMBDA_SRC_DIR = PROJECT_ROOT / "app" / "aws_lambda"
sys.path.insert(0, str(LAMBDA_SRC_DIR))

# Set environment variables for local testing
os.environ['ENVIRONMENT'] = 'local'
os.environ['SECRET_KEY'] = 'test-secret-key-for-local-development'
os.environ['USERS_TABLE'] = 'BookLibrary-Users-dev'
os.environ['BOOKS_TABLE'] = 'BookLibrary-Books-dev'
os.environ['USER_BOOKS_TABLE'] = 'BookLibrary-UserBooks-dev'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['METADATA_QUEUE_URL'] = ''  # Empty for local testing

from lambda_handler import lambda_handler


def create_api_gateway_event(method='GET', path='/', body=None, headers=None):
    """Create a mock API Gateway event"""
    event = {
        'requestContext': {
            'http': {
                'method': method,
                'path': path,
                'sourceIp': '127.0.0.1'
            },
            'requestId': 'test-request-id',
            'accountId': '123456789012'
        },
        'headers': headers or {
            'content-type': 'application/json',
            'host': 'localhost'
        },
        'queryStringParameters': None,
        'body': json.dumps(body) if body else None,
        'isBase64Encoded': False
    }
    return event


def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    event = create_api_gateway_event('GET', '/health')
    context = {}
    
    response = lambda_handler(event, context)
    print(f"Status: {response['statusCode']}")
    print(f"Body: {response['body']}")
    assert response['statusCode'] == 200
    print("✓ Health check passed")


def test_home_page():
    """Test home page"""
    print("\n=== Testing Home Page ===")
    event = create_api_gateway_event('GET', '/home')
    context = {}
    
    response = lambda_handler(event, context)
    print(f"Status: {response['statusCode']}")
    print(f"Body length: {len(response['body'])} characters")
    assert response['statusCode'] == 200
    print("✓ Home page test passed")


def test_register_page():
    """Test register page GET"""
    print("\n=== Testing Register Page (GET) ===")
    event = create_api_gateway_event('GET', '/register')
    context = {}
    
    response = lambda_handler(event, context)
    print(f"Status: {response['statusCode']}")
    assert response['statusCode'] == 200
    print("✓ Register page test passed")


def test_login_page():
    """Test login page GET"""
    print("\n=== Testing Login Page (GET) ===")
    event = create_api_gateway_event('GET', '/login')
    context = {}
    
    response = lambda_handler(event, context)
    print(f"Status: {response['statusCode']}")
    assert response['statusCode'] == 200
    print("✓ Login page test passed")


def main():
    """Run all tests"""
    print("=" * 50)
    print("Local Lambda Function Testing")
    print("=" * 50)
    print("\nNote: Make sure you have AWS credentials configured")
    print("and DynamoDB tables created in your AWS account.\n")
    
    try:
        test_health_check()
        test_home_page()
        test_register_page()
        test_login_page()
        
        print("\n" + "=" * 50)
        print("All tests passed! ✓")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
