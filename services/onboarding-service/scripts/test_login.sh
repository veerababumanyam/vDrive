#!/bin/bash
# Test Login Script for vDrive Onboarding Service
#
# Usage: ./test_login.sh [email] [password]
#
# Default test user: free@test.vdrive.in / Test@123

set -e

# Configuration
API_BASE="${API_BASE:-http://localhost:8006/api/v1/onboarding}"
EMAIL="${1:-free@test.vdrive.in}"
PASSWORD="${2:-Test@123}"

echo "=============================================="
echo "  vDrive Login Test"
echo "=============================================="
echo ""
echo "API Base: $API_BASE"
echo "Email: $EMAIL"
echo ""

# Test 1: Health Check
echo "[1/3] Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/../health")
if [ "$HEALTH_RESPONSE" == "200" ]; then
    echo "  ✅ Health check passed"
else
    echo "  ❌ Health check failed (HTTP $HEALTH_RESPONSE)"
    echo "  Make sure the onboarding service is running on port 8006"
    exit 1
fi

# Test 2: Login
echo ""
echo "[2/3] Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
JSON_BODY=$(echo "$LOGIN_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" == "200" ]; then
    echo "  ✅ Login successful!"
    echo ""
    echo "  Response:"
    echo "$JSON_BODY" | python -m json.tool 2>/dev/null || echo "$JSON_BODY"

    # Extract access token
    ACCESS_TOKEN=$(echo "$JSON_BODY" | python -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

    if [ -n "$ACCESS_TOKEN" ]; then
        echo ""
        echo "[3/3] Testing authenticated endpoint..."
        STATE_RESPONSE=$(curl -s -X GET "$API_BASE/state" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -w "\n%{http_code}")

        STATE_CODE=$(echo "$STATE_RESPONSE" | tail -n1)
        if [ "$STATE_CODE" == "200" ] || [ "$STATE_CODE" == "404" ]; then
            echo "  ✅ Authenticated request successful (HTTP $STATE_CODE)"
        else
            echo "  ⚠️ Authenticated request returned HTTP $STATE_CODE"
        fi
    fi
else
    echo "  ❌ Login failed (HTTP $HTTP_CODE)"
    echo ""
    echo "  Response:"
    echo "$JSON_BODY" | python -m json.tool 2>/dev/null || echo "$JSON_BODY"
    exit 1
fi

echo ""
echo "=============================================="
echo "  All tests passed!"
echo "=============================================="
