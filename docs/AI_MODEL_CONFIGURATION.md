# 🤖 Sage - AI Model Configuration Guide

## Overview

Sage supports multiple advanced AI models with intelligent routing for optimal healthcare responses. The system is configured to use Google Gemini 1.5 Pro as the default model with OpenAI GPT-4o-mini as a fallback, providing comprehensive healthcare support across all medical specialties.

---

## 🎯 **Supported AI Models**

### **Google Gemini 1.5 Pro** (Default)
- **Model ID**: `gemini-1.5-pro`
- **Primary Use**: Default model for all healthcare applications
- **Strengths**: 
  - Advanced reasoning capabilities for complex medical queries
  - High safety settings optimized for medical content
  - Multimodal support (text, image, voice)
  - Cost-effective for comprehensive healthcare coverage
  - Extensive medical knowledge base

### **OpenAI GPT-4o-mini** (Fallback)
- **Model ID**: `gpt-4o-mini`
- **Primary Use**: Fallback model and alternative for specific use cases
- **Strengths**:
  - Reliable performance with medical knowledge
  - Fast response times for routine queries
  - Well-tested healthcare applications
  - Strong reasoning capabilities

---

## ⚙️ **Configuration Settings**

### **Environment Variables**

```bash
# Google Gemini Configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-pro
GEMINI_MAX_TOKENS=2000
GEMINI_TEMPERATURE=0.3
GEMINI_SAFETY_SETTINGS=high

# OpenAI Configuration (Fallback)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.3

# Healthcare Model Configuration
DEFAULT_HEALTHCARE_MODEL=gemini
SAGE_HEALTHCARE_MODE=true
MODEL_ROUTING_ENABLED=true
```

### **Docker Compose Configuration**

```yaml
services:
  backend:
    environment:
      # AI Model Configuration
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_MODEL=gemini-1.5-pro
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=gpt-4o-mini
      
      # Healthcare Configuration
      - DEFAULT_HEALTHCARE_MODEL=gemini
      - SAGE_HEALTHCARE_MODE=true
      - MODEL_ROUTING_ENABLED=true
      - OPENAI_TEMPERATURE=0.3
      - GEMINI_TEMPERATURE=0.3
```

---

## 🧠 **Intelligent Model Routing**

### **Routing Logic**

The system automatically selects the optimal model based on query complexity and urgency:

```python
# Simple Queries → Gemini Pro
Query: "What is aspirin?"
→ Uses: Gemini 1.5 Pro (efficient, comprehensive)

# Complex Queries → Gemini Pro
Query: "Explain heart failure pathophysiology and treatment options"
→ Uses: Gemini 1.5 Pro (comprehensive medical knowledge)

# Critical Queries → Best Available Model
Query: "I'm having chest pain and difficulty breathing"
→ Uses: Gemini 1.5 Pro or GPT-4 Advanced (most capable, safety-focused)
```

### **Complexity Assessment Factors**

1. **Urgency Level**: High urgency queries (8+/10) → Advanced models
2. **Medical Entities**: Multiple medical terms → Complex routing
3. **Crisis Keywords**: Emergency terms → Critical routing
4. **RAG Results**: Extensive knowledge needed → Complex routing

### **Fallback Strategy**

```python
# Primary: Gemini 1.5 Pro
if gemini_available:
    return ("gemini", "gemini-1.5-pro")

# Fallback: OpenAI GPT-4o-mini
elif openai_available:
    return ("openai", "gpt-4o-mini")

# Error: No models available
else:
    raise ValueError("No AI models available")
```

---

## 🏥 **Healthcare-Specific Optimizations**

### **Medical Safety Settings**

```python
# Gemini Safety Configuration
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}
```

### **Healthcare Mode Features**

When `SAGE_HEALTHCARE_MODE=true`:
- **Conservative Temperature**: 0.3 for medical accuracy
- **Medical Disclaimers**: Automatic inclusion in all responses
- **Professional Consultation**: Recommendations for human medical oversight
- **Crisis Detection**: Enhanced safety monitoring
- **Evidence-Based**: Emphasis on scientific citations

### **Specialized Healthcare Prompts**

```python
healthcare_prompt = """
You are Sage, a comprehensive healthcare AI assistant with expertise across all medical specialties:

MEDICAL SPECIALTIES COVERED:
- Internal Medicine & Family Practice
- Cardiology & Cardiovascular Health  
- Endocrinology & Metabolism
- Oncology & Cancer Care
- Pediatrics & Child Health
- Geriatrics & Elderly Care
- Emergency Medicine & Critical Care
- Infectious Diseases & Prevention
- Women's Health & Obstetrics
- Mental Health & Psychiatry

CRITICAL SAFETY GUIDELINES:
1. Always include comprehensive medical disclaimers
2. Encourage professional consultation for all medical concerns
3. Provide crisis resources for emergency situations
4. Never diagnose or prescribe medications
5. Cite authoritative medical sources when available
6. Indicate confidence levels and uncertainty
"""
```

---

## 🔧 **Setup Instructions**

### **1. API Key Configuration**

