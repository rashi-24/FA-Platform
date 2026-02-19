#!/bin/bash

# Login and get token
echo "=== Testing Login ==="
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"Demo@Pass123!"}')

echo "Login Response: $LOGIN_RESPONSE"

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "ERROR: No token received"
  exit 1
fi

echo -e "\n=== Token Extracted ==="
echo "Token (first 50 chars): ${TOKEN:0:50}..."

# Test /api/auth/me
echo -e "\n=== Testing /api/auth/me ==="
ME_RESPONSE=$(curl -s -X GET http://localhost:3000/api/auth/me \
  -H "Authorization: Bearer $TOKEN")

echo "Me Response: $ME_RESPONSE"

# Also test directly against backend (bypassing nginx)
echo -e "\n=== Testing directly against backend (port 8000) ==="
DIRECT_RESPONSE=$(curl -s -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN")

echo "Direct Backend Response: $DIRECT_RESPONSE"
