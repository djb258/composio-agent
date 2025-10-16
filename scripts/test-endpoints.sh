#!/bin/bash

# Composio Agent Gateway - Endpoint Testing Script
# Tests all endpoints to verify deployment

set -e

# Configuration
BASE_URL="${BASE_URL:-https://composio-imo-creator-url.onrender.com}"
VERBOSE="${VERBOSE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Composio Agent Gateway - Endpoint Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Testing service at: $BASE_URL"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# Function to print test result
print_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"

    if [ "$status" == "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
        [ "$VERBOSE" == "true" ] && echo "  $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} - $test_name"
        echo -e "  ${RED}$message${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test 1: Status Endpoint
echo -e "${YELLOW}Testing /status endpoint...${NC}"
STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/status")
STATUS_CODE=$(echo "$STATUS_RESPONSE" | tail -n 1)
STATUS_BODY=$(echo "$STATUS_RESPONSE" | sed '$d')

if [ "$STATUS_CODE" == "200" ]; then
    print_result "/status returns 200" "PASS" "Response: $STATUS_BODY"
else
    print_result "/status returns 200" "FAIL" "Expected 200, got $STATUS_CODE"
fi

# Test 2: Status Response Contains Required Fields
if echo "$STATUS_BODY" | grep -q '"status"'; then
    print_result "/status contains 'status' field" "PASS"
else
    print_result "/status contains 'status' field" "FAIL" "Missing 'status' field"
fi

if echo "$STATUS_BODY" | grep -q '"service":"composio-agent"'; then
    print_result "/status service is 'composio-agent'" "PASS"
else
    print_result "/status service is 'composio-agent'" "FAIL" "Service field incorrect or missing"
fi

# Test 3: Schema Endpoint
echo ""
echo -e "${YELLOW}Testing /schema endpoint...${NC}"
SCHEMA_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/schema")
SCHEMA_CODE=$(echo "$SCHEMA_RESPONSE" | tail -n 1)
SCHEMA_BODY=$(echo "$SCHEMA_RESPONSE" | sed '$d')

if [ "$SCHEMA_CODE" == "200" ]; then
    print_result "/schema returns 200" "PASS" "Response length: ${#SCHEMA_BODY} chars"
else
    print_result "/schema returns 200" "FAIL" "Expected 200, got $SCHEMA_CODE"
fi

# Test 4: Schema Contains Tools
if echo "$SCHEMA_BODY" | grep -q '"tools"'; then
    print_result "/schema contains 'tools' field" "PASS"
else
    print_result "/schema contains 'tools' field" "FAIL" "Missing 'tools' field"
fi

# Test 5: Schema Contains Expected Tools
if echo "$SCHEMA_BODY" | grep -q '"firebase_read"'; then
    print_result "/schema contains 'firebase_read' tool" "PASS"
else
    print_result "/schema contains 'firebase_read' tool" "FAIL" "Missing firebase_read tool"
fi

if echo "$SCHEMA_BODY" | grep -q '"firebase_write"'; then
    print_result "/schema contains 'firebase_write' tool" "PASS"
else
    print_result "/schema contains 'firebase_write' tool" "FAIL" "Missing firebase_write tool"
fi

# Test 6: Invoke Endpoint (Validation Test - Missing Fields)
echo ""
echo -e "${YELLOW}Testing /invoke endpoint validation...${NC}"
INVOKE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/invoke" \
    -H "Content-Type: application/json" \
    -d '{"tool":"firebase_read","data":{}}')
INVOKE_CODE=$(echo "$INVOKE_RESPONSE" | tail -n 1)
INVOKE_BODY=$(echo "$INVOKE_RESPONSE" | sed '$d')

if [ "$INVOKE_CODE" == "400" ]; then
    print_result "/invoke validates required fields" "PASS" "Correctly rejects invalid request"
else
    print_result "/invoke validates required fields" "FAIL" "Expected 400 for missing fields, got $INVOKE_CODE"
fi

if echo "$INVOKE_BODY" | grep -q '"error"'; then
    print_result "/invoke returns error message" "PASS"
else
    print_result "/invoke returns error message" "FAIL" "Missing error field in validation response"
fi

# Test 7: Response Time Check
echo ""
echo -e "${YELLOW}Testing response time...${NC}"
START_TIME=$(date +%s%N)
curl -s "$BASE_URL/status" > /dev/null
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))

if [ "$RESPONSE_TIME" -lt 3000 ]; then
    print_result "Response time < 3s" "PASS" "${RESPONSE_TIME}ms"
else
    print_result "Response time < 3s" "FAIL" "${RESPONSE_TIME}ms (too slow)"
fi

# Test 8: HTTPS Check
echo ""
echo -e "${YELLOW}Testing HTTPS...${NC}"
if [[ "$BASE_URL" == https://* ]]; then
    print_result "Service uses HTTPS" "PASS"
else
    print_result "Service uses HTTPS" "FAIL" "URL should use HTTPS"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo "Total: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
