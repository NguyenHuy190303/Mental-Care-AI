# 🚀 Sage - Local Setup Guide

## 📋 **Prerequisites**

- Docker và Docker Compose đã cài đặt
- Python 3.8+ (để chạy setup script)
- OpenAI API Key

## ⚡ **Quick Start (5 phút) - RECOMMENDED**

### **🚀 New Quick Setup Script**

The fastest and most secure way to get Sage running locally:

### **Bước 1: Clone và Quick Setup**
```bash
# Clone repository
git clone <your-repo-url>
cd sage

# Run the automated quick setup script
python scripts/quick-setup.py
```

**What the quick setup script does:**
- ✅ Prompts for your OpenAI API key
- ✅ Generates cryptographically secure JWT secrets
- ✅ Creates HIPAA/GDPR compliant encryption keys
- ✅ Generates strong database passwords
- ✅ Configures crisis detection and safety monitoring
- ✅ Creates Docker override for development
- ✅ Generates test script for verification

### **Bước 2: Khởi động Services**
```bash
# Start all services (PostgreSQL, Redis, ChromaDB, Backend, Frontend)
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

### **Bước 3: Test Deployment**
```bash
# Run the generated test script
./test-local.sh

# Or test manually
curl http://localhost:8000/api/health
```

### **Bước 4: Truy cập Sage**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database Admin (PgAdmin)**: http://localhost:5050 (admin@sage.local / admin)
- **ChromaDB**: http://localhost:8001

### **🔐 Generated Security Features**
The quick setup automatically configures:
- **Secure JWT Authentication** with 32-character secrets
- **Field-level Encryption** for HIPAA/GDPR compliance
- **Crisis Detection** with ML-based monitoring
- **Rate Limiting** and input validation
- **Audit Logging** for compliance
- **Emergency Resources** integration

---

## 🔧 **Manual Setup (nếu cần tùy chỉnh)**

### **1. Tạo .env file**
```bash
cp .env.example .env
# Edit .env với API keys của bạn
```

### **2. Cấu hình API Keys**
```bash
# Trong .env file
OPENAI_API_KEY=sk-your-openai-key-here
JWT_SECRET_KEY=your-32-character-secret-key
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-secure-password
```

### **3. Generate Secure Keys**
```bash
# JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption Key
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

---

## 🧪 **Testing & Verification**

### **Health Checks**
```bash
# Backend health
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "app_name": "Sage",
  "version": "1.0.0",
  "database": "healthy",
  "active_websocket_connections": 0
}
```

### **API Documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### **Database Access**
- PgAdmin: http://localhost:5050
- Username: admin@sage.local
- Password: admin

### **Test Chat Functionality**
```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I need help with anxiety"}'
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Kill process if needed
kill -9 <PID>
```

#### **Docker Issues**
```bash
# Restart Docker
docker-compose down
docker-compose up -d

# Rebuild containers
docker-compose up -d --build

# View logs
docker-compose logs backend
docker-compose logs frontend
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Connect to database directly
docker exec -it mental-health-postgres psql -U mental_health_user -d mental_health_db
```

#### **OpenAI API Issues**
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-your-key-here"
```

### **Service Status Check**
```bash
# Check all containers
docker-compose ps

# Check specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose logs chromadb
docker-compose logs redis
```

---

## 📊 **Service Overview**

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Frontend | 3000 | http://localhost:3000 | Sage UI |
| Backend | 8000 | http://localhost:8000 | API Server |
| PostgreSQL | 5432 | localhost:5432 | Main Database |
| ChromaDB | 8001 | http://localhost:8001 | Vector Database |
| Redis | 6379 | localhost:6379 | Cache |
| PgAdmin | 5050 | http://localhost:5050 | DB Admin |

---

## 🔐 **Security Features (Local)**

### **Enabled Features**
- ✅ Crisis detection and monitoring
- ✅ Content filtering and safety
- ✅ Medical disclaimers
- ✅ Audit logging
- ✅ Data encryption
- ✅ Rate limiting
- ✅ Input validation

### **Development Settings**
- Debug mode enabled
- Swagger UI accessible
- Detailed logging
- CORS allows localhost

---

## 🚀 **Next Steps**

### **After Local Testing**
1. **Production Setup**: Use `scripts/setup-production-env.py`
2. **Deploy to Cloud**: Follow `DEPLOYMENT_CHECKLIST.md`
3. **Configure Domain**: Update CORS and URLs
4. **SSL Setup**: Configure HTTPS certificates
5. **Monitoring**: Setup alerts and monitoring

### **Development**
1. **Code Changes**: Edit files in `backend/` or `frontend/`
2. **Hot Reload**: Backend auto-reloads on changes
3. **Database Changes**: Use migrations in `backend/database/`
4. **Testing**: Add tests in `backend/tests/`

---

## 📞 **Support**

### **Crisis Resources (Always Available)**
- **988 Suicide & Crisis Lifeline**: 988
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911
- **Crisis Chat**: https://suicidepreventionlifeline.org/chat/

### **Technical Support**
- Check logs: `docker-compose logs -f`
- Review documentation: `docs/`
- Test endpoints: `./test-local.sh`

---

## ✅ **Success Indicators**

You'll know Sage is working when:
- ✅ All containers are running (`docker-compose ps`)
- ✅ Health check returns "healthy" status
- ✅ Frontend loads at http://localhost:3000
- ✅ API docs accessible at http://localhost:8000/docs
- ✅ Chat functionality responds to messages
- ✅ Crisis detection triggers appropriately
- ✅ Medical disclaimers display correctly

**🎉 Sage is ready to provide safe, AI-powered mental health support!**