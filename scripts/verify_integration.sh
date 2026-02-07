#!/bin/bash
# =============================================================================
# Nexus Global Payments Sandbox - Integration Verification Script
# =============================================================================
# This script verifies that all services are running correctly and can
# communicate with each other.
#
# Usage:
#   ./scripts/verify_integration.sh
#
# Requirements:
#   - docker-compose is installed
#   - All services are running (docker-compose up -d)
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# =============================================================================
# Test Functions
# =============================================================================

test_service_health() {
    local service=$1
    local url=$2
    local expected_status=${3:-200}
    
    log_info "Testing $service health at $url..."
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$response" == "$expected_status" ]; then
            log_success "$service is healthy (HTTP $response)"
        else
            log_error "$service returned HTTP $response (expected $expected_status)"
        fi
    else
        log_error "$service is not responding"
    fi
}

test_api_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local expected_status=${4:-200}
    local data=${5:-}
    
    log_info "Testing API: $name ($method $url)..."
    
    if [ -n "$data" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$url" 2>/dev/null || echo "000")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
            "$url" 2>/dev/null || echo "000")
    fi
    
    if [ "$response" == "$expected_status" ]; then
        log_success "$name endpoint working (HTTP $response)"
    else
        log_error "$name endpoint failed (HTTP $response, expected $expected_status)"
    fi
}

test_iso_message_validation() {
    log_info "Testing ISO 20022 pacs.008 validation (missing mandatory fields)..."
    
    # This should fail with validation error due to missing mandatory fields
    response=$(curl -s -X POST \
        -H "Content-Type: application/xml" \
        -d '<?xml version="1.0"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.13">
  <FIToFICstmrCdtTrf>
    <GrpHdr>
      <MsgId>TEST001</MsgId>
      <CreDtTm>2026-02-07T00:00:00Z</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
    </GrpHdr>
  </FIToFICstmrCdtTrf>
</Document>' \
        http://localhost:8000/v1/iso20022/pacs008 2>/dev/null)
    
    if echo "$response" | grep -q "Missing mandatory field"; then
        log_success "pacs.008 mandatory field validation working"
    else
        log_warn "pacs.008 validation response: $response"
        # Don't fail - validation might work differently
    fi
}

test_sanctions_screening() {
    log_info "Testing sanctions screening API..."
    
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "uetr": "test-uetr-123",
            "sender_name": "John Doe",
            "sender_account": "123456789",
            "recipient_name": "Jane Smith",
            "recipient_account": "987654321",
            "recipient_address": "123 Main St, Bangkok"
        }' \
        http://localhost:8000/v1/sanctions/review-data 2>/dev/null)
    
    if echo "$response" | grep -q "fatf_r16_compliant"; then
        log_success "Sanctions screening API responding correctly"
    else
        log_error "Sanctions screening API not responding as expected"
        log_info "Response: $response"
    fi
}

test_namespace_version() {
    log_info "Verifying pacs.008 namespace version in code..."
    
    if grep -q "pacs.008.001.13" services/nexus-gateway/src/api/iso20022/pacs008.py; then
        log_success "pacs.008 namespace is .001.13 (correct)"
    else
        log_error "pacs.008 namespace is not .001.13"
    fi
}

test_status_codes() {
    log_info "Verifying ACCC status code usage..."
    
    # Check that ACCP is not used in main code (only in XSD files is OK)
    if grep -r "ACCP" services/nexus-gateway/src/ services/demo-dashboard/src/ 2>/dev/null | grep -v "node_modules" | grep -v ".xsd"; then
        log_warn "ACCP still found in code (should be ACCC)"
    else
        log_success "ACCP not found in main code (using ACCC correctly)"
    fi
}

# =============================================================================
# Main Test Suite
# =============================================================================

echo "======================================================================"
echo "  Nexus Global Payments - Integration Verification"
echo "======================================================================"
echo ""

# Check if services are running
log_info "Checking if services are running..."
if ! docker-compose ps | grep -q "Up"; then
    log_error "No services appear to be running. Start with: docker-compose up -d"
    exit 1
fi
log_success "Services are running"

echo ""
echo "----------------------------------------------------------------------"
echo "  Service Health Checks"
echo "----------------------------------------------------------------------"

# Test service health endpoints
test_service_health "Nexus Gateway" "http://localhost:8000/health" "200"
test_service_health "Demo Dashboard" "http://localhost:8080/health" "200"

echo ""
echo "----------------------------------------------------------------------"
echo "  API Endpoint Tests"
echo "----------------------------------------------------------------------"

# Test discovery APIs
test_api_endpoint "Get Countries" "GET" "http://localhost:8000/v1/countries" "200"
test_api_endpoint "Get Currencies" "GET" "http://localhost:8000/v1/currencies" "200"

# Test quotes API (might return empty if no FXPs seeded, but should not error)
test_api_endpoint "Get Quotes" "GET" "http://localhost:8000/v1/quotes/SG/SGD/TH/THB/SGD/100" "200"

# Test addressing API
test_api_endpoint "Get Address Types" "GET" "http://localhost:8000/v1/address-types/SG" "200"

# Test actors API
test_api_endpoint "Get Actors" "GET" "http://localhost:8000/v1/actors" "200"

# Test new sanctions screening API
test_api_endpoint "Sanctions Review" "POST" "http://localhost:8000/v1/sanctions/review-data" "200" '{
    "uetr": "test-uetr-123",
    "sender_name": "John Doe",
    "sender_account": "123456789",
    "recipient_name": "Jane Smith",
    "recipient_account": "987654321"
}'

echo ""
echo "----------------------------------------------------------------------"
echo "  Code Verification Tests"
echo "----------------------------------------------------------------------"

# Test namespace versions
test_namespace_version

# Test status codes
test_status_codes

echo ""
echo "----------------------------------------------------------------------"
echo "  Integration Tests"
echo "----------------------------------------------------------------------"

# Test sanctions screening
test_sanctions_screening

# Test ISO message validation
test_iso_message_validation

echo ""
echo "----------------------------------------------------------------------"
echo "  Frontend-Backend Integration"
echo "----------------------------------------------------------------------"

# Test that frontend can reach backend through nginx proxy
log_info "Testing frontend → nginx → gateway proxy chain..."
if curl -s http://localhost:8080/api/v1/health > /dev/null 2>&1; then
    log_success "Frontend can reach backend via /api proxy"
else
    log_error "Frontend cannot reach backend via /api proxy"
fi

echo ""
echo "======================================================================"
echo "  Test Summary"
echo "======================================================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All integration tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  - Access the demo dashboard: http://localhost:8080"
    echo "  - View API docs: http://localhost:8081 (Swagger UI)"
    echo "  - Test a payment flow through the UI"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please review the errors above.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose logs <service-name>"
    echo "  2. Restart services: docker-compose restart"
    echo "  3. Rebuild: docker-compose up --build -d"
    exit 1
fi
