# 🚀 Sage - Production Deployment Checklist

## 📋 **Pre-Deployment Checklist**

### ✅ **Environment Setup**
- [ ] Run setup script: `python scripts/setup-production-env.py`
- [ ] Validate environment: `python scripts/validate-environment.py`
- [ ] Verify all environment variables are set correctly
- [ ] **Configure default healthcare model (Google Gemini)**:
  - [ ] Set `GEMINI_API_KEY=your-gemini-key` in environment
  - [ ] Set `SAGE_HEALTHCARE_MODE=true` (default)
  - [ ] Set `DEFAULT_HEALTHCARE_MODEL=gemini` (default)
  - [ ] Set `MODEL_ROUTING_ENABLED=true` for intelligent routing
- [ ] Test local deployment: `docker-compose up -d`
- [ ] Confirm health check: `curl http://localhost:8000/api/health`

### ✅ **Security Configuration**
- [ ] All encryption keys generated and secured
- [ ] JWT secrets are unique and strong (32+ characters)
- [ ] Database passwords are strong (16+ characters)
- [ ] CORS origins configured for production domain
- [ ] SSL/TLS certificates ready
- [ ] Security monitoring enabled

### ✅ **Database Setup**
- [ ] PostgreSQL database created
- [ ] Database migrations ready
- [ ] Backup strategy configured
- [ ] Connection pooling configured
- [ ] Audit logging enabled

### ✅ **Infrastructure**
- [ ] Domain DNS configured
- [ ] SSL certificates installed
- [ ] Load balancer configured (if using)
- [ ] Monitoring and alerting setup
- [ ] Log aggregation configured

---

## 🚀 **Deployment Options**

### **Option A: Quick Deploy (Docker Compose)**
```bash
# 1. Setup environment
python scripts/setup-production-env.py

# 2. Validate configuration
python scripts/validate-environment.py

# 3. Deploy
docker-compose up -d

# 4. Test
curl https://your-domain.com/api/health
```

### **Option B: Vercel + Render (Recommended)**

#### **Frontend (Vercel)**
```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy frontend
cd frontend
vercel --prod

# 3. Configure environment variables in Vercel dashboard
```

#### **Backend (Render)**
```bash
# 1. Connect GitHub repo to Render
# 2. Create new Web Service
# 3. Configure build settings:
#    - Build Command: docker build -t sage-backend ./backend
#    - Start Command: python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
# 4. Add environment variables from .env
```

**⚠️ Docker Build Context Issue:**
The backend Dockerfile currently references `../requirements.txt` but the Docker build context is set to `./backend`. This will cause build failures. See troubleshooting section below.

### **Option C: Kubernetes (Enterprise)**
```bash
# 1. Apply Kubernetes configurations
kubectl apply -f infrastructure/kubernetes/

# 2. Verify deployment
kubectl get pods -n sage-production

# 3. Check services
kubectl get services -n sage-production
```

---

## 🔧 **Environment Variables Setup**

### **Required Variables**
```bash
# Core API
OPENAI_API_KEY=sk-your-key-here
GEMINI_API_KEY=your-gemini-key-here         # Primary healthcare model
JWT_SECRET_KEY=your-32-char-secret
JWT_REFRESH_SECRET_KEY=your-different-32-char-secret

# Healthcare Model Configuration (UPDATED)
OPENAI_MODEL=gpt-4o-mini                    # OpenAI model configuration
GEMINI_MODEL=gemini-1.5-pro                 # Google Gemini model (default for healthcare)
OPENAI_TEMPERATURE=0.3                      # Conservative temperature for medical use
GEMINI_TEMPERATURE=0.3                      # Conservative temperature for medical use
GEMINI_SAFETY_SETTINGS=high                 # High safety settings for medical content
SAGE_HEALTHCARE_MODE=true                   # Enable healthcare-specific model selection
DEFAULT_HEALTHCARE_MODEL=gemini             # Default to Gemini for healthcare applications
MODEL_ROUTING_ENABLED=true                  # Enable intelligent model routing

# Database
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=your-secure-password

# Encryption (HIPAA/GDPR)
ENCRYPTION_KEY=your-base64-32-byte-key
FIELD_ENCRYPTION_KEY=your-base64-32-byte-key
CRISIS_ENCRYPTION_KEY=your-base64-32-byte-key

# Domain
FRONTEND_URL=https://your-domain.com
BACKEND_URL=https://api.your-domain.com
CORS_ORIGINS=["https://your-domain.com"]
```

