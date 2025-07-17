#!/usr/bin/env python3
"""
Sage - Quick Local Setup Script
Setup Sage for local Docker testing
"""

import secrets
import base64
import os
from pathlib import Path

def generate_secure_key(length=32):
    """Generate a secure random key."""
    return secrets.token_urlsafe(length)

def generate_encryption_key():
    """Generate a 32-byte encryption key encoded in base64."""
    key = secrets.token_bytes(32)
    return base64.b64encode(key).decode('utf-8')

def quick_setup():
    """Quick setup for local testing."""
    print("🚀 Sage - Quick Local Setup")
    print("=" * 40)
    
    # Get API key from user
    print("\n🔑 Please provide your OpenAI API key:")
    openai_key = input("OpenAI API Key (sk-...): ").strip()
    
    if not openai_key.startswith('sk-'):
        print("❌ Invalid OpenAI API key format")
        return
    
    print("\n🔧 Generating secure keys for local testing...")
    
    # Generate secure keys
    jwt_secret = generate_secure_key(32)
    jwt_refresh_secret = generate_secure_key(32)
    encryption_key = generate_encryption_key()
    field_encryption_key = generate_encryption_key()
    crisis_encryption_key = generate_encryption_key()
    
    # Generate passwords
    postgres_password = generate_secure_key(16)
    redis_password = generate_secure_key(16)
    
    # Create .env for local testing
    env_content = f"""# Sage - Local Development Environment
# Generated for Docker local testing

# ===========================================
# CORE API CONFIGURATION
# ===========================================
OPENAI_API_KEY={openai_key}
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.3

# ===========================================
# JWT AUTHENTICATION
# ===========================================
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_REFRESH_SECRET_KEY={jwt_refresh_secret}

# ===========================================
# DATABASE CONFIGURATION
# ===========================================
POSTGRES_PASSWORD={postgres_password}
DATABASE_URL=postgresql://mental_health_user:{postgres_password}@postgres:5432/mental_health_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ===========================================
# REDIS CONFIGURATION
# ===========================================
REDIS_PASSWORD={redis_password}
REDIS_URL=redis://:{redis_password}@redis:6379/0

# ===========================================
# ENCRYPTION KEYS (HIPAA/GDPR COMPLIANCE)
# ===========================================
ENCRYPTION_KEY={encryption_key}
FIELD_ENCRYPTION_KEY={field_encryption_key}
CRISIS_ENCRYPTION_KEY={crisis_encryption_key}

# ===========================================
# APPLICATION CONFIGURATION
# ===========================================
APP_NAME=Sage
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# ===========================================
# CORS & SECURITY (LOCAL)
# ===========================================
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080","http://127.0.0.1:3000"]
ALLOWED_HOSTS=["localhost","127.0.0.1","0.0.0.0"]

# ===========================================
# CRISIS INTERVENTION & SAFETY
# ===========================================
ENABLE_CRISIS_DETECTION=true
CRISIS_DETECTION_MODEL=advanced_ml
ENABLE_CONTENT_FILTERING=true
ENABLE_SAFETY_LOGGING=true
ENABLE_CRISIS_MONITORING=true

# Crisis Hotlines
CRISIS_HOTLINE_988=988
CRISIS_TEXT_LINE=741741
EMERGENCY_NUMBER=911
CRISIS_CHAT_URL=https://suicidepreventionlifeline.org/chat/

# ===========================================
# COMPLIANCE & AUDIT LOGGING
# ===========================================
ENABLE_AUDIT_LOGGING=true
GDPR_COMPLIANCE=true
HIPAA_COMPLIANCE=true
DATA_RETENTION_DAYS=90
AUDIT_LOG_RETENTION_DAYS=365

# ===========================================
# CHROMADB CONFIGURATION
# ===========================================
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000
CHROMADB_AUTH_TOKEN={generate_secure_key(24)}

# ===========================================
# RATE LIMITING & SECURITY
# ===========================================
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=2000
MAX_REQUEST_SIZE=10485760
MAX_UPLOAD_SIZE=5242880

# Input Validation
ENABLE_PROMPT_INJECTION_PROTECTION=true
ENABLE_CONTENT_SCANNING=true
MAX_INPUT_LENGTH=4000

# ===========================================
# MONITORING & ALERTING (LOCAL)
# ===========================================
ENABLE_HEALTH_MONITORING=true
HEALTH_CHECK_INTERVAL=30
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_SECURITY_MONITORING=true

# ===========================================
# FRONTEND CONFIGURATION (LOCAL)
# ===========================================
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
WEBSOCKET_URL=ws://localhost:8000/api/ws

# ===========================================
# FEATURE FLAGS (ALL ENABLED FOR TESTING)
# ===========================================
ENABLE_MULTIMODAL_INPUT=true
ENABLE_VOICE_PROCESSING=true
ENABLE_IMAGE_ANALYSIS=true
ENABLE_MEDICAL_IMAGE_SEARCH=true
ENABLE_ANALYTICS_DASHBOARD=true
ENABLE_FEEDBACK_SYSTEM=true

# ===========================================
# DEVELOPMENT SETTINGS
# ===========================================
ENABLE_DEBUG_ENDPOINTS=true
ENABLE_SWAGGER_UI=true
ENABLE_REDOC=true
"""

    # Write .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Environment file created: .env")
    
    # Create docker-compose override for local development
    override_content = """version: '3.8'

services:
  backend:
    volumes:
      - ./backend:/app
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
    
  frontend:
    ports:
      - "3000:8080"
    
  postgres:
    ports:
      - "5432:5432"
    
  chromadb:
    ports:
      - "8001:8000"
    
  redis:
    ports:
      - "6379:6379"

  # Development tools
  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@sage.local
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres
    networks:
      - mental-health-network
"""
    
    with open('docker-compose.override.yml', 'w') as f:
        f.write(override_content)
    
    print("✅ Docker override created: docker-compose.override.yml")
    
    # Create quick test script
    test_script = """#!/bin/bash
# Sage - Quick Test Script

echo "🧪 Testing Sage Local Deployment"
echo "================================"

echo "📡 Testing Backend Health..."
curl -s http://localhost:8000/api/health | jq '.' || echo "❌ Backend not responding"

echo ""
echo "🌐 Testing Frontend..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 && echo "✅ Frontend responding" || echo "❌ Frontend not responding"

echo ""
echo "💾 Testing Database..."
curl -s http://localhost:8000/api/monitoring/health | jq '.database' || echo "❌ Database check failed"

echo ""
echo "🔍 Testing ChromaDB..."
curl -s http://localhost:8001/api/v1/heartbeat && echo "✅ ChromaDB responding" || echo "❌ ChromaDB not responding"

echo ""
echo "📊 Testing Redis..."
docker exec mental-health-redis redis-cli ping && echo "✅ Redis responding" || echo "❌ Redis not responding"

echo ""
echo "🎯 All tests completed!"
echo "Access points:"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Frontend: http://localhost:3000"
echo "- PgAdmin: http://localhost:5050"
echo "- ChromaDB: http://localhost:8001"
"""
    
    with open('test-local.sh', 'w') as f:
        f.write(test_script)
    
    # Make script executable
    os.chmod('test-local.sh', 0o755)
    
    print("✅ Test script created: test-local.sh")
    
    print("\n🎉 Quick setup completed!")
    print("\n🚀 Next steps:")
    print("1. docker-compose up -d")
    print("2. ./test-local.sh")
    print("3. Open http://localhost:3000")
    
    print("\n📊 Access Points:")
    print("- Backend API: http://localhost:8000")
    print("- API Documentation: http://localhost:8000/docs")
    print("- Frontend: http://localhost:3000")
    print("- Database Admin: http://localhost:5050")
    print("- ChromaDB: http://localhost:8001")
    
    print("\n🔐 Generated Credentials:")
    print(f"- PostgreSQL Password: {postgres_password}")
    print(f"- Redis Password: {redis_password}")
    print(f"- PgAdmin: admin@sage.local / admin")

if __name__ == "__main__":
    quick_setup()