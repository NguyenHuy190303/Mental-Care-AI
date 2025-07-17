# Sage - Production Deployment Guide

## 🚀 Production Environment Setup

Sage includes a comprehensive production environment setup script that generates secure configurations for enterprise deployment. This guide covers the complete production deployment process.

## 📋 Prerequisites

Before deploying to production, ensure you have:

- **Domain Name**: A registered domain for your deployment
- **OpenAI API Key**: Valid OpenAI API key with sufficient credits
- **SSL Certificates**: SSL/TLS certificates for HTTPS
- **Infrastructure**: Docker/Kubernetes environment ready
- **Monitoring**: Alerting and monitoring systems configured

## 🔧 Production Environment Configuration

### Automated Setup Script

Use the production environment setup script to generate secure configurations:

```bash
python scripts/setup-production-env.py
```

### Interactive Configuration

The script will prompt for:

1. **OpenAI API Key** (required): Your OpenAI API key starting with `sk-`
2. **Google Gemini API Key** (recommended): Your Google AI API key for the default healthcare model
3. **Domain Name** (required): Your production domain (e.g., `your-domain.com`)
4. **Environment Type**: `production` or `staging` (default: production)
5. **Alert Email** (optional): Email for system alerts
6. **Slack Webhook** (optional): Slack webhook for notifications

### Generated Security Features

The script automatically generates:

- **JWT Secrets**: Cryptographically secure JWT signing keys
- **Encryption Keys**: HIPAA/GDPR compliant encryption keys for health data
- **Database Passwords**: Secure passwords for PostgreSQL and Redis
- **API Tokens**: Secure tokens for service authentication
- **Security Headers**: Complete security header configuration

## 🔐 Security Configuration

### Encryption & Compliance

```bash
# HIPAA/GDPR Compliance Keys (Auto-generated)
ENCRYPTION_KEY=<32-byte-base64-key>           # Primary health data encryption
FIELD_ENCRYPTION_KEY=<32-byte-base64-key>     # PII field-level encryption
CRISIS_ENCRYPTION_KEY=<32-byte-base64-key>    # Crisis data encryption
BACKUP_ENCRYPTION_KEY=<32-byte-base64-key>    # Backup encryption
```

### Authentication & Authorization

```bash
# JWT Configuration (Auto-generated)
JWT_SECRET_KEY=<secure-32-char-key>
JWT_REFRESH_SECRET_KEY=<secure-32-char-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Database Security

```bash
# Secure Database Configuration (Auto-generated)
POSTGRES_PASSWORD=<secure-16-char-password>
REDIS_PASSWORD=<secure-16-char-password>
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

## 🛡️ Safety & Crisis Intervention

### Crisis Detection Configuration

```bash
# Enhanced Crisis Detection
ENABLE_CRISIS_DETECTION=true
CRISIS_DETECTION_MODEL=advanced_ml
ENABLE_CONTENT_FILTERING=true
ENABLE_SAFETY_LOGGING=true
ENABLE_CRISIS_MONITORING=true

# Crisis Hotlines (US Configuration)
CRISIS_HOTLINE_988=988
CRISIS_TEXT_LINE=741741
EMERGENCY_NUMBER=911
CRISIS_CHAT_URL=https://suicidepreventionlifeline.org/chat/
```

### Content Safety

```bash
# Input Validation & Security
ENABLE_PROMPT_INJECTION_PROTECTION=true
ENABLE_CONTENT_SCANNING=true
MAX_INPUT_LENGTH=4000
BLOCKED_PATTERNS=["<script>","javascript:","data:","vbscript:"]
```

## 📊 Monitoring & Alerting

### Health Monitoring

```bash
# System Monitoring
ENABLE_HEALTH_MONITORING=true
HEALTH_CHECK_INTERVAL=30
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_SECURITY_MONITORING=true
```

### Alert Configuration

```bash
# Alerting Channels
ALERT_EMAIL=admin@your-domain.com
SLACK_WEBHOOK=https://hooks.slack.com/your-webhook
PAGERDUTY_API_KEY=your-pagerduty-key
```

## 🏥 Healthcare Compliance

### HIPAA/GDPR Configuration

```bash
# Compliance Settings
ENABLE_AUDIT_LOGGING=true
GDPR_COMPLIANCE=true
HIPAA_COMPLIANCE=true
DATA_RETENTION_DAYS=90
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years for HIPAA
ENABLE_DATA_ANONYMIZATION=true
```

### Legal & Compliance URLs

```bash
# Legal Documentation
PRIVACY_POLICY_URL=https://your-domain.com/privacy
TERMS_OF_SERVICE_URL=https://your-domain.com/terms
MEDICAL_DISCLAIMER_URL=https://your-domain.com/medical-disclaimer
HIPAA_NOTICE_URL=https://your-domain.com/hipaa-notice
```

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended for Small-Medium Scale)

```bash
# After running setup script
docker-compose up -d

# Verify deployment
curl https://api.your-domain.com/api/health
```

