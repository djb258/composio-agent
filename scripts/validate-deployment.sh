#!/bin/bash

# Composio Agent Gateway - Post-Deploy Validation Script
# Comprehensive validation including /invoke, latency, and log analysis

set -e

# Configuration
BASE_URL="${BASE_URL:-https://composio-imo-creator-url.onrender.com}"
SERVICE_ID="${SERVICE_ID:-srv-d3b7ikje5dus73cba2ng}"
RENDER_API_KEY="${RENDER_API_KEY:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Print header
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Composio Agent - Post-Deploy Validation${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "Service URL: $BASE_URL"
echo "Service ID: $SERVICE_ID"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# Function to run test
run_test() {
    local name="$1"
    local command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${CYAN}[$TOTAL_TESTS] $name${NC}"

    if eval "$command"; then
        echo -e "${GREEN}✓ PASS${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Test 1: Health Check
run_test "Health Check (/status)" '
    RESPONSE=$(curl -s "$BASE_URL/status")
    echo "$RESPONSE" | jq -e ".status == \"ok\"" > /dev/null 2>&1 &&
    echo "$RESPONSE" | jq -e ".service == \"composio-agent\"" > /dev/null 2>&1
'

# Test 2: Schema Availability
run_test "Schema Availability (/schema)" '
    RESPONSE=$(curl -s "$BASE_URL/schema")
    echo "$RESPONSE" | jq -e ".tools | length > 0" > /dev/null 2>&1
'

# Test 3: Response Time - Status
run_test "Response Time - /status (< 2s)" '
    START=$(date +%s%N)
    curl -s "$BASE_URL/status" > /dev/null
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))
    echo "  Latency: ${LATENCY}ms"
    [ $LATENCY -lt 2000 ]
'

# Test 4: Response Time - Schema
run_test "Response Time - /schema (< 3s)" '
    START=$(date +%s%N)
    curl -s "$BASE_URL/schema" > /dev/null
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))
    echo "  Latency: ${LATENCY}ms"
    [ $LATENCY -lt 3000 ]
'

# Test 5: Invoke Validation - Missing agent_id
run_test "Invoke Validation - Missing agent_id" '
    RESPONSE=$(curl -s -X POST "$BASE_URL/invoke" \
        -H "Content-Type: application/json" \
        -d "{\"tool\":\"firebase_read\",\"data\":{}}")
    echo "$RESPONSE" | grep -q "Missing required field: agent_id"
'

# Test 6: Invoke Validation - Missing process_id
run_test "Invoke Validation - Missing process_id" '
    RESPONSE=$(curl -s -X POST "$BASE_URL/invoke" \
        -H "Content-Type: application/json" \
        -d "{\"tool\":\"firebase_read\",\"data\":{\"agent_id\":\"test\"}}")
    echo "$RESPONSE" | grep -q "Missing required field: process_id"
'

# Test 7: Invoke Validation - Missing blueprint_id
run_test "Invoke Validation - Missing blueprint_id" '
    RESPONSE=$(curl -s -X POST "$BASE_URL/invoke" \
        -H "Content-Type: application/json" \
        -d "{\"tool\":\"firebase_read\",\"data\":{\"agent_id\":\"test\",\"process_id\":\"test\"}}")
    echo "$RESPONSE" | grep -q "Missing required field: blueprint_id"
'

# Test 8: Invoke Validation - Missing timestamp_last_touched
run_test "Invoke Validation - Missing timestamp_last_touched" '
    RESPONSE=$(curl -s -X POST "$BASE_URL/invoke" \
        -H "Content-Type: application/json" \
        -d "{\"tool\":\"firebase_read\",\"data\":{\"agent_id\":\"test\",\"process_id\":\"test\",\"blueprint_id\":\"test\"}}")
    echo "$RESPONSE" | grep -q "Missing required field: timestamp_last_touched"
'

# Test 9: HTTPS Certificate
run_test "HTTPS Certificate Valid" '
    curl -s --fail --max-time 5 "$BASE_URL/status" > /dev/null
'

# Test 10: No Error Pages
run_test "No Error Pages (404/500)" '
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/status")
    [ "$STATUS_CODE" == "200" ]
'

# Test 11: Service Uptime Check (if Render API key provided)
if [ -n "$RENDER_API_KEY" ]; then
    run_test "Service Status via Render API" '
        RESPONSE=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
            "https://api.render.com/v1/services/$SERVICE_ID")
        echo "$RESPONSE" | jq -e ".service.state == \"live\"" > /dev/null 2>&1
    '
fi

# Test 12: Tool Definitions Present
run_test "Tool Definitions Present" '
    RESPONSE=$(curl -s "$BASE_URL/schema")
    echo "$RESPONSE" | jq -e ".tools[] | select(.name == \"firebase_read\")" > /dev/null 2>&1 &&
    echo "$RESPONSE" | jq -e ".tools[] | select(.name == \"firebase_write\")" > /dev/null 2>&1 &&
    echo "$RESPONSE" | jq -e ".tools[] | select(.name == \"send_email\")" > /dev/null 2>&1
'

# Test 13: Response Headers Check
run_test "Response Headers Valid" '
    HEADERS=$(curl -s -I "$BASE_URL/status")
    echo "$HEADERS" | grep -q "HTTP.*200" &&
    echo "$HEADERS" | grep -iq "content-type.*application/json"
'

# Test 14: Kill Switch Check
run_test "Kill Switch Status" '
    RESPONSE=$(curl -s "$BASE_URL/status")
    echo "$RESPONSE" | jq -e ".kill_switch == false" > /dev/null 2>&1
'

# Test 15: Concurrent Requests Handling
run_test "Concurrent Requests Handling" '
    for i in {1..5}; do
        curl -s "$BASE_URL/status" > /dev/null &
    done
    wait
    [ $? -eq 0 ]
'

# Latency Analysis
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Latency Analysis (10 requests)${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

LATENCIES=()
for i in {1..10}; do
    START=$(date +%s%N)
    curl -s "$BASE_URL/status" > /dev/null
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))
    LATENCIES+=($LATENCY)
    echo "Request $i: ${LATENCY}ms"
done

# Calculate average
TOTAL=0
for lat in "${LATENCIES[@]}"; do
    TOTAL=$((TOTAL + lat))
done
AVG=$((TOTAL / 10))

echo ""
echo "Average Latency: ${AVG}ms"
echo ""

# Check logs if Render API key provided
if [ -n "$RENDER_API_KEY" ]; then
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Recent Logs (Last 20 lines)${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""

    curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
        "https://api.render.com/v1/services/$SERVICE_ID/logs?limit=20" | jq -r '.logs[].message'
    echo ""
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓✓✓ All validations passed! Deployment successful!${NC}"
    echo ""
    echo -e "${CYAN}Service is ready for production use.${NC}"
    exit 0
else
    echo -e "${RED}✗✗✗ Some validations failed. Please review.${NC}"
    echo ""
    echo -e "${YELLOW}Recommended Actions:${NC}"
    echo "1. Check Render Dashboard logs"
    echo "2. Verify environment variables"
    echo "3. Test endpoints manually"
    echo "4. Review error messages above"
    exit 1
fi
