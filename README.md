# Sage

![Mental Health Hub](https://media.post.rvohealth.io/wp-content/uploads/sites/3/2021/03/609849-mental-health-hub-1200x628-facebook.jpg)

## AI-Powered Comprehensive Healthcare Support System

## Project Overview
Sage is a comprehensive healthcare support system built on a **Single-Threaded Linear Agent** architecture. The system provides AI-powered medical information and assistance across **all healthcare domains and medical specialties**, including but not limited to internal medicine, cardiology, neurology, oncology, pediatrics, geriatrics, emergency medicine, and mental health. It prioritizes reliability, context integrity, and medical safety through scientifically-backed responses with proper citations from authoritative medical sources.

**Current Status**: ✅ **PRODUCTION READY** - Complete enterprise-grade system with all 18 tasks implemented and validated, plus enhanced AI model integration and comprehensive user onboarding.

### Key Features
- **Single-Threaded Linear Agent**: One main agent processes requests sequentially through specialized tools
- **Scientific Citations**: All medical information backed by authoritative sources (PubMed, WHO, CDC)
- **Multimodal Support**: Text, image, and voice input capabilities with PWA mobile optimization
- **Advanced Crisis Detection**: ML-based crisis intervention with real-time monitoring and emergency resources
- **Enterprise Security**: HIPAA/GDPR compliant with field-level encryption and comprehensive audit logging
- **Context Engineering**: Advanced context management for consistent, reliable responses
- **Enterprise Integration**: SSO, EHR integration (FHIR), API Gateway, and white-label capabilities
- **Security Monitoring**: Real-time security monitoring with automated threat detection and alerting
- **Production Infrastructure**: Kubernetes deployment with Pod Security Standards and Network Policies

## Architecture

### Technology Stack
- **Backend**: FastAPI + LangChain + ChromaDB
- **Frontend**: Open WebUI (planned)
- **Database**: PostgreSQL + ChromaDB + Redis
- **AI Models**: Google Gemini 2.5 Pro (default), OpenAI GPT-4o-mini with intelligent model routing
- **Deployment**: Docker + GitHub Actions + Vercel/Render

### System Architecture
```
User Input → Open WebUI → FastAPI Backend → Linear Agent → [Sequential Tools] → LLM → Response
```

### 🤖 AI Model Configuration

Sage supports multiple advanced AI models with intelligent routing for optimal healthcare responses:

#### Supported Models
- **Google Gemini 2.5 Pro**: Default primary model for healthcare applications
  - High safety settings optimized for medical content
  - Advanced reasoning capabilities for complex medical queries
  - Multimodal support for text, image, and voice processing
- **OpenAI GPT-4o-mini**: Alternative model with healthcare optimization
  - Cost-effective for routine medical information queries
  - Reliable performance with medical knowledge base

#### Healthcare-Optimized Features
- **Default Healthcare Model**: Google Gemini (configurable via `DEFAULT_HEALTHCARE_MODEL`)
- **Healthcare Mode**: Specialized prompts and safety measures (`SAGE_HEALTHCARE_MODE=true`)
- **Model Routing**: Intelligent switching based on query complexity (`MODEL_ROUTING_ENABLED=true`)
- **Conservative Temperature**: 0.3 for both models to ensure medical accuracy
- **Safety Settings**: High-level safety configurations for medical content
- **Fallback Support**: Automatic fallback between models for reliability

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- OpenAI API Key

### 🚀 Option 1: Quick Setup Script (Recommended)

The fastest way to get Sage running locally:

```bash
git clone https://github.com/NguyenHuy190303/Sage.git
cd Sage

# Run the quick setup script
python scripts/quick-setup.py

# Start all services
docker-compose up -d

# Test the deployment
./test-local.sh
```

The quick setup script will:
- ✅ Generate secure encryption keys for HIPAA/GDPR compliance
- ✅ Create strong passwords for PostgreSQL and Redis
- ✅ Configure JWT authentication with secure secrets
- ✅ Set up crisis detection and safety monitoring
- ✅ Create Docker override configuration for development
- ✅ Generate a test script to verify all services

**Access Points After Setup:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database Admin (PgAdmin)**: http://localhost:5050
- **ChromaDB**: http://localhost:8001

### 🔧 Option 2: Manual Setup

```bash
git clone https://github.com/NguyenHuy190303/Salus-Analytica.git
cd Sage

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Start all services
docker-compose up -d
```

**⚠️ Important Note**: If you encounter Docker build errors related to `requirements.txt` not found, see the troubleshooting section in [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md#docker-build-issues) for solutions.

### 🏭 Option 3: Production Setup

For production deployment with enhanced security:

```bash
# Generate production environment
python scripts/setup-production-env.py

# Validate configuration
python scripts/validate-environment.py

# Deploy
docker-compose up -d
```

### 🛠️ Development Setup (Alternative)

```bash
# Create Python environment
conda create -n mental_env python=3.11
conda activate mental_env

# Install dependencies
pip install -r requirements.txt

# Start backend locally
cd backend
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
mental-health-agent/
├── backend/                 # FastAPI backend application
│   ├── src/                # Source code
│   │   ├── api/           # API endpoints
│   │   ├── agents/        # AI agent implementations
│   │   ├── database/      # Database models and connections
│   │   ├── models/        # Pydantic data models
│   │   ├── tools/         # Agent tools (RAG, Context, etc.)
│   │   ├── utils/         # Utility functions
│   │   └── main.py        # Application entry point
│   ├── database/          # Database initialization scripts
│   └── Dockerfile         # Backend container configuration
├── frontend/               # Open WebUI frontend (planned)
├── config/                # Configuration management
│   ├── settings.py        # Application settings
│   └── logging.py         # Logging configuration
├── data/                  # Data storage directories
├── tests/                 # Test suites
├── scripts/               # Development scripts
└── docker-compose.yml     # Development environment
```

## Development Commands

```bash
# Start all services
docker-compose up -d

# Start with development tools (PgAdmin)
docker-compose --profile dev-tools up -d

# View logs
docker-compose logs -f backend

# Run tests
pytest tests/

# Stop services
docker-compose down
```

## Documentation

### API Documentation
Once the backend is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

### 📚 Documentation Structure

For comprehensive documentation, see the **[docs/](docs/)** directory:

#### 🚀 Setup & Development Guides
- **[Development Guide](docs/guides/DEVELOPMENT.md)**: Development environment setup and guidelines
- **[Local Setup Guide](docs/guides/LOCAL_SETUP_GUIDE.md)**: Detailed local development setup
- **[Deployment Checklist](docs/guides/DEPLOYMENT_CHECKLIST.md)**: Production deployment guide

#### 📊 Technical Documentation  
- **[Quick Setup Guide](docs/QUICK_SETUP_GUIDE.md)**: Automated quick setup script guide
- **[AI Model Configuration](docs/AI_MODEL_CONFIGURATION.md)**: Multi-model AI setup with Gemini and OpenAI
- **[RAG System Guide](docs/RAG_SYSTEM.md)**: Document ingestion and retrieval system
- **[Healthcare Onboarding System](docs/HEALTHCARE_ONBOARDING_SYSTEM.md)**: User onboarding documentation
- **[Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)**: Production deployment guide
- **[Knowledge Base Assessment](docs/KNOWLEDGE_BASE_ASSESSMENT.md)**: Medical knowledge base analysis

#### 📈 Project Reports
- **[Project Completion Summary](docs/reports/PROJECT_COMPLETION_SUMMARY.md)**: Overall project status
- **[System Validation Summary](docs/reports/SYSTEM_VALIDATION_SUMMARY.md)**: Testing and validation results
- **[Implementation Summary](docs/reports/IMPLEMENTATION_SUMMARY.md)**: Architecture and implementation details
- **[System Enhancements Summary](docs/SYSTEM_ENHANCEMENTS_SUMMARY.md)**: Recent improvements and features

#### 🏗️ Architecture
- **[Architecture Overview](.kiro/steering/architecture.md)**: System design principles and patterns

## Contributing

This project follows the Single-Threaded Linear Agent pattern. When contributing:

1. **No Parallel Sub-Agents**: Use sequential tool execution only
2. **Context Integrity**: Maintain complete context throughout processing
3. **Medical Safety**: Always include proper disclaimers and safety checks
4. **Scientific Citations**: Back all medical information with authoritative sources

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Legacy System

The original Streamlit-based system (formerly "Mental Care AI") is being migrated to this new architecture under the name "SAGE". Legacy UI screenshots and system diagrams are preserved for reference but represent the previous implementation.
