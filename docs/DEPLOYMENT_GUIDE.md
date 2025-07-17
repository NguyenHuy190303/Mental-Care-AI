# Mental Health Agent - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Mental Health Agent system in production environments. The system follows the Single-Threaded Linear Agent pattern and includes comprehensive safety, compliance, and monitoring features.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Databases     │
│  (Open WebUI)   │◄──►│   (FastAPI)     │◄──►│  PostgreSQL     │
│                 │    │                 │    │  ChromaDB       │
│                 │    │                 │    │  Redis          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **CPU**: Minimum 4 cores, 8 cores recommended
- **Memory**: Minimum 8GB RAM, 16GB recommended
- **Storage**: Minimum 50GB free space, SSD recommended
- **Network**: Stable internet connection for AI model API calls

### Software Dependencies

- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Python**: 3.9+ (for development)
- **Node.js**: 18+ (for frontend development)

### External Services

- **OpenAI API**: Valid API key with GPT-4 access
- **Email Service**: SMTP server for notifications (optional)
- **Monitoring**: Webhook endpoints for alerts (optional)

## Quick Start Deployment

### 1. Clone Repository

```bash
git clone https://github.com/your-org/mental-health-agent.git
cd mental-health-agent
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Critical Environment Variables:**

```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here

# Security (CHANGE IN PRODUCTION)
POSTGRES_PASSWORD=secure_postgres_password
REDIS_PASSWORD=secure_redis_password
JWT_SECRET_KEY=your_jwt_secret_32_chars_minimum
ENCRYPTION_KEY=your_encryption_key_32_chars_minimum

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 3. Start Services

```bash
# Using the startup script (recommended)
chmod +x scripts/start-mental-health-agent.sh
./scripts/start-mental-health-agent.sh

# Or manually with Docker Compose
docker-compose up -d
```

### 4. Verify Deployment

```bash
# Check service health
curl http://localhost:8000/api/monitoring/health

# Check frontend
curl http://localhost:3000

# View logs
docker-compose logs -f
```

## Production Deployment

### 1. Security Configuration

#### SSL/TLS Setup

```bash
# Generate SSL certificates (using Let's Encrypt)
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# Update nginx configuration
cp nginx/nginx.conf.example nginx/nginx.conf
# Edit SSL certificate paths
```

#### Environment Security

```bash
# Generate secure secrets
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 32  # For ENCRYPTION_KEY

# Set restrictive file permissions
chmod 600 .env
chown root:root .env
```

### 2. Database Configuration

#### PostgreSQL Production Setup

```yaml
# docker-compose.prod.yml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: mental_health_db
    POSTGRES_USER: mental_health_user
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./backups:/backups
  command: >
    postgres
    -c shared_preload_libraries=pg_stat_statements
    -c max_connections=200
    -c shared_buffers=256MB
    -c effective_cache_size=1GB
```

#### Backup Configuration

```bash
# Create backup script
cat > scripts/backup-database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U mental_health_user mental_health_db > $BACKUP_DIR/backup_$TIMESTAMP.sql
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x scripts/backup-database.sh

# Add to crontab
echo "0 2 * * * /path/to/scripts/backup-database.sh" | crontab -
```

### 3. Monitoring and Alerting

#### Health Monitoring

```bash
# Add health check monitoring
cat > scripts/health-monitor.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:8000/api/monitoring/health"
WEBHOOK_URL="your-webhook-url"

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -ne 200 ]; then
    curl -X POST $WEBHOOK_URL \
        -H "Content-Type: application/json" \
        -d '{"text":"Mental Health Agent health check failed: HTTP '$RESPONSE'"}'
fi
EOF

chmod +x scripts/health-monitor.sh

# Add to crontab (every 5 minutes)
echo "*/5 * * * * /path/to/scripts/health-monitor.sh" | crontab -
```

#### Log Monitoring

```bash
# Configure log rotation
cat > /etc/logrotate.d/mental-health-agent << 'EOF'
/var/log/mental-health-agent/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose restart backend
    endscript
}
EOF
```

