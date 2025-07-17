"""
Chain-of-Thought LLM Engine for structured reasoning and response generation.
Supports both OpenAI and Google Gemini models with intelligent routing.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

# Configuration fallback
try:
    from config.settings import settings
except ImportError:
    import os
    class FallbackSettings:
        def __init__(self):
            self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
            self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            self.openai_temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
            self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
            self.anthropic_model = os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
    settings = FallbackSettings()
from ..integrations.gemini_client import create_gemini_client, GeminiClient
from ..models.core import (
    UserInput, AnalyzedInput, RAGResults, AgentResponse,
    ProcessingContext, Citation, MedicalImage
)

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Available LLM models for different complexity levels."""
    # OpenAI Models
    OPENAI_SIMPLE = "gpt-3.5-turbo"
    OPENAI_COMPLEX = "gpt-4"
    OPENAI_ADVANCED = "gpt-4-turbo"
    OPENAI_HEALTHCARE = "gpt-4o-mini"  # GPT-4o-mini for healthcare applications
    
    # Gemini Models
    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH = "gemini-1.5-flash"
    
    # Default routing
    HEALTHCARE_DEFAULT = "gemini"  # Default to Gemini for comprehensive healthcare


class ReasoningStep:
    """Represents a single step in chain-of-thought reasoning."""
    
    def __init__(
        self,
        step_number: int,
        description: str,
        reasoning: str,
        confidence: float,
        evidence: List[str] = None
    ):
        self.step_number = step_number
        self.description = description
        self.reasoning = reasoning
        self.confidence = confidence
        self.evidence = evidence or []
        self.timestamp = datetime.utcnow()


class ChainOfThoughtEngine:
    """Chain-of-thought reasoning engine for comprehensive healthcare consultations."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        default_model: ModelType = ModelType.HEALTHCARE_DEFAULT,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        """
        Initialize Chain-of-Thought engine with multi-model support.
        
        Args:
            openai_api_key: OpenAI API key
            gemini_api_key: Gemini API key
            default_model: Default model to use
            temperature: Model temperature for creativity
            max_tokens: Maximum tokens in response
        """
        self.default_model = default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize OpenAI client
        self.openai_client = None
        if OPENAI_AVAILABLE:
            self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY
            if self.openai_api_key:
                openai.api_key = self.openai_api_key
                self.openai_client = openai
                logger.info("OpenAI client initialized")
        
        # Initialize Gemini client
        self.gemini_client = None
        try:
            self.gemini_client = create_gemini_client(gemini_api_key)
            if self.gemini_client:
                logger.info("Gemini client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")
        
        # Check if at least one model is available
        if not self.openai_client and not self.gemini_client:
            raise ValueError("At least one AI model (OpenAI or Gemini) must be available")
        
        # Model routing configuration
        self.model_routing_enabled = settings.MODEL_ROUTING_ENABLED
        self.complexity_thresholds = {
            "simple": 0.3,    # Simple queries
            "complex": 0.7,   # Complex queries
            "critical": 0.9   # Critical queries
        }
        
        logger.info(f"Chain-of-Thought engine initialized with routing: {self.model_routing_enabled}")
    
    def _assess_query_complexity(self, context: ProcessingContext) -> str:
        """
        Assess the complexity of the user query.
        
        Args:
            context: Processing context with user input and analysis
            
        Returns:
            Complexity level: 'simple', 'complex', or 'critical'
        """
        # Check urgency level
        if context.analyzed_input and context.analyzed_input.urgency_level >= 8:
            return "critical"
        
        # Check for complex medical terms or multiple conditions
        if context.analyzed_input:
            medical_entities = context.analyzed_input.medical_entities
            if len(medical_entities) > 3:
                return "complex"
            
            # Check for crisis-related keywords
            crisis_keywords = ["suicide", "self-harm", "emergency", "crisis", "urgent"]
            text_lower = context.analyzed_input.text.lower()
            if any(keyword in text_lower for keyword in crisis_keywords):
                return "critical"
        
        # Check RAG results complexity
        if context.rag_results and len(context.rag_results.documents) > 5:
            return "complex"
        
        # Default to simple for basic queries
        return "simple"
    
    def _select_model(self, complexity: str) -> Tuple[str, str]:
        """
        Select appropriate model based on query complexity and availability.
        
        Args:
            complexity: Query complexity level
            
        Returns:
            Tuple of (model_provider, model_name)
        """
        # Default healthcare model preference
        default_model = settings.DEFAULT_HEALTHCARE_MODEL.lower()
        
        # Model selection based on complexity and availability
        if complexity == "critical":
            # For critical queries, prefer most capable models
            if default_model == "gemini" and self.gemini_client:
                return ("gemini", ModelType.GEMINI_PRO.value)
            elif self.openai_client:
                return ("openai", ModelType.OPENAI_ADVANCED.value)
            elif self.gemini_client:
                return ("gemini", ModelType.GEMINI_PRO.value)
        
        elif complexity == "complex":
            # For complex queries, use balanced models
            if default_model == "gemini" and self.gemini_client:
                return ("gemini", ModelType.GEMINI_PRO.value)
            elif self.openai_client:
                return ("openai", ModelType.OPENAI_HEALTHCARE.value)
            elif self.gemini_client:
                return ("gemini", ModelType.GEMINI_PRO.value)
        
        else:  # simple queries
            # For simple queries, use efficient models
            if default_model == "gemini" and self.gemini_client:
                return ("gemini", ModelType.GEMINI_PRO.value)  # Gemini Pro for all healthcare
            elif self.openai_client:
                return ("openai", ModelType.OPENAI_HEALTHCARE.value)
            elif self.gemini_client:
                return ("gemini", ModelType.GEMINI_PRO.value)
        
        # Fallback to any available model
        if self.gemini_client:
            return ("gemini", ModelType.GEMINI_PRO.value)
        elif self.openai_client:
            return ("openai", ModelType.OPENAI_HEALTHCARE.value)
        
        raise ValueError("No AI models available")
    
    def _build_system_prompt(self, context: ProcessingContext) -> str:
        """
        Build system prompt for the LLM.
        
        Args:
            context: Processing context
            
        Returns:
            System prompt string
        """
        base_prompt = """You are a professional mental health AI assistant with expertise in psychology and psychiatry. Your role is to provide empathetic, evidence-based support while maintaining appropriate boundaries.

