# 🚀 Sage - Quick Setup Script Guide

## Overview

The `scripts/quick-setup.py` script is the fastest and most secure way to get Sage running locally for development and testing. It automates the entire environment configuration process with enterprise-grade security.

## 🎯 What It Does

### Automated Configuration
- **🔑 API Key Collection**: Prompts for and validates your OpenAI API key (required)
- **🤖 AI Model Setup**: Configures Google Gemini as default healthcare model with OpenAI fallback
- **🔐 Security Generation**: Creates cryptographically secure keys and passwords
- **⚙️ Environment Setup**: Generates complete `.env` configuration file
- **🐳 Docker Configuration**: Creates `docker-compose.override.yml` for development
- **🧪 Test Script**: Generates `test-local.sh` for deployment verification

### Security Features Generated
- **JWT Authentication**: 32-character secure secrets for access and refresh tokens
- **HIPAA/GDPR Encryption**: Base64-encoded 32-byte encryption keys for health data
- **Database Security**: Strong passwords for PostgreSQL and Redis
- **Crisis Detection**: ML-based crisis intervention configuration
- **Audit Logging**: Comprehensive compliance logging setup

## 🚀 Usage

### Basic Usage
```bash
# Navigate to your Sage directory
cd sage

# Run the quick setup script
python scripts/quick-setup.py

# Follow the prompts:
# 1. Enter your OpenAI API key (sk-...)
# 2. Script generates all security configurations automatically

# Start services
docker-compose up -d

# Test deployment
./test-local.sh
```

### What You'll Be Asked
1. **OpenAI API Key**: Your API key starting with `sk-`
   - The script validates the format
   - Required for AI functionality

## 📁 Generated Files

### `.env` File
Complete environment configuration with:
```bash
# Core API Configuration
OPENAI_API_KEY=your-provided-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.3

# Google Gemini Configuration (Default Healthcare Model)
GEMINI_API_KEY=your-gemini-key-here
GEMINI_MODEL=gemini-1.5-pro
GEMINI_MAX_TOKENS=2000
GEMINI_TEMPERATURE=0.3
GEMINI_SAFETY_SETTINGS=high

# Healthcare Model Configuration
SAGE_HEALTHCARE_MODE=true
DEFAULT_HEALTHCARE_MODEL=gemini
MODEL_ROUTING_ENABLED=true

# JWT Authentication (Auto-generated)
JWT_SECRET_KEY=secure-32-char-secret
JWT_REFRESH_SECRET_KEY=different-32-char-secret

# Database Configuration (Auto-generated)
POSTGRES_PASSWORD=secure-16-char-password
REDIS_PASSWORD=secure-16-char-password

# Encryption Keys (HIPAA/GDPR Compliant)
ENCRYPTION_KEY=base64-encoded-32-byte-key
FIELD_ENCRYPTION_KEY=base64-encoded-32-byte-key
CRISIS_ENCRYPTION_KEY=base64-encoded-32-byte-key

# Crisis Detection & Safety
ENABLE_CRISIS_DETECTION=true
CRISIS_DETECTION_MODEL=advanced_ml
ENABLE_CONTENT_FILTERING=true
ENABLE_SAFETY_LOGGING=true

# And much more...
```

### `docker-compose.override.yml`
Development-optimized Docker configuration:
```yaml
version: '3.8'

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
  
  # Additional development tools
  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@sage.local
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
```

### `test-local.sh`
Comprehensive test script that checks:
```bash
#!/bin/bash
# Tests all services and endpoints
echo "🧪 Testing Sage Local Deployment"

# Backend health check
curl -s http://localhost:8000/api/health

# Frontend accessibility
curl -s http://localhost:3000

# Database connectivity
curl -s http://localhost:8000/api/monitoring/health

# ChromaDB status
curl -s http://localhost:8001/api/v1/heartbeat

# Redis connectivity
docker exec mental-health-redis redis-cli ping
```

## 🔐 Security Features

### Generated Security Components

#### JWT Authentication
- **Access Token Secret**: 32-character cryptographically secure key
- **Refresh Token Secret**: Different 32-character secure key
- **Algorithm**: HS256 with proper expiration times

#### Encryption Keys (HIPAA/GDPR Compliant)
- **Primary Encryption Key**: For sensitive health data
- **Field Encryption Key**: For PII field-level encryption
- **Crisis Encryption Key**: For crisis intervention data
- All keys are 32-byte base64-encoded for maximum security

#### Database Security
- **PostgreSQL Password**: 16-character secure password
- **Redis Password**: 16-character secure password
- **Connection Pooling**: Optimized for development