#### **Google Gemini API Key**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to your `.env` file:
   ```bash
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

#### **OpenAI API Key** (Optional Fallback)
1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to your `.env` file:
   ```bash
   OPENAI_API_KEY=your-openai-api-key-here
   ```

### **2. Model Configuration**

Update your `.env` file with healthcare-optimized settings:

```bash
# Primary Model (Gemini)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-pro
GEMINI_TEMPERATURE=0.3
GEMINI_SAFETY_SETTINGS=high

# Fallback Model (OpenAI)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3

# Healthcare Configuration
DEFAULT_HEALTHCARE_MODEL=gemini
SAGE_HEALTHCARE_MODE=true
MODEL_ROUTING_ENABLED=true
```

### **3. Validation**

Test your configuration:

```bash
# Run model configuration test
python validate_model_config.py

# Expected output:
# ✅ Environment variables configured correctly
# ✅ Gemini API key format valid
# ✅ Healthcare mode enabled
# ✅ Model routing enabled
```

---

## 🧪 **Testing & Validation**

### **Model Integration Test**

```bash
# Run comprehensive model integration test
python test_model_integration.py

# Expected results:
# ✅ Model configuration validation passed
# ✅ Gemini client initialization successful
# ✅ OpenAI client initialization successful
# ✅ Healthcare mode configuration correct
# ✅ Model routing logic working
```

### **Healthcare Response Test**

```bash
# Test healthcare-specific responses
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the symptoms of diabetes and how is it diagnosed?",
    "user_id": "test_user",
    "session_id": "test_session"
  }'

# Expected response includes:
# - Comprehensive medical information
# - Scientific citations
# - Medical disclaimers
# - Professional consultation recommendations
```

---

## 📊 **Performance Monitoring**

### **Model Usage Tracking**

Monitor which models are being used:

```bash
# Check backend logs for model routing
docker-compose logs backend | grep "Using"

# Expected output:
# Using gemini:gemini-1.5-pro for complex query
# Using gemini:gemini-1.5-pro for simple query
# Using openai:gpt-4o-mini for fallback query
```

### **Cost Optimization**

The intelligent routing system optimizes costs by:
- **Primary Gemini Usage**: Cost-effective for most healthcare queries
- **Efficient Routing**: Right model for each complexity level
- **Fallback Strategy**: Prevents service interruption
- **Usage Monitoring**: Track API usage and costs

---

## 🔒 **Security & Compliance**

### **Healthcare Data Protection**

- **HIPAA Compliance**: All model interactions comply with healthcare data protection
- **Audit Logging**: Complete logging of all AI model interactions
- **Data Encryption**: All API communications encrypted in transit
- **Access Control**: Proper authentication for all model access

### **Medical Safety Measures**

- **High Safety Settings**: Maximum safety configurations for medical content
- **Content Filtering**: Automatic filtering of inappropriate medical content
- **Crisis Detection**: Real-time monitoring for medical emergencies
- **Professional Oversight**: Clear guidance for human medical supervision

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Gemini API Key Issues**
```bash
# Error: Invalid API key
# Solution: Verify key format and permissions
echo $GEMINI_API_KEY | grep "^AIza"
```

#### **Model Unavailable**
```bash
# Error: Model not available
# Solution: System automatically falls back to available models
# Check logs: docker-compose logs backend | grep "model"
```

#### **Rate Limiting**
```bash
# Error: Rate limit exceeded
# Solution: Gemini has generous rate limits, but implement backoff
# Monitor usage in Google AI Studio console
```

### **Health Check**

```bash
# Verify system health
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "app_name": "Sage",
  "ai_models": {
    "gemini": "available",
    "openai": "available"
  },
  "default_model": "gemini"
}
```

---

## 🎯 **Best Practices**

### **For Healthcare Applications**

1. **Always Use Healthcare Mode**: Set `SAGE_HEALTHCARE_MODE=true`
2. **Conservative Temperature**: Use 0.3 for medical accuracy
3. **Enable Model Routing**: Allow intelligent model selection
4. **Monitor Usage**: Track model performance and costs
5. **Regular Testing**: Validate model responses for medical accuracy

### **For Production Deployment**

1. **Secure API Keys**: Use environment variables, never hardcode
2. **Enable Monitoring**: Track model usage and performance
3. **Implement Fallbacks**: Ensure service continuity
4. **Regular Updates**: Keep model configurations current
5. **Compliance Validation**: Regular HIPAA/GDPR compliance checks

---

## 📞 **Support**

### **Technical Support**
- **Configuration Issues**: Check environment variables and API keys
- **Model Performance**: Monitor logs and usage patterns
- **Integration Problems**: Verify API connectivity and authentication

### **Healthcare Compliance**
- **HIPAA Questions**: Review audit logging and data encryption
- **Medical Safety**: Verify crisis detection and safety measures
- **Professional Oversight**: Ensure proper medical disclaimers

---

**Sage's AI model configuration provides enterprise-grade healthcare AI with intelligent routing, comprehensive safety measures, and optimal performance across all medical specialties!** 🏥🤖