CRITICAL SAFETY GUIDELINES:
1. Always include medical disclaimers
2. Encourage professional consultation for serious concerns
3. Provide crisis resources for emergency situations
4. Never diagnose or prescribe medications
5. Maintain empathetic and professional tone

REASONING APPROACH:
Use chain-of-thought reasoning to:
1. Analyze the user's concern
2. Consider relevant medical knowledge
3. Evaluate evidence and confidence levels
4. Formulate appropriate response
5. Include safety considerations

RESPONSE FORMAT:
Provide structured reasoning followed by a clear, empathetic response."""
        
        # Add context-specific instructions
        if context.analyzed_input:
            if context.analyzed_input.urgency_level >= 8:
                base_prompt += "\n\nURGENT: This appears to be a high-urgency situation. Prioritize safety and crisis resources."
            
            if "crisis" in context.analyzed_input.intent:
                base_prompt += "\n\nCRISIS DETECTED: Provide immediate crisis resources and encourage professional help."
        
        return base_prompt
    
    def _build_user_prompt(self, context: ProcessingContext) -> str:
        """
        Build user prompt with context information.
        
        Args:
            context: Processing context
            
        Returns:
            User prompt string
        """
        prompt_parts = []
        
        # User query
        prompt_parts.append(f"User Query: {context.user_input.content}")
        
        # Analysis results
        if context.analyzed_input:
            prompt_parts.append(f"Intent: {context.analyzed_input.intent}")
            prompt_parts.append(f"Urgency Level: {context.analyzed_input.urgency_level}/10")
            if context.analyzed_input.medical_entities:
                prompt_parts.append(f"Medical Entities: {', '.join(context.analyzed_input.medical_entities)}")
            if context.analyzed_input.emotional_context:
                prompt_parts.append(f"Emotional Context: {context.analyzed_input.emotional_context}")
        
        # RAG results
        if context.rag_results and context.rag_results.documents:
            prompt_parts.append("\nRelevant Medical Information:")
            for i, doc in enumerate(context.rag_results.documents[:3], 1):
                prompt_parts.append(f"{i}. {doc.content[:300]}...")
        
        # Citations
        if context.rag_results and context.rag_results.citations:
            prompt_parts.append("\nScientific Sources:")
            for i, citation in enumerate(context.rag_results.citations[:3], 1):
                prompt_parts.append(f"{i}. {citation.title} - {citation.source}")
        
        # User context
        if context.user_context and context.user_context.compressed_history:
            prompt_parts.append(f"\nConversation History: {context.user_context.compressed_history}")
        
        prompt_parts.append("\nPlease provide a structured chain-of-thought analysis followed by an empathetic, helpful response.")
        
        return "\n".join(prompt_parts)
    
    async def generate_response(self, context: ProcessingContext) -> Tuple[AgentResponse, List[ReasoningStep]]:
        """
        Generate response using chain-of-thought reasoning with multi-model support.
        
        Args:
            context: Processing context with all available information
            
        Returns:
            Tuple of (AgentResponse, reasoning steps)
        """
        try:
            # Assess complexity and select model
            complexity = self._assess_query_complexity(context)
            model_provider, model_name = self._select_model(complexity)
            
            logger.info(f"Using {model_provider}:{model_name} for {complexity} query")
            
            # Build prompts
            system_prompt = self._build_comprehensive_healthcare_prompt(context)
            user_prompt = self._build_user_prompt(context)
            
            # Generate response based on selected model
            if model_provider == "gemini" and self.gemini_client:
                response_data = await self._generate_gemini_response(
                    context, system_prompt, user_prompt, model_name
                )
            elif model_provider == "openai" and self.openai_client:
                response_data = await self._generate_openai_response(
                    system_prompt, user_prompt, model_name
                )
            else:
                raise ValueError(f"Model provider {model_provider} not available")
            
            # Parse response
            reasoning_steps, final_response = self._parse_response(response_data["content"])
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(reasoning_steps, context)
            
            # Create agent response
            agent_response = AgentResponse(
                content=final_response,
                citations=context.rag_results.citations if context.rag_results else [],
                medical_images=context.medical_images,
                reasoning_steps=[step.reasoning for step in reasoning_steps],
                confidence_level=overall_confidence,
                safety_warnings=self._extract_safety_warnings(final_response),
                medical_disclaimer=self._get_comprehensive_medical_disclaimer(),
                response_metadata={
                    "model_provider": model_provider,
                    "model_used": model_name,
                    "complexity": complexity,
                    "temperature": self.temperature,
                    "reasoning_steps_count": len(reasoning_steps),
                    "timestamp": datetime.utcnow().isoformat(),
                    **response_data.get("model_metadata", {})
                }
            )
            
            return agent_response, reasoning_steps
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            
            # Return error response
            error_response = AgentResponse(
                content="I apologize, but I'm experiencing technical difficulties. Please try again or contact a healthcare professional if you need immediate assistance.",
                citations=[],
                medical_images=[],
                reasoning_steps=["Error occurred during response generation"],
                confidence_level=0.0,
                safety_warnings=["Technical error occurred"],
                medical_disclaimer=self._get_comprehensive_medical_disclaimer(),
                response_metadata={"error": str(e)}
            )
            
            return error_response, []
    
    def _parse_response(self, response_content: str) -> Tuple[List[ReasoningStep], str]:
        """
        Parse LLM response to extract reasoning steps and final response.
        
        Args:
            response_content: Raw LLM response
            
        Returns:
            Tuple of (reasoning steps, final response)
        """
        reasoning_steps = []
        final_response = response_content
        
        # Try to extract structured reasoning
        lines = response_content.split('\n')
        current_step = None
        step_number = 1
        
        for line in lines:
            line = line.strip()
            
            # Look for reasoning step indicators
            if any(indicator in line.lower() for indicator in ['step', 'analysis', 'reasoning', 'consideration']):
                if current_step:
                    reasoning_steps.append(current_step)
                
                current_step = ReasoningStep(
                    step_number=step_number,
                    description=line,
                    reasoning=line,
                    confidence=0.8  # Default confidence
                )
                step_number += 1
            elif current_step and line:
                current_step.reasoning += f" {line}"
        
        if current_step:
            reasoning_steps.append(current_step)
        
        # If no structured reasoning found, create a single step
        if not reasoning_steps:
            reasoning_steps.append(ReasoningStep(
                step_number=1,
                description="Response generation",
                reasoning="Generated response based on available context and medical knowledge",
                confidence=0.7
            ))
        
        return reasoning_steps, final_response
    
    def _calculate_overall_confidence(
        self,
        reasoning_steps: List[ReasoningStep],
        context: ProcessingContext
    ) -> float:
        """
        Calculate overall confidence based on reasoning steps and context.
        
        Args:
            reasoning_steps: List of reasoning steps
            context: Processing context
            
        Returns:
            Overall confidence score (0-1)
        """
        if not reasoning_steps:
            return 0.5
        
        # Average confidence from reasoning steps
        step_confidence = sum(step.confidence for step in reasoning_steps) / len(reasoning_steps)
        
        # Factor in RAG results confidence
        rag_confidence = 0.5
        if context.rag_results and context.rag_results.confidence_scores:
            rag_confidence = sum(context.rag_results.confidence_scores) / len(context.rag_results.confidence_scores)
        
        # Factor in analysis confidence
        analysis_confidence = 0.5
        if context.analyzed_input:
            analysis_confidence = context.analyzed_input.confidence
        
        # Weighted combination
        overall_confidence = (
            step_confidence * 0.5 +
            rag_confidence * 0.3 +
            analysis_confidence * 0.2
        )
        
        return min(1.0, max(0.0, overall_confidence))
    
    def _extract_safety_warnings(self, response: str) -> List[str]:
        """Extract safety warnings from response."""
        warnings = []
        
        warning_indicators = [
            "seek immediate help",
            "emergency",
            "crisis",
            "professional help",
            "consult a doctor",
            "medical attention"
        ]
        
        response_lower = response.lower()
        for indicator in warning_indicators:
            if indicator in response_lower:
                warnings.append(f"Response contains guidance to {indicator}")
        
        return warnings
    
    def _get_medical_disclaimer(self) -> str:
        """Get standard medical disclaimer."""
        return (
            "This AI assistant provides general mental health information and support. "
            "It is not a substitute for professional medical advice, diagnosis, or treatment. "
            "Always seek the advice of qualified mental health professionals with any questions "
            "you may have regarding a medical condition. If you are experiencing a mental health "
            "emergency, please contact emergency services or a crisis hotline immediately."
        )
    
    def _get_comprehensive_medical_disclaimer(self) -> str:
        """Get comprehensive medical disclaimer for healthcare system."""
        return (
            "This AI system provides general healthcare information for educational purposes only. "
            "It is not a substitute for professional medical advice, diagnosis, or treatment. "
            "Always seek the advice of qualified healthcare professionals with any questions "
            "you may have regarding a medical condition. Never disregard professional medical advice "
            "or delay seeking treatment because of information provided by this AI system. "
            "If you are experiencing a medical emergency, please contact emergency services immediately."
        )
    
    def _build_comprehensive_healthcare_prompt(self, context: ProcessingContext) -> str:
        """
        Build comprehensive healthcare system prompt for multi-model support.
        
        Args:
            context: Processing context
            
        Returns:
            Comprehensive healthcare system prompt
        """
        base_prompt = """You are Sage, a comprehensive healthcare AI assistant with expertise across all medical specialties. Your role is to provide evidence-based medical information and support while maintaining the highest standards of medical safety and ethics.

