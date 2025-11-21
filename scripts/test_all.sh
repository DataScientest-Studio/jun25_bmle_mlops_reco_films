#!/bin/bash
# Script de test complet de toutes les fonctionnalités

echo "=========================================="
echo "Tests Complets du Système"
echo "=========================================="

API_URL="${API_URL:-http://localhost:8080}"

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -n "Test: $description... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED (HTTP $http_code)${NC}"
        echo "  Response: $body"
        return 1
    fi
}

# Tests
echo ""
echo "1. Test Health Check"
test_endpoint "GET" "/health" "" "Health check"

echo ""
echo "2. Test Prometheus Metrics"
test_endpoint "GET" "/metrics" "" "Prometheus metrics"

echo ""
echo "3. Test Cold Start"
test_endpoint "POST" "/predict/" '{"user_id": 999999999, "top_n": 5}' "Cold start recommendation"

echo ""
echo "4. Test Data Drift Baseline"
test_endpoint "POST" "/monitoring/drift/baseline" "" "Create drift baseline"

echo ""
echo "5. Test Data Drift Detection"
test_endpoint "GET" "/monitoring/drift?threshold_pct=10.0" "" "Detect data drift"

echo ""
echo "6. Test Monitoring Stats"
test_endpoint "GET" "/monitoring/stats" "" "Monitoring statistics"

echo ""
echo "7. Test Monitoring Recommendations"
test_endpoint "GET" "/monitoring/recommendations?days=7" "" "Recommendation monitoring"

echo ""
echo "8. Test Training Status"
test_endpoint "GET" "/training/status" "" "Training status"

echo ""
echo "=========================================="
echo "Tests terminés"
echo "=========================================="