### **Generate Secure Keys**
```bash
# JWT Secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Encryption Keys
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"

# Passwords
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

---

## 🏥 **Healthcare Model Configuration**

### **Default Model Setup (Google Gemini)**
The Sage system is now pre-configured to use Google Gemini 1.5 Pro as the default model for healthcare applications, with OpenAI GPT-4o-mini as a fallback option. This eliminates the need for manual model selection by healthcare users.

#### **Key Features:**
- **Primary Model**: Google Gemini 1.5 Pro for most healthcare queries
- **Fallback Model**: OpenAI GPT-4o-mini for reliability and cost optimization
- **Healthcare Mode**: Enabled by default with `SAGE_HEALTHCARE_MODE=true`
- **Intelligent Model Routing**: Automatic selection based on query complexity and model availability
- **High Safety Settings**: Enhanced safety configurations for medical content
- **No User Intervention**: Healthcare professionals and patients don't need to select models

#### **Configuration Variables:**
```bash
GEMINI_API_KEY=your-gemini-key-here         # Primary healthcare model
GEMINI_MODEL=gemini-1.5-pro                 # Google Gemini model configuration
OPENAI_MODEL=gpt-4o-mini                    # Fallback model
SAGE_HEALTHCARE_MODE=true                   # Enable healthcare-specific logic
DEFAULT_HEALTHCARE_MODEL=gemini             # Primary healthcare model
MODEL_ROUTING_ENABLED=true                  # Enable intelligent model routing
GEMINI_TEMPERATURE=0.3                      # Conservative temperature for medical accuracy
GEMINI_SAFETY_SETTINGS=high                 # High safety settings for medical content
```

#### **Model Selection Logic:**
1. **Healthcare Mode Enabled** (default): Uses Google Gemini 1.5 Pro for most healthcare queries
2. **Model Routing**: Intelligent switching between Gemini and GPT-4o-mini based on:
   - Query complexity and type
   - Model availability and response times
   - Cost optimization considerations
3. **Fallback Support**: If primary model unavailable, automatically uses OpenAI GPT-4o-mini
4. **Safety Priority**: Both models configured with conservative settings for medical accuracy

---

## 🧪 **Testing Checklist**

### **Health Checks**
```bash
# Backend health
curl https://api.your-domain.com/api/health

# Frontend accessibility
curl https://your-domain.com

# WebSocket connection
wscat -c wss://api.your-domain.com/api/ws
```

### **Functionality Tests**
- [ ] User registration/login works
- [ ] Chat interface loads correctly
- [ ] **Healthcare model configuration**:
  - [ ] System automatically uses Google Gemini 1.5 Pro by default
  - [ ] OpenAI GPT-4o-mini available as fallback model
  - [ ] No manual model selection required for users
  - [ ] Healthcare mode is enabled and functioning
  - [ ] Intelligent model routing works for different complexity levels
- [ ] Crisis detection triggers properly
- [ ] Medical disclaimers display
- [ ] Citations are clickable
- [ ] Feedback system works
- [ ] Mobile PWA functions offline

### **Security Tests**
- [ ] HTTPS enforced
- [ ] Security headers present
- [ ] Rate limiting active
- [ ] Input validation working
- [ ] Audit logging enabled
- [ ] Crisis monitoring active

---

## 📊 **Monitoring Setup**

### **Health Monitoring**
```bash
# Setup monitoring endpoints
curl https://api.your-domain.com/api/monitoring/health
curl https://api.your-domain.com/api/monitoring/metrics
```

### **Alerting Configuration**
- [ ] Email alerts configured
- [ ] Slack notifications setup
- [ ] Crisis intervention alerts active
- [ ] Security incident alerts enabled
- [ ] Performance monitoring active

### **Log Monitoring**
- [ ] Application logs centralized
- [ ] Error logs monitored
- [ ] Audit logs secured
- [ ] Crisis intervention logs encrypted

---

## 🔒 **Security Verification**

### **SSL/TLS**
```bash
# Test SSL configuration
curl -I https://your-domain.com
openssl s_client -connect your-domain.com:443
```

### **Security Headers**
```bash
# Check security headers
curl -I https://api.your-domain.com/api/health
```

Expected headers:
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

### **Database Security**
- [ ] Database connections encrypted
- [ ] Field-level encryption active
- [ ] Audit logging enabled
- [ ] Backup encryption configured

---

## 🚨 **Crisis Intervention Verification**

### **Crisis Detection**
- [ ] ML-based detection active
- [ ] Keyword detection backup working
- [ ] Crisis alerts triggering
- [ ] Emergency resources accessible

### **Emergency Contacts**
- [ ] 988 Suicide & Crisis Lifeline: 988
- [ ] Crisis Text Line: Text HOME to 741741
- [ ] Emergency Services: 911
- [ ] Crisis Chat: https://suicidepreventionlifeline.org/chat/

### **Crisis Monitoring**
- [ ] Real-time crisis alerts
- [ ] Crisis intervention logging
- [ ] Emergency escalation procedures
- [ ] Crisis data encryption

---

## 📋 **Compliance Verification**

### **HIPAA Compliance**
- [ ] Technical safeguards implemented
- [ ] Administrative safeguards documented
- [ ] Physical safeguards in place
- [ ] Audit controls active
- [ ] Data integrity measures
- [ ] Transmission security

### **GDPR Compliance**
- [ ] Data protection by design
- [ ] User consent management
- [ ] Right to be forgotten
- [ ] Data portability
- [ ] Breach notification procedures
- [ ] Privacy impact assessment

---

## 🎯 **Go-Live Checklist**

### **Final Verification**
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Backup procedures tested
- [ ] Incident response plan ready
- [ ] Staff training completed

### **Launch Sequence**
1. [ ] Final environment validation
2. [ ] Database migration (if needed)
3. [ ] DNS cutover
4. [ ] SSL certificate activation
5. [ ] Monitoring activation
6. [ ] Go-live announcement
7. [ ] Post-launch monitoring

### **Post-Launch**
- [ ] Monitor system performance
- [ ] Check error rates
- [ ] Verify crisis detection
- [ ] Monitor user feedback
- [ ] Review security logs
- [ ] Validate compliance metrics

---

## 🔧 **Troubleshooting**

### **Docker Build Issues**

#### **Backend Dockerfile Build Context Error**
**Problem**: The backend Dockerfile references `../requirements.txt` but the build context is `./backend`, causing build failures.

**Error Message**:
```
COPY failed: file not found in build context or excluded by .dockerignore: stat requirements.txt: file does not exist
```

**Solutions**:

**Option 1: Fix the Dockerfile (Recommended)**
```dockerfile
# In backend/Dockerfile, change:
COPY ../requirements.txt .
# To:
COPY requirements.txt .
```
Then copy requirements.txt to the backend directory:
```bash
cp requirements.txt backend/
```

**Option 2: Change Docker Compose Build Context**
```yaml
# In docker-compose.yml, change:
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile
# To:
backend:
  build:
    context: .
    dockerfile: backend/Dockerfile
