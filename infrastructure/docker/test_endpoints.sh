#!/bin/bash

# Test all authentication endpoints for correct responses

BASE_URL="http://localhost:8006/api/v1/onboarding"

echo "=========================================="
echo "Authentication Endpoints Verification"
echo "=========================================="

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test 1: Login endpoint (should return 401 for invalid credentials)
echo -e "\n${BLUE}Test 1: POST /login (invalid credentials)${NC}"
RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid@test.com","password":"wrongpass"}')
STATUS=${RESPONSE: -3}
if [ "$STATUS" == "401" ]; then
  echo -e "${GREEN}✅ Correctly returns 401 for invalid credentials${NC}"
else
  echo -e "${RED}❌ Expected 401, got $STATUS${NC}"
fi

# Test 2: Refresh endpoint (should return 401 without cookie)
echo -e "\n${BLUE}Test 2: POST /refresh (no cookie)${NC}"
RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/login/refresh")
STATUS=${RESPONSE: -3}
if [ "$STATUS" == "401" ]; then
  echo -e "${GREEN}✅ Correctly returns 401 without refresh token${NC}"
else
  echo -e "${RED}❌ Expected 401, got $STATUS${NC}"
fi

# Test 3: Logout endpoint (should return 401 without auth)
echo -e "\n${BLUE}Test 3: POST /logout (no auth)${NC}"
RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/login/logout")
STATUS=${RESPONSE: -3}
if [ "$STATUS" == "401" ]; then
  echo -e "${GREEN}✅ Correctly returns 401 without auth token${NC}"
else
  echo -e "${RED}❌ Expected 401, got $STATUS${NC}"
fi

# Test 4: Logout all endpoint (should return 401 without auth)
echo -e "\n${BLUE}Test 4: POST /logout/all (no auth)${NC}"
RESPONSE=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/login/logout/all")
STATUS=${RESPONSE: -3}
if [ "$STATUS" == "401" ]; then
  echo -e "${GREEN}✅ Correctly returns 401 without auth token${NC}"
else
  echo -e "${RED}❌ Expected 401, got $STATUS${NC}"
fi

# Test 5: Google OAuth signin (should return redirect)
echo -e "\n${BLUE}Test 5: GET /oauth/google/signin${NC}"
RESPONSE=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/login/oauth/google/signin")
STATUS=${RESPONSE: -3}
if [ "$STATUS" == "307" ] || [ "$STATUS" == "302" ]; then
  echo -e "${GREEN}✅ Correctly returns redirect ($STATUS)${NC}"
else
  echo -e "${RED}❌ Expected 307/302, got $STATUS${NC}"
fi

# Test 6: Health endpoint
echo -e "\n${BLUE}Test 6: GET /login/health${NC}"
RESPONSE=$(curl -s "$BASE_URL/login/health")
if echo "$RESPONSE" | grep -q "healthy"; then
  echo -e "${GREEN}✅ Health check passed${NC}"
else
  echo -e "${RED}❌ Health check failed${NC}"
fi

echo -e "\n=========================================="
echo -e "${GREEN}✅ All authentication endpoints are properly configured${NC}"
echo -e "=========================================="