#### Crisis Detection & Safety
- **ML-based Crisis Detection**: Advanced algorithms for crisis identification
- **Content Filtering**: Automatic content safety scanning
- **Safety Logging**: Comprehensive audit trail
- **Emergency Resources**: Integration with crisis hotlines

## 🌐 Access Points

After running the quick setup and starting services:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | N/A |
| **Backend API** | http://localhost:8000 | N/A |
| **API Documentation** | http://localhost:8000/docs | N/A |
| **Database Admin** | http://localhost:5050 | admin@sage.local / admin |
| **ChromaDB** | http://localhost:8001 | N/A |

## 🧪 Testing & Verification

### Automated Testing
```bash
# Run the generated test script
./test-local.sh
```

### Manual Testing
```bash
# Health check
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "app_name": "Sage",
  "version": "1.0.0",
  "database": "healthy"
}

# Test chat functionality
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I need help with anxiety"}'
```

## 🔧 Customization

### Environment Variables
After running the script, you can customize the generated `.env` file:

```bash
# Edit the generated environment file
nano .env

# Common customizations:
# - Change log levels
# - Adjust rate limiting
# - Modify feature flags
# - Update crisis hotline numbers for your region
```

### Docker Configuration
Customize the generated `docker-compose.override.yml`:

```bash
# Edit Docker override
nano docker-compose.override.yml

# Common customizations:
# - Add additional services
# - Modify port mappings
# - Add volume mounts
# - Configure environment variables
```

## 🚨 Crisis Detection Configuration

The quick setup automatically configures comprehensive crisis detection:

### Crisis Hotlines (US Default)
```bash
CRISIS_HOTLINE_988=988
CRISIS_TEXT_LINE=741741
EMERGENCY_NUMBER=911
CRISIS_CHAT_URL=https://suicidepreventionlifeline.org/chat/
```

### Crisis Detection Features
- **ML-based Detection**: Advanced machine learning algorithms
- **Real-time Monitoring**: Immediate crisis intervention
- **Emergency Resources**: Automatic resource provision
- **Audit Logging**: Complete crisis intervention tracking

## 🔍 Troubleshooting

### Common Issues

#### Invalid OpenAI API Key
```bash
# Error: Invalid OpenAI API key format
# Solution: Ensure your key starts with 'sk-'
```

#### Port Conflicts
```bash
# Check for port conflicts
lsof -i :8000
lsof -i :3000
lsof -i :5432

# Kill conflicting processes
kill -9 <PID>
```

#### Docker Issues
```bash
# Restart Docker services
docker-compose down
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Validation
```bash
# Validate your environment after setup
python scripts/validate-environment.py
```

## 🎯 Next Steps

### After Quick Setup
1. **Start Services**: `docker-compose up -d`
2. **Run Tests**: `./test-local.sh`
3. **Access Frontend**: http://localhost:3000
4. **Review API Docs**: http://localhost:8000/docs
5. **Test Chat**: Send a message through the API

### Development Workflow
1. **Code Changes**: Edit files in `backend/` or `frontend/`
2. **Hot Reload**: Backend automatically reloads on changes
3. **Database Changes**: Use migrations in `backend/database/`
4. **Testing**: Add tests in `backend/tests/`

### Production Deployment
1. **Production Setup**: Use `scripts/setup-production-env.py`
2. **Environment Validation**: Use `scripts/validate-environment.py`
3. **Deploy**: Follow `DEPLOYMENT_CHECKLIST.md`

## 🔒 Security Best Practices

### Key Management
- **Never commit** the generated `.env` file to version control
- **Backup encryption keys** securely
- **Rotate keys regularly** in production
- **Use different keys** for different environments

### Development Security
- The quick setup enables debug mode for development
- Production deployment requires `scripts/setup-production-env.py`
- Always validate environment with `scripts/validate-environment.py`

## 📞 Support

### Crisis Resources (Always Available)
- **988 Suicide & Crisis Lifeline**: 988
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911
- **Crisis Chat**: https://suicidepreventionlifeline.org/chat/

### Technical Support
- **Documentation**: Check `docs/` directory
- **Logs**: `docker-compose logs -f`
- **Health Check**: `curl http://localhost:8000/api/health`
- **Test Script**: `./test-local.sh`

---

## ✅ Success Checklist

After running the quick setup, you should have:

- ✅ Generated `.env` file with secure configuration
- ✅ Created `docker-compose.override.yml` for development
- ✅ Generated `test-local.sh` script for verification
- ✅ All services starting successfully with `docker-compose up -d`
- ✅ Health check returning "healthy" status
- ✅ Frontend accessible at http://localhost:3000
- ✅ API documentation available at http://localhost:8000/docs
- ✅ Crisis detection and safety features enabled
- ✅ HIPAA/GDPR compliant encryption configured

**🎉 Sage is ready to provide safe, AI-powered mental health support!**