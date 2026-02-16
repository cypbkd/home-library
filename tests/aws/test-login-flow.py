#!/usr/bin/env python3
"""
Test script to verify login flow and session handling
"""
import requests
import sys

# API endpoint
API_ENDPOINT = "https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com"

def test_login_flow():
    """Test the complete login flow"""
    print("=" * 60)
    print("Testing Book Library Login Flow")
    print("=" * 60)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Access home page (unauthenticated)
    print("\n1. Accessing home page (unauthenticated)...")
    response = session.get(f"{API_ENDPOINT}/home")
    print(f"   Status: {response.status_code}")
    print(f"   Cookies received: {session.cookies.get_dict()}")
    
    if "Login" in response.text and "Register" in response.text:
        print("   ✓ Unauthenticated home page shows Login/Register")
    else:
        print("   ✗ Expected Login/Register buttons not found")
    
    # Step 2: Register a test user
    print("\n2. Registering test user...")
    test_email = f"test_{int(requests.utils.default_headers()['User-Agent'].__hash__())}@example.com"
    test_username = f"testuser_{int(requests.utils.default_headers()['User-Agent'].__hash__())}"
    test_password = "TestPassword123!"
    
    register_data = {
        'username': test_username,
        'email': test_email,
        'password': test_password,
        'confirm_password': test_password
    }
    
    response = session.post(f"{API_ENDPOINT}/register", data=register_data, allow_redirects=False)
    print(f"   Status: {response.status_code}")
    print(f"   Location: {response.headers.get('Location', 'N/A')}")
    print(f"   Cookies: {session.cookies.get_dict()}")
    
    if response.status_code in [302, 303]:
        print(f"   ✓ Registration redirect successful")
    else:
        print(f"   ✗ Registration failed")
        print(f"   Response: {response.text[:500]}")
    
    # Step 3: Login with the test user
    print("\n3. Logging in with test user...")
    login_data = {
        'email': test_email,
        'password': test_password
    }
    
    response = session.post(f"{API_ENDPOINT}/login", data=login_data, allow_redirects=False)
    print(f"   Status: {response.status_code}")
    print(f"   Location: {response.headers.get('Location', 'N/A')}")
    print(f"   Set-Cookie headers: {response.headers.get('Set-Cookie', 'N/A')}")
    print(f"   Session cookies: {session.cookies.get_dict()}")
    
    if response.status_code in [302, 303]:
        print(f"   ✓ Login redirect successful")
    else:
        print(f"   ✗ Login failed")
        print(f"   Response: {response.text[:500]}")
        return False
    
    # Step 4: Follow redirect to home page (authenticated)
    print("\n4. Accessing home page after login...")
    response = session.get(f"{API_ENDPOINT}/home")
    print(f"   Status: {response.status_code}")
    print(f"   Cookies: {session.cookies.get_dict()}")
    
    # Check for authenticated content
    if "My Books" in response.text and "Add Book" in response.text:
        print("   ✓ Authenticated home page shows My Books/Add Book")
        print("   ✓ LOGIN FLOW WORKING CORRECTLY!")
        success = True
    elif "Login" in response.text and "Register" in response.text:
        print("   ✗ Still showing Login/Register (session not maintained)")
        print("   ✗ LOGIN FLOW FAILED - Session not persisting")
        success = False
    else:
        print("   ? Unexpected content")
        success = False
    
    # Step 5: Try to access protected route
    print("\n5. Accessing protected route (/books)...")
    response = session.get(f"{API_ENDPOINT}/books", allow_redirects=False)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✓ Can access protected route (authenticated)")
    elif response.status_code in [302, 303]:
        print(f"   ✗ Redirected to: {response.headers.get('Location', 'N/A')}")
        print("   ✗ Not authenticated - session lost")
    else:
        print(f"   ? Unexpected status: {response.status_code}")
    
    # Step 6: Check session cookie details
    print("\n6. Session cookie analysis...")
    for cookie in session.cookies:
        print(f"   Cookie: {cookie.name}")
        print(f"     Value: {cookie.value[:50]}...")
        print(f"     Domain: {cookie.domain}")
        print(f"     Path: {cookie.path}")
        print(f"     Secure: {cookie.secure}")
        print(f"     HttpOnly: {cookie.has_nonstandard_attr('HttpOnly')}")
    
    print("\n" + "=" * 60)
    if success:
        print("TEST PASSED: Login flow working correctly")
    else:
        print("TEST FAILED: Session not persisting after login")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    try:
        success = test_login_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
