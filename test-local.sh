#!/bin/bash
# Sage - Quick Test Script

echo "🧪 Testing Sage Local Deployment"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    echo -n "📡 Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed (HTTP $response)${NC}"
        return 1
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local url=$1
    local name=$2
    
    echo -n "📡 Testing $name... "
    
    response=$(curl -s "$url" 2>/dev/null)
    
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        echo "   Response: $(echo "$response" | jq -c .)"
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        echo "   Response: $response"
        return 1
    fi
}

echo ""
echo "🔍 Checking Docker containers..."
docker-compose ps

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "🧪 Running Health Tests..."
echo "=========================="

# Test Backend Health
test_json_endpoint "http://localhost:8000/api/health" "Backend Health"

# Test Frontend
test_endpoint "http://localhost:3000" "Frontend" "200"

# Test API Documentation
test_endpoint "http://localhost:8000/docs" "API Documentation" "200"

# Test ChromaDB
test_json_endpoint "http://localhost:8001/api/v1/heartbeat" "ChromaDB"

# Test Database connection through backend
echo -n "💾 Testing Database Connection... "
db_response=$(curl -s "http://localhost:8000/api/health" | jq -r '.database' 2>/dev/null)
if [ "$db_response" = "healthy" ]; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Test Redis
echo -n "📊 Testing Redis... "
redis_response=$(docker exec mental-health-redis redis-cli ping 2>/dev/null)
if [ "$redis_response" = "PONG" ]; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

echo ""
echo "🎯 Test Summary"
echo "==============="

# Count running containers
running_containers=$(docker-compose ps --services --filter "status=running" | wc -l)
total_containers=$(docker-compose ps --services | wc -l)

echo "📦 Containers: $running_containers/$total_containers running"

if [ $running_containers -eq $total_containers ]; then
    echo -e "${GREEN}🎉 All services are running!${NC}"
else
    echo -e "${YELLOW}⚠️  Some services may not be running properly${NC}"
fi

echo ""
echo "🌐 Access Points:"
echo "=================="
echo "🖥️  Frontend (Sage UI):     http://localhost:3000"
echo "🔧 Backend API:             http://localhost:8000"
echo "📚 API Documentation:       http://localhost:8000/docs"
echo "🗄️  Database Admin:         http://localhost:5050"
echo "🔍 ChromaDB:               http://localhost:8001"

echo ""
echo "🔐 Default Credentials:"
echo "======================="
echo "PgAdmin: admin@sage.local / admin"

echo ""
echo "📋 Useful Commands:"
echo "==================="
echo "View logs:           docker-compose logs -f"
echo "Restart services:    docker-compose restart"
echo "Stop services:       docker-compose down"
echo "View containers:     docker-compose ps"

echo ""
echo "🚀 Ready to test Sage!"
echo "Open http://localhost:3000 to start using the mental health agent."