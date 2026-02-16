#!/usr/bin/env python3
"""Decode Flask session cookie"""
import sys
from itsdangerous import URLSafeTimedSerializer

# The session cookie from the test
session_cookie = ".eJwtjktqAzEQBa9ieu0Jav01Z8gNgjGt1uvYYGKwPCvju2cgWT2KR0G96Gw3mRdMWr9edHjuQ3NTxZx0pM_79_Xn8M-23T7o9D4dd-eBeaH1-diw03XQSh25R-EiiLGVxGH0rmhNYD1YG6E3ZKloOZcSrBvbiNKLiuakyFqyiEMzl11M7LzjmpirjFjM5xQ4qcX9bKECGoaZr3CJTaQx_F573iYefzXgGtBdWTxKXaJPvDSrWJw6uFyLV1V6_wJFqEsU.aZFYOQ.psVrbG3XlCPL5h1ucY6zwV2B3f4"

# Try to decode with a test secret key
secret_key = "Ha38lr5PtAw3FYZDGvbCR/1IaA2C7xLwHx7PJJ0C4sg="

serializer = URLSafeTimedSerializer(secret_key)

try:
    data = serializer.loads(session_cookie)
    print("Session data:")
    print(data)
except Exception as e:
    print(f"Error decoding: {e}")
    print("\nTrying to decode without verification...")
    try:
        # Just decode the payload without verification
        import base64
        import zlib
        payload = session_cookie.split('.')[0]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        try:
            decompressed = zlib.decompress(decoded)
            print(f"Decompressed: {decompressed}")
        except:
            print(f"Raw decoded: {decoded}")
    except Exception as e2:
        print(f"Also failed: {e2}")
