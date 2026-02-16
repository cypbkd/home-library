"""
AWS Lambda handler for the Book Library application.
Handles API Gateway events and routes them to Flask app.
"""
import json
import base64
from app_lambda import app

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    Converts API Gateway event to WSGI-compatible format and invokes Flask app.
    """
    
    # Handle different event formats (API Gateway v1 vs v2)
    if 'requestContext' in event:
        if 'http' in event['requestContext']:
            # API Gateway HTTP API (v2)
            return handle_http_api_v2(event, context)
        else:
            # API Gateway REST API (v1)
            return handle_rest_api_v1(event, context)
    
    return {
        'statusCode': 400,
        'body': json.dumps({'error': 'Invalid event format'})
    }


def handle_rest_api_v1(event, context):
    """Handle API Gateway REST API (v1) events"""
    from werkzeug.wrappers import Request, Response
    from io import BytesIO
    
    # Extract request details
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    headers = event.get('headers', {})
    
    print(f"[DEBUG] Request: {http_method} {path}")
    print(f"[DEBUG] Event headers keys: {list(headers.keys())}")
    print(f"[DEBUG] Cookie in headers: {'cookie' in headers or 'Cookie' in headers}")
    if 'cookie' in headers or 'Cookie' in headers:
        print(f"[DEBUG] Cookie value: {headers.get('cookie', headers.get('Cookie', 'NONE'))}")
    
    # Check for cookies in multiValueHeaders
    multi_headers = event.get('multiValueHeaders', {})
    if multi_headers:
        print(f"[DEBUG] multiValueHeaders keys: {list(multi_headers.keys())}")
        if 'cookie' in multi_headers or 'Cookie' in multi_headers:
            print(f"[DEBUG] Cookie in multiValueHeaders: {multi_headers.get('cookie', multi_headers.get('Cookie'))}")
    
    query_params = event.get('queryStringParameters') or {}
    body = event.get('body', '')
    is_base64 = event.get('isBase64Encoded', False)
    
    # Decode body if base64 encoded
    if is_base64 and body:
        body = base64.b64decode(body)
    elif body:
        body = body.encode('utf-8')
    else:
        body = b''
    
    # Build query string
    query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
    
    # Create WSGI environment
    environ = {
        'REQUEST_METHOD': http_method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'CONTENT_TYPE': headers.get('content-type', headers.get('Content-Type', '')),
        'CONTENT_LENGTH': str(len(body)),
        'SERVER_NAME': headers.get('Host', 'lambda'),
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(body),
        'wsgi.errors': BytesIO(),
        'wsgi.multiprocess': False,
        'wsgi.multithread': False,
        'wsgi.run_once': False,
    }
    
    # Add headers to environ
    for key, value in headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # Call Flask app with both app and request context
    with app.app_context():
        with app.request_context(environ):
            try:
                response = app.full_dispatch_request()
            except Exception as e:
                print(f"Error processing request: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    # Convert Flask response to API Gateway format
    response_body = response.get_data(as_text=True)
    
    # Convert headers to proper format and handle Set-Cookie
    response_headers = {}
    cookies = []
    for key, value in response.headers:
        if key.lower() == 'set-cookie':
            cookies.append(value)
        else:
            response_headers[key] = value
    
    result = {
        'statusCode': response.status_code,
        'headers': response_headers,
        'body': response_body,
        'isBase64Encoded': False
    }
    
    # Add cookies if present
    if cookies:
        result['multiValueHeaders'] = {'Set-Cookie': cookies}
    
    return result


def handle_http_api_v2(event, context):
    """Handle API Gateway HTTP API (v2) events"""
    from werkzeug.wrappers import Request, Response
    from io import BytesIO
    
    # Extract request details
    request_context = event['requestContext']
    http = request_context['http']
    
    http_method = http['method']
    path = http['path']
    headers = event.get('headers', {})
    query_params = event.get('queryStringParameters') or {}
    body = event.get('body', '')
    is_base64 = event.get('isBase64Encoded', False)
    
    # Decode body if base64 encoded
    if is_base64 and body:
        body = base64.b64decode(body)
    elif body:
        body = body.encode('utf-8')
    else:
        body = b''
    
    # Build query string
    query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
    
    # Create WSGI environment
    environ = {
        'REQUEST_METHOD': http_method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'CONTENT_TYPE': headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(body)),
        'SERVER_NAME': headers.get('host', 'lambda'),
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': BytesIO(body),
        'wsgi.errors': BytesIO(),
        'wsgi.multiprocess': False,
        'wsgi.multithread': False,
        'wsgi.run_once': False,
    }
    
    # Add headers to environ
    for key, value in headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # Call Flask app with both app and request context
    with app.app_context():
        with app.request_context(environ):
            try:
                response = app.full_dispatch_request()
            except Exception as e:
                print(f"Error processing request: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    # Convert Flask response to API Gateway format
    response_body = response.get_data(as_text=True)
    
    # Convert headers to proper format and handle Set-Cookie
    response_headers = {}
    cookies = []
    for key, value in response.headers:
        if key.lower() == 'set-cookie':
            cookies.append(value)
        else:
            response_headers[key] = value
    
    result = {
        'statusCode': response.status_code,
        'headers': response_headers,
        'body': response_body,
        'isBase64Encoded': False
    }
    
    # Add cookies if present
    if cookies:
        result['cookies'] = cookies
    
    return result