```

**Option 3: Use Multi-stage Build**
```dockerfile
# In backend/Dockerfile:
FROM python:3.11-slim as requirements
WORKDIR /app
COPY requirements.txt .

FROM python:3.11-slim
WORKDIR /app
COPY --from=requirements /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

### **Common Deployment Issues**

#### **Port Conflicts**
```bash
# Check what's using ports
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL

# Kill conflicting processes
kill -9 <PID>
```

#### **Environment Variable Issues**
```bash
# Validate environment
python scripts/validate-environment.py

# Check Docker environment
docker-compose config
```

#### **Database Connection Issues**
```bash
# Test PostgreSQL connection
docker exec -it mental-health-postgres psql -U mental_health_user -d mental_health_db

# Check database logs
docker-compose logs postgres
```

#### **SSL Certificate Issues**
```bash
# Test SSL configuration
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check certificate expiry
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### **Performance Issues**

#### **High Memory Usage**
```bash
# Monitor container resources
docker stats

# Optimize Docker memory limits
# Add to docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

#### **Slow Response Times**
```bash
# Check backend health
curl -w "@curl-format.txt" -o /dev/null -s https://api.your-domain.com/api/health

# Monitor database performance
docker exec -it mental-health-postgres pg_stat_activity
```

### **Security Issues**

#### **CORS Errors**
```bash
# Update CORS_ORIGINS in .env
CORS_ORIGINS=["https://your-domain.com","https://www.your-domain.com"]

# Restart backend
docker-compose restart backend
```

#### **Authentication Issues**
```bash
# Verify JWT configuration
python -c "
import jwt
import os
from dotenv import load_dotenv
load_dotenv()
secret = os.getenv('JWT_SECRET_KEY')
print(f'JWT Secret length: {len(secret)}')
print(f'JWT Secret valid: {len(secret) >= 32}')
"
```

---

## 📞 **Support Contacts**

### **Emergency Contacts**
- **Security Incidents**: security@your-domain.com
- **Crisis Escalation**: crisis@your-domain.com
- **Technical Support**: support@your-domain.com
- **Compliance Officer**: compliance@your-domain.com

### **Crisis Resources**
- **988 Suicide & Crisis Lifeline**: 988
- **Crisis Text Line**: 741741
- **Emergency Services**: 911
- **Crisis Chat**: https://suicidepreventionlifeline.org/chat/

---

## ✅ **Deployment Complete**

Once all items are checked:

🎉 **Sage is LIVE and ready to provide safe, compliant mental health support!**

**Remember:**
- Monitor crisis detection alerts closely
- Review security logs regularly
- Maintain compliance documentation
- Keep emergency contacts updated
- Test backup procedures monthly

**Sage is now serving users with enterprise-grade security and healthcare compliance.** 🚀