### 4. Performance Optimization

#### Resource Limits

```yaml
# docker-compose.prod.yml
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G

frontend:
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 2G
      reservations:
        cpus: '0.5'
        memory: 1G
```

#### Caching Configuration

```bash
# Redis production configuration
redis:
  command: >
    redis-server
    --maxmemory 1gb
    --maxmemory-policy allkeys-lru
    --save 900 1
    --save 300 10
    --save 60 10000
```

## Compliance and Security

### GDPR Compliance

1. **Data Encryption**: All data encrypted at rest and in transit
2. **User Consent**: Implement consent management
3. **Data Deletion**: Automated data retention policies
4. **Audit Logging**: Comprehensive audit trails

### HIPAA Compliance

1. **Access Controls**: Role-based access control
2. **Audit Controls**: Detailed access logging
3. **Integrity Controls**: Data integrity verification
4. **Transmission Security**: Encrypted communications

### Safety Features

1. **Crisis Intervention**: Automatic crisis detection and resource provision
2. **Medical Disclaimers**: Required disclaimers for medical content
3. **Content Filtering**: Inappropriate content detection
4. **Safety Monitoring**: Continuous safety assessment

## Maintenance and Updates

### Regular Maintenance Tasks

```bash
# Weekly maintenance script
cat > scripts/weekly-maintenance.sh << 'EOF'
#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean Docker resources
docker system prune -f

# Backup database
./scripts/backup-database.sh

# Check disk space
df -h

# Check service health
curl -f http://localhost:8000/api/monitoring/health || echo "Health check failed"
EOF
```

### Update Procedure

```bash
# 1. Backup current state
./scripts/backup-database.sh
docker-compose down
cp -r . ../mental-health-agent-backup-$(date +%Y%m%d)

# 2. Pull updates
git pull origin main

# 3. Update dependencies
docker-compose pull
docker-compose build

# 4. Apply database migrations
docker-compose run backend python -m alembic upgrade head

# 5. Restart services
docker-compose up -d

# 6. Verify deployment
curl -f http://localhost:8000/api/monitoring/health
```

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Check disk space
df -h

# Check memory usage
free -h

# Restart services
docker-compose restart
```

#### Database Connection Issues

```bash
# Check database health
docker-compose exec postgres pg_isready -U mental_health_user

# Check connection from backend
docker-compose exec backend python -c "
from src.database import check_database_health
import asyncio
print(asyncio.run(check_database_health()))
"
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Check database performance
docker-compose exec postgres psql -U mental_health_user -d mental_health_db -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"

# Check Redis memory usage
docker-compose exec redis redis-cli info memory
```

### Emergency Procedures

#### System Recovery

```bash
# 1. Stop all services
docker-compose down

# 2. Restore from backup
cp -r ../mental-health-agent-backup-YYYYMMDD/* .

# 3. Restore database
docker-compose up -d postgres
docker-compose exec postgres psql -U mental_health_user -d mental_health_db < /backups/backup_YYYYMMDD_HHMMSS.sql

# 4. Start all services
docker-compose up -d
```

#### Crisis Response

```bash
# Immediate crisis response checklist:
# 1. Check crisis intervention system
curl http://localhost:8000/api/monitoring/health | jq '.components.ai_model'

# 2. Verify emergency resources are accessible
curl http://localhost:8000/api/agent/emergency-resources

# 3. Check safety monitoring
curl http://localhost:8000/api/monitoring/metrics | jq '.safety_metrics'

# 4. Alert administrators
# (Use your organization's emergency notification system)
```

## Support and Documentation

### Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **System Health**: http://localhost:8000/api/monitoring/health
- **Logs Location**: `./backend/logs/`
- **Configuration**: `.env` file

### Contact Information

- **Technical Support**: [your-support-email]
- **Emergency Contact**: [emergency-contact]
- **Documentation**: [documentation-url]

---

**Important**: This system handles sensitive mental health data. Ensure all security, privacy, and compliance requirements are met before deploying to production.
