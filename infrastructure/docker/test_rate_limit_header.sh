#!/bin/bash

# Test rate limit headers

BASE_URL="http://localhost:8006/api/v1/onboarding/login"

echo "=========================================="
echo "Rate Limit Header Test"
echo "=========================================="

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\n${BLUE}Triggering rate limit by making 6 requests...${NC}"

# Make 6 login attempts to trigger rate limit (limit is 5)
for i in {1..6}; do
  echo -e "\nAttempt $i:"
  RESPONSE=$(curl -s -i -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrongpassword123"}' 2>&1)

  STATUS=$(echo "$RESPONSE" | grep "HTTP/" | awk '{print $2}')
  RETRY_AFTER=$(echo "$RESPONSE" | grep -i "retry-after:" | awk '{print $2}' | tr -d '\r')

  echo "  Status: $STATUS"

  if [ "$STATUS" == "429" ]; then
    if [ -n "$RETRY_AFTER" ]; then
      echo -e "  ${GREEN}✅ Retry-After header present: $RETRY_AFTER seconds${NC}"
    else
      echo -e "  ${RED}❌ Retry-After header MISSING${NC}"
    fi

    # Show response body
    BODY=$(echo "$RESPONSE" | grep -A 100 "^{" | head -1)
    echo "  Body: $BODY"
    break
  else
    echo "  No rate limit yet"
  fi

  sleep 0.5
done

echo -e "\n=========================================="