### Option 2: Kubernetes (Enterprise Scale)

```bash
# Apply Kubernetes manifests
kubectl apply -f infrastructure/kubernetes/

# Check deployment status
kubectl get pods -n sage-production
```

### Option 3: Cloud Native (AWS/GCP/Azure)

```bash
# Deploy using cloud-specific configurations
# See infrastructure/scripts/ for cloud deployment scripts
```

## 🔍 Post-Deployment Verification

### Health Checks

```bash
# API Health Check
curl https://api.your-domain.com/api/health

# Database Connectivity
curl https://api.your-domain.com/api/health/database

# AI Model Connectivity
curl https://api.your-domain.com/api/health/ai-models
```

### Security Validation

```bash
# SSL Certificate Check
curl -I https://your-domain.com

# Security Headers Check
curl -I https://api.your-domain.com/api/health
```

### Crisis Detection Testing

```bash
# Test crisis detection (use test endpoints only)
curl -X POST https://api.your-domain.com/api/test/crisis-detection \
  -H "Content-Type: application/json" \
  -d '{"message": "test crisis scenario"}'
```

## 📈 Performance Optimization

### Caching Configuration

```bash
# Redis Caching
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600
REDIS_MAX_CONNECTIONS=100
```

### Rate Limiting

```bash
# API Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
```

### Content Delivery

```bash
# CDN Configuration
ENABLE_CDN=true
CDN_URL=https://cdn.your-domain.com
ENABLE_COMPRESSION=true
```

## 🔄 Backup & Disaster Recovery

### Automated Backups

```bash
# Backup Configuration
ENABLE_AUTOMATED_BACKUPS=true
BACKUP_RETENTION_DAYS=30
BACKUP_STORAGE_URL=s3://your-backup-bucket
```

### Disaster Recovery

```bash
# AWS Configuration for Backups
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
```

## 🏢 Enterprise Features

### Single Sign-On (SSO)

```bash
# SSO Configuration
ENABLE_SSO=true
SAML_METADATA_URL=https://your-idp.com/metadata
OAUTH_CLIENT_ID=your-oauth-client-id
OAUTH_CLIENT_SECRET=your-oauth-client-secret
```

### EHR Integration (FHIR)

```bash
# Healthcare System Integration
ENABLE_EHR_INTEGRATION=true
FHIR_BASE_URL=https://your-fhir-server.com
FHIR_CLIENT_ID=your-fhir-client-id
FHIR_CLIENT_SECRET=your-fhir-client-secret
```

### White-Label Customization

```bash
# Branding Configuration
ENABLE_WHITE_LABEL=true
BRAND_NAME=Your Healthcare Organization
BRAND_LOGO_URL=https://your-domain.com/logo.png
BRAND_PRIMARY_COLOR=#your-color
```

## 📞 Security Contact Information

### Incident Response

```bash
# Security Contacts
SECURITY_CONTACT_EMAIL=security@your-domain.com
INCIDENT_RESPONSE_PHONE=+1-555-SECURITY
COMPLIANCE_OFFICER_EMAIL=compliance@your-domain.com
```

## ⚠️ Important Security Notes

### Key Management
- **Store encryption keys securely** - Never commit to version control
- **Backup encryption keys** - Store in secure key management system
- **Rotate keys regularly** - Implement key rotation schedule
- **Monitor key usage** - Track and audit key access

### Access Control
- **Principle of least privilege** - Grant minimum required permissions
- **Multi-factor authentication** - Enable MFA for all admin accounts
- **Regular access reviews** - Audit user permissions quarterly
- **Session management** - Implement secure session handling

### Monitoring & Alerting
- **Real-time monitoring** - Monitor all critical system metrics
- **Security alerts** - Set up alerts for security events
- **Performance monitoring** - Track response times and errors
- **Compliance monitoring** - Monitor HIPAA/GDPR compliance metrics

## 🆘 Emergency Procedures

### Crisis Response
1. **Immediate Response**: Crisis detection triggers automatic resource provision
2. **Escalation**: Severe cases escalated to human crisis counselors
3. **Documentation**: All crisis interventions logged for compliance
4. **Follow-up**: Automated follow-up procedures for user safety

### System Incidents
1. **Detection**: Automated monitoring detects issues
2. **Alerting**: Immediate alerts sent to on-call team
3. **Response**: Incident response team activated
4. **Recovery**: System restored with minimal downtime
5. **Post-mortem**: Incident analysis and prevention measures

## 📚 Additional Resources

- [Kubernetes Deployment Guide](./KUBERNETES_DEPLOYMENT.md)
- [Security Best Practices](./SECURITY_GUIDE.md)
- [HIPAA Compliance Checklist](./HIPAA_COMPLIANCE.md)
- [Crisis Intervention Procedures](./CRISIS_PROCEDURES.md)
- [API Documentation](./API_DOCUMENTATION.md)

---

*For technical support or security concerns, contact: security@your-domain.com*