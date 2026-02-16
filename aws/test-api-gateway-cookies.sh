#!/bin/bash

API="https://hpfao6gnvl.execute-api.us-west-2.amazonaws.com"

echo "Testing API Gateway Cookie Handling"
echo "===================================="

# Step 1: Make a request and save cookies
echo -e "\n1. Making initial request to /home..."
curl -c /tmp/cookies.txt -s -o /dev/null -w "HTTP Status: %{http_code}\n" "$API/home"

echo -e "\n2. Checking saved cookies..."
cat /tmp/cookies.txt

# Step 2: Login and save the session cookie
echo -e "\n3. Logging in..."
curl -c /tmp/cookies.txt -b /tmp/cookies.txt -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  -X POST "$API/login" \
  -d "email=test@example.com&password=test123"

echo -e "\n4. Checking cookies after login..."
cat /tmp/cookies.txt

# Step 3: Make a request with the cookie
echo -e "\n5. Making request to /home with cookie..."
curl -b /tmp/cookies.txt -v "$API/home" 2>&1 | grep -E "Cookie:|HTTP/2"

# Cleanup
rm -f /tmp/cookies.txt
