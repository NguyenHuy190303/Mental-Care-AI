#!/usr/bin/env python3
"""
Sage - Production Environment Setup Script
Generates secure environment variables for production deployment
"""

import secrets
import base64
import os
import sys
from pathlib import Path

def generate_secure_key(length=32):
    """Generate a secure random key."""
    return secrets.token_urlsafe(length)

def generate_encryption_key():
    """Generate a 32-byte encryption key encoded in base64."""
    key = secrets.token_bytes(32)
    return base64.b64encode(key).decode('utf-8')

def generate_password(length=16):
    """Generate a secure password."""
    return secrets.token_urlsafe(length)

def setup_production_env():
    """Setup production environment variables."""
    print("🚀 Sage - Production Environment Setup")
    print("=" * 50)
    
    # Check if .env already exists
    env_file = Path('.env')
    if env_file.exists():
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled.")
            return
    
    print("\n📝 Generating secure keys and passwords...")
    
    # Generate secure keys
    jwt_secret = generate_secure_key(32)
    jwt_refresh_secret = generate_secure_key(32)
    encryption_key = generate_encryption_key()
    field_encryption_key = generate_encryption_key()
    crisis_encryption_key = generate_encryption_key()
    backup_encryption_key = generate_encryption_key()
    
    # Generate passwords
    postgres_password = generate_password(16)
    redis_password = generate_password(16)
    
    # Get user inputs
    print("\n🔑 Please provide the following information:")
    
    openai_api_key = input("OpenAI API Key (sk-...): ").strip()
    if not openai_api_key.startswith('sk-'):
        print("❌ Invalid OpenAI API key format")
        return
    
    domain = input("Your domain (e.g., your-domain.com): ").strip()
    if not domain:
        print("❌ Domain is required")
        return
    
    environment = input("Environment (production/staging) [production]: ").strip() or "production"
    
    # Optional configurations
    print("\n🔧 Optional configurations (press Enter to skip):")
    alert_email = input("Alert email address: ").strip()
    slack_webhook = input("Slack webhook URL: ").strip()
    
    # Generate .env content
    env_content = f"""# ===========================================
# SAGE - MENTAL HEALTH AGENT CONFIGURATION
# PRODUCTION-READY WITH ENHANCED SECURITY
# Generated on: {__import__('datetime').datetime.now().isoformat()}
# ===========================================

# ===========================================
# CORE API CONFIGURATION
# ===========================================
OPENAI_API_KEY={openai_api_key}
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.3

# ===========================================
# JWT AUTHENTICATION (ENHANCED SECURITY)
# ===========================================
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_REFRESH_SECRET_KEY={jwt_refresh_secret}

# ===========================================
# DATABASE CONFIGURATION (SECURE)
# ===========================================
POSTGRES_PASSWORD={postgres_password}
DATABASE_URL=postgresql://mental_health_user:{postgres_password}@postgres:5432/mental_health_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# ===========================================
# REDIS CONFIGURATION (SECURE)
# ===========================================
REDIS_PASSWORD={redis_password}
REDIS_URL=redis://:{redis_password}@redis:6379/0
REDIS_SSL=false
REDIS_MAX_CONNECTIONS=100

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
ENVIRONMENT={environment}
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# ===========================================
# CORS & SECURITY HEADERS
# ===========================================
CORS_ORIGINS=["https://{domain}","https://www.{domain}"]
ALLOWED_HOSTS=["{domain}","www.{domain}","localhost"]
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_CONTENT_TYPE_NOSNIFF=true
SECURE_BROWSER_XSS_FILTER=true

# ===========================================
# CRISIS INTERVENTION & SAFETY (ENHANCED)
# ===========================================
ENABLE_CRISIS_DETECTION=true
CRISIS_DETECTION_MODEL=advanced_ml
ENABLE_CONTENT_FILTERING=true
ENABLE_SAFETY_LOGGING=true
ENABLE_CRISIS_MONITORING=true
CRISIS_ALERT_WEBHOOK=
EMERGENCY_CONTACT_API=

# Crisis Hotlines Configuration
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
AUDIT_LOG_RETENTION_DAYS=2555
ENABLE_DATA_ANONYMIZATION=true

# ===========================================
# CHROMADB CONFIGURATION
# ===========================================
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000
CHROMADB_SSL=false
CHROMADB_AUTH_TOKEN={generate_secure_key(24)}

# ===========================================
# RATE LIMITING & SECURITY
# ===========================================
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
MAX_REQUEST_SIZE=10485760
MAX_UPLOAD_SIZE=5242880

# Input Validation
ENABLE_PROMPT_INJECTION_PROTECTION=true
ENABLE_CONTENT_SCANNING=true
MAX_INPUT_LENGTH=4000
BLOCKED_PATTERNS=["<script>","javascript:","data:","vbscript:"]

# ===========================================
# MONITORING & ALERTING
# ===========================================
ENABLE_HEALTH_MONITORING=true
HEALTH_CHECK_INTERVAL=30
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_SECURITY_MONITORING=true

# Alerting Configuration
ALERT_EMAIL={alert_email}
SLACK_WEBHOOK={slack_webhook}
PAGERDUTY_API_KEY=

# ===========================================
# FRONTEND CONFIGURATION
# ===========================================
FRONTEND_URL=https://{domain}
BACKEND_URL=https://api.{domain}
WEBSOCKET_URL=wss://api.{domain}/api/ws

# ===========================================
# BACKUP & DISASTER RECOVERY
# ===========================================
ENABLE_AUTOMATED_BACKUPS=true
BACKUP_ENCRYPTION_KEY={backup_encryption_key}
BACKUP_RETENTION_DAYS=30
BACKUP_STORAGE_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# ===========================================
# KUBERNETES & CONTAINER SECURITY
# ===========================================
KUBERNETES_NAMESPACE=sage-production
ENABLE_POD_SECURITY_STANDARDS=true
ENABLE_NETWORK_POLICIES=true
ENABLE_RBAC=true
SERVICE_ACCOUNT_NAME=sage-service-account

# ===========================================
# EXTERNAL INTEGRATIONS (ENTERPRISE)
# ===========================================
# SSO Configuration
ENABLE_SSO=false
SAML_METADATA_URL=
OAUTH_CLIENT_ID=
OAUTH_CLIENT_SECRET=

# EHR Integration (FHIR)
ENABLE_EHR_INTEGRATION=false
FHIR_BASE_URL=
FHIR_CLIENT_ID=
FHIR_CLIENT_SECRET=

# ===========================================
# FEATURE FLAGS
# ===========================================
ENABLE_MULTIMODAL_INPUT=true
ENABLE_VOICE_PROCESSING=true
ENABLE_IMAGE_ANALYSIS=true
ENABLE_MEDICAL_IMAGE_SEARCH=true
ENABLE_ANALYTICS_DASHBOARD=true
ENABLE_FEEDBACK_SYSTEM=true
ENABLE_WHITE_LABEL=false

# ===========================================
# PERFORMANCE OPTIMIZATION
# ===========================================
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600
ENABLE_COMPRESSION=true
ENABLE_CDN=false
CDN_URL=

# ===========================================
# LEGAL & COMPLIANCE NOTICES
# ===========================================
PRIVACY_POLICY_URL=https://{domain}/privacy
TERMS_OF_SERVICE_URL=https://{domain}/terms
MEDICAL_DISCLAIMER_URL=https://{domain}/medical-disclaimer
HIPAA_NOTICE_URL=https://{domain}/hipaa-notice

# ===========================================
# SECURITY CONTACT INFORMATION
# ===========================================
SECURITY_CONTACT_EMAIL=security@{domain}
INCIDENT_RESPONSE_PHONE=+1-555-SECURITY
COMPLIANCE_OFFICER_EMAIL=compliance@{domain}
"""

    # Write .env file
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ Environment configuration saved to .env")
    print(f"🔐 Generated secure keys and passwords")
    print(f"🌐 Configured for domain: {domain}")
    
    # Create summary file
    summary_content = f"""# Sage - Environment Setup Summary

## Generated Keys (KEEP SECURE!)
- JWT Secret Key: {jwt_secret[:10]}...
- JWT Refresh Secret: {jwt_refresh_secret[:10]}...
- Encryption Key: {encryption_key[:10]}...
- Field Encryption Key: {field_encryption_key[:10]}...
- Crisis Encryption Key: {crisis_encryption_key[:10]}...
- Backup Encryption Key: {backup_encryption_key[:10]}...

## Generated Passwords
- PostgreSQL Password: {postgres_password}
- Redis Password: {redis_password}

## Configuration
- Domain: {domain}
- Environment: {environment}
- OpenAI API Key: {openai_api_key[:10]}...

## Next Steps
1. Review and customize .env file as needed
2. Set up DNS records for your domain
3. Configure SSL certificates
4. Run: docker-compose up -d
5. Test: curl https://api.{domain}/api/health

## Security Notes
- All keys are cryptographically secure
- Passwords meet enterprise security standards
- HIPAA/GDPR compliance enabled
- Crisis detection and monitoring enabled

Generated on: {__import__('datetime').datetime.now().isoformat()}
"""
    
    with open('ENVIRONMENT_SETUP_SUMMARY.md', 'w') as f:
        f.write(summary_content)
    
    print(f"📋 Setup summary saved to ENVIRONMENT_SETUP_SUMMARY.md")
    
    print("\n🚀 Next Steps:")
    print("1. Review .env file and customize as needed")
    print("2. Set up your domain DNS records")
    print("3. Configure SSL certificates")
    print("4. Run: docker-compose up -d")
    print(f"5. Test: curl https://api.{domain}/api/health")
    
    print("\n⚠️  IMPORTANT SECURITY NOTES:")
    print("- Keep your .env file secure and never commit it to git")
    print("- Store backup copies of your encryption keys securely")
    print("- Set up monitoring and alerting for production")
    print("- Review security settings before going live")

def main():
    """Main function."""
    try:
        setup_production_env()
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()