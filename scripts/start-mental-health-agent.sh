#!/bin/bash

# Mental Health Agent Startup Script
# This script helps set up and start the Mental Health Agent system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
port_available() {
    ! nc -z localhost $1 2>/dev/null
}

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate JWT secret
generate_jwt_secret() {
    openssl rand -hex 32
}

print_status "🚀 Starting Mental Health Agent Setup..."

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Prerequisites check passed"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env file from template"
        
        # Generate secure passwords and secrets
        print_status "Generating secure passwords and secrets..."
        
        POSTGRES_PASSWORD=$(generate_password)
        REDIS_PASSWORD=$(generate_password)
        JWT_SECRET=$(generate_jwt_secret)
        ENCRYPTION_KEY=$(generate_jwt_secret)
        
        # Update .env file with generated secrets
        if command_exists sed; then
            sed -i.bak "s/secure_postgres_password_change_me/$POSTGRES_PASSWORD/g" .env
            sed -i.bak "s/secure_redis_password_change_me/$REDIS_PASSWORD/g" .env
            sed -i.bak "s/your_jwt_secret_key_change_me_in_production/$JWT_SECRET/g" .env
            sed -i.bak "s/your_encryption_key_change_me_in_production/$ENCRYPTION_KEY/g" .env
            rm .env.bak 2>/dev/null || true
            print_success "Generated secure passwords and secrets"
        else
            print_warning "sed not available. Please manually update passwords in .env file"
        fi
        
        print_warning "⚠️  IMPORTANT: Please update the OPENAI_API_KEY in .env file before continuing"
        print_warning "⚠️  IMPORTANT: Review and update other settings in .env file as needed"
        
        read -p "Press Enter to continue after updating .env file..."
    else
        print_error ".env.example file not found. Cannot create .env file."
        exit 1
    fi
else
    print_success ".env file found"
fi

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" .env; then
    print_error "OpenAI API key not set in .env file. Please update OPENAI_API_KEY before continuing."
    exit 1
fi

# Check port availability
print_status "Checking port availability..."

PORTS=(3000 8000 5432 6379 8001)
for port in "${PORTS[@]}"; do
    if ! port_available $port; then
        print_warning "Port $port is already in use. Please stop the service using this port or change the configuration."
    fi
done

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/chromadb
mkdir -p backend/logs
mkdir -p frontend/data
mkdir -p frontend/static/images
print_success "Directories created"

# Pull latest images
print_status "Pulling latest Docker images..."
docker-compose pull

# Build custom images
print_status "Building custom images..."
docker-compose build

# Start the system
print_status "Starting Mental Health Agent system..."

# Start databases first
print_status "Starting database services..."
docker-compose up -d postgres redis chromadb

# Wait for databases to be ready
print_status "Waiting for databases to be ready..."
sleep 10

# Check database health
print_status "Checking database health..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U mental_health_user -d mental_health_db >/dev/null 2>&1; then
        print_success "PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL failed to start"
        exit 1
    fi
    sleep 2
done

# Start backend
print_status "Starting backend service..."
docker-compose up -d backend

# Wait for backend to be ready
print_status "Waiting for backend to be ready..."
for i in {1..60}; do
    if curl -f http://localhost:8000/api/health >/dev/null 2>&1; then
        print_success "Backend is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        print_error "Backend failed to start"
        docker-compose logs backend
        exit 1
    fi
    sleep 2
done

# Start frontend
print_status "Starting frontend service..."
docker-compose up -d frontend

# Wait for frontend to be ready
print_status "Waiting for frontend to be ready..."
for i in {1..60}; do
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        print_success "Frontend is ready"
        break
    fi
    if [ $i -eq 60 ]; then
        print_error "Frontend failed to start"
        docker-compose logs frontend
        exit 1
    fi
    sleep 2
done

# Final status check
print_status "Performing final system health check..."

# Check all services
SERVICES=(postgres redis chromadb backend frontend)
ALL_HEALTHY=true

for service in "${SERVICES[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        print_success "$service is running"
    else
        print_error "$service is not running"
        ALL_HEALTHY=false
    fi
done

if [ "$ALL_HEALTHY" = true ]; then
    print_success "🎉 Mental Health Agent is now running!"
    echo ""
    echo "📱 Frontend (Open WebUI): http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📊 API Documentation: http://localhost:8000/docs"
    echo "🗄️  Database: localhost:5432"
    echo "🔍 ChromaDB: http://localhost:8001"
    echo ""
    print_status "To stop the system, run: docker-compose down"
    print_status "To view logs, run: docker-compose logs -f [service_name]"
    print_status "To restart a service, run: docker-compose restart [service_name]"
    echo ""
    print_warning "⚠️  Remember to:"
    print_warning "   - Keep your .env file secure and never commit it to version control"
    print_warning "   - Regularly backup your data"
    print_warning "   - Monitor the system logs for any issues"
    print_warning "   - Update passwords and secrets regularly in production"
else
    print_error "Some services failed to start. Please check the logs:"
    echo "docker-compose logs"
    exit 1
fi
