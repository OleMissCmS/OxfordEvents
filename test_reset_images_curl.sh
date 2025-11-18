#!/bin/bash
# Script to test the admin reset-images endpoint on Render
# Usage: ./test_reset_images_curl.sh <admin_username> <admin_password>

BASE_URL="https://oxfordevents.onrender.com"
USERNAME="${1:-CmSCMU}"
PASSWORD="${2}"

if [ -z "$PASSWORD" ]; then
    echo "Usage: $0 <username> <password>"
    echo "Example: $0 CmSCMU your_password"
    exit 1
fi

echo "Step 1: Logging in to get session cookie..."
# Login and save cookies
COOKIE_JAR=$(mktemp)
LOGIN_RESPONSE=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
    -X POST "$BASE_URL/admin/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$USERNAME" \
    -d "password=$PASSWORD" \
    -d "next=/admin/dashboard" \
    -L -w "\n%{http_code}")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" != "200" ]; then
    echo "ERROR: Login failed with HTTP $HTTP_CODE"
    echo "Response: $LOGIN_RESPONSE"
    rm -f "$COOKIE_JAR"
    exit 1
fi

echo "Login successful!"

echo ""
echo "Step 2: Calling reset-images endpoint..."
RESET_RESPONSE=$(curl -s -b "$COOKIE_JAR" \
    -X POST "$BASE_URL/api/admin/reset-images" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESET_RESPONSE" | tail -n1)
BODY=$(echo "$RESET_RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "Response:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

rm -f "$COOKIE_JAR"

if [ "$HTTP_CODE" = "200" ]; then
    echo ""
    echo "SUCCESS: Images reset successfully!"
    exit 0
else
    echo ""
    echo "ERROR: Reset failed"
    exit 1
fi