COMPREHENSIVE HEALTHCARE SCOPE:
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
- And all other medical specialties

CRITICAL SAFETY GUIDELINES:
1. Always include comprehensive medical disclaimers
2. Encourage professional consultation for all medical concerns
3. Provide crisis resources for emergency situations
4. Never diagnose or prescribe medications
5. Maintain professional, empathetic tone
6. Cite authoritative medical sources when available
7. Indicate confidence levels and uncertainty
8. Follow medical ethics and safety protocols

REASONING APPROACH:
Use structured chain-of-thought reasoning to:
1. Analyze the healthcare query comprehensively
2. Consider relevant medical knowledge across specialties
3. Evaluate evidence quality and confidence levels
4. Cross-reference with authoritative medical sources
5. Formulate evidence-based response
6. Include appropriate safety considerations and disclaimers

RESPONSE REQUIREMENTS:
- Provide comprehensive, evidence-based medical information
- Include confidence level assessment
- Add appropriate medical disclaimers
- Cite authoritative sources when available
- Use clear, professional medical language
- Structure response with reasoning steps
- Recommend professional consultation when needed"""
        
        # Add context-specific instructions
        if context.analyzed_input:
            if context.analyzed_input.urgency_level >= 8:
                base_prompt += "\n\nURGENT: This appears to be a high-urgency medical situation. Prioritize safety and emergency resources."
            
            if "crisis" in context.analyzed_input.intent:
                base_prompt += "\n\nCRISIS DETECTED: Provide immediate crisis resources and encourage professional medical help."
            
            # Add specialty-specific guidance based on medical entities
            if context.analyzed_input.medical_entities:
                specialties = self._map_entities_to_specialties(context.analyzed_input.medical_entities)
                if specialties:
                    base_prompt += f"\n\nMEDICAL SPECIALTIES INVOLVED: {', '.join(specialties)}"
        
        return base_prompt
    
    def _map_entities_to_specialties(self, medical_entities: List[str]) -> List[str]:
        """Map medical entities to relevant specialties."""
        specialty_mapping = {
            # Cardiology
            "heart": "Cardiology", "cardiac": "Cardiology", "cardiovascular": "Cardiology",
            "hypertension": "Cardiology", "blood pressure": "Cardiology",
            
            # Endocrinology
            "diabetes": "Endocrinology", "thyroid": "Endocrinology", "hormone": "Endocrinology",
            "insulin": "Endocrinology", "glucose": "Endocrinology",
            
            # Oncology
            "cancer": "Oncology", "tumor": "Oncology", "chemotherapy": "Oncology",
            "radiation": "Oncology", "malignant": "Oncology",
            
            # Pediatrics
            "child": "Pediatrics", "pediatric": "Pediatrics", "infant": "Pediatrics",
            "vaccination": "Pediatrics", "growth": "Pediatrics",
            
            # Mental Health
            "depression": "Psychiatry", "anxiety": "Psychiatry", "mental": "Psychiatry",
            "psychiatric": "Psychiatry", "therapy": "Psychiatry",
            
            # Emergency Medicine
            "emergency": "Emergency Medicine", "urgent": "Emergency Medicine", 
            "trauma": "Emergency Medicine", "critical": "Emergency Medicine"
        }
        
        specialties = set()
        for entity in medical_entities:
            entity_lower = entity.lower()
            for keyword, specialty in specialty_mapping.items():
                if keyword in entity_lower:
                    specialties.add(specialty)
        
        return list(specialties)
    
    async def _generate_gemini_response(
        self,
        context: ProcessingContext,
        system_prompt: str,
        user_prompt: str,
        model_name: str
    ) -> Dict[str, Any]:
        """Generate response using Gemini model."""
        if not self.gemini_client:
            raise ValueError("Gemini client not available")
        
        # Build medical context from RAG results
        medical_context = None
        if context.rag_results and context.rag_results.documents:
            medical_context = "\n\n".join([
                f"Source: {doc.source}\nContent: {doc.content[:500]}..."
                for doc in context.rag_results.documents[:3]
            ])
        
        # Prepare citations
        citations = []
        if context.rag_results and context.rag_results.citations:
            citations = [
                {
                    "title": cite.title,
                    "source": cite.source,
                    "url": cite.url,
                    "authors": cite.authors
                }
                for cite in context.rag_results.citations[:5]
            ]
        
        # Generate response using Gemini
        response_data = await self.gemini_client.generate_healthcare_response(
            context=context,
            system_prompt=system_prompt,
            user_query=user_prompt,
            medical_context=medical_context,
            citations=citations
        )
        
        return response_data
    
    async def _generate_openai_response(
        self,
        system_prompt: str,
        user_prompt: str,
        model_name: str
    ) -> Dict[str, Any]:
        """Generate response using OpenAI model."""
        if not self.openai_client:
            raise ValueError("OpenAI client not available")
        
        try:
            # Call OpenAI API
            response = await self.openai_client.ChatCompletion.acreate(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            response_content = response.choices[0].message.content
            
            return {
                "content": response_content,
                "model_metadata": {
                    "model": model_name,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "usage": response.usage.dict() if hasattr(response, 'usage') else {}
                }
            }
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise
    
    async def estimate_cost(self, context: ProcessingContext) -> Dict[str, Any]:
        """
        Estimate the cost of processing this request.
        
        Args:
            context: Processing context
            
        Returns:
            Cost estimation details
        """
        complexity = self._assess_query_complexity(context)
        model = self._select_model(complexity)
        
        # Rough token estimation
        input_tokens = len(self._build_user_prompt(context).split()) * 1.3  # Rough estimation
        output_tokens = self.max_tokens
        
        # Cost per 1K tokens (approximate)
        costs = {
            ModelType.SIMPLE: {"input": 0.0015, "output": 0.002},
            ModelType.COMPLEX: {"input": 0.03, "output": 0.06},
            ModelType.ADVANCED: {"input": 0.01, "output": 0.03}
        }
        
        model_costs = costs[model]
        estimated_cost = (
            (input_tokens / 1000) * model_costs["input"] +
            (output_tokens / 1000) * model_costs["output"]
        )
        
        return {
            "model": model.value,
            "complexity": complexity,
            "estimated_input_tokens": int(input_tokens),
            "estimated_output_tokens": output_tokens,
            "estimated_cost_usd": round(estimated_cost, 4)
        }
