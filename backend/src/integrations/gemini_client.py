"""
Google Gemini API integration for comprehensive healthcare AI support.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Configuration fallback
try:
    from config.settings import settings
except ImportError:
    import os
    class FallbackSettings:
        def __init__(self):
            self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
            self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-pro')
    settings = FallbackSettings()
from ..models.core import AgentResponse, ProcessingContext

logger = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini API client for healthcare AI responses."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to settings)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package is required for Gemini integration")
        
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model_name = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_TOKENS
        
        # Safety settings for healthcare
        self.safety_settings = self._get_safety_settings()
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.safety_settings
        )
        
        logger.info(f"Gemini client initialized with model: {self.model_name}")
    
    def _get_safety_settings(self) -> Dict[HarmCategory, HarmBlockThreshold]:
        """Get safety settings for healthcare use."""
        safety_level = settings.GEMINI_SAFETY_SETTINGS.lower()
        
        if safety_level == "high":
            threshold = HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
        elif safety_level == "medium":
            threshold = HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        elif safety_level == "low":
            threshold = HarmBlockThreshold.BLOCK_ONLY_HIGH
        else:
            threshold = HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        
        return {
            HarmCategory.HARM_CATEGORY_HARASSMENT: threshold,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: threshold,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: threshold,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    async def generate_healthcare_response(
        self,
        context: ProcessingContext,
        system_prompt: str,
        user_query: str,
        medical_context: Optional[str] = None,
        citations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate healthcare response using Gemini.
        
        Args:
            context: Processing context
            system_prompt: System prompt for healthcare guidance
            user_query: User's medical query
            medical_context: Additional medical context from RAG
            citations: Medical citations for reference
            
        Returns:
            Generated response with metadata
        """
        try:
            # Build comprehensive prompt
            full_prompt = self._build_healthcare_prompt(
                system_prompt=system_prompt,
                user_query=user_query,
                medical_context=medical_context,
                citations=citations,
                context=context
            )
            
            # Generate response
            response = await self._generate_response(full_prompt)
            
            # Process and validate response
            processed_response = self._process_healthcare_response(response)
            
            return {
                "content": processed_response["content"],
                "reasoning_steps": processed_response["reasoning_steps"],
                "confidence_level": processed_response["confidence_level"],
                "medical_disclaimer": processed_response["medical_disclaimer"],
                "citations_used": processed_response["citations_used"],
                "safety_flags": processed_response["safety_flags"],
                "model_metadata": {
                    "model": self.model_name,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "safety_settings": settings.GEMINI_SAFETY_SETTINGS,
                    "generation_time": processed_response["generation_time"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating Gemini healthcare response: {e}")
            return {
                "content": "I apologize, but I'm unable to process your healthcare query at the moment. Please consult with a healthcare professional for medical advice.",
                "reasoning_steps": [f"Error occurred: {str(e)}"],
                "confidence_level": 0.0,
                "medical_disclaimer": "This system cannot replace professional medical consultation.",
                "citations_used": [],
                "safety_flags": ["generation_error"],
                "model_metadata": {
                    "model": self.model_name,
                    "error": str(e)
                }
            }
    
    def _build_healthcare_prompt(
        self,
        system_prompt: str,
        user_query: str,
        medical_context: Optional[str] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        context: Optional[ProcessingContext] = None
    ) -> str:
        """Build comprehensive healthcare prompt for Gemini."""
        
        prompt_parts = []
        
        # System prompt with healthcare focus
        prompt_parts.append(f"""
{system_prompt}

CRITICAL HEALTHCARE GUIDELINES:
- You are Sage, a comprehensive healthcare AI assistant
- Provide evidence-based medical information across ALL healthcare specialties
- Always include proper medical disclaimers
- Cite authoritative medical sources when available
- Indicate confidence levels and uncertainty
- Recommend professional medical consultation when appropriate
- Follow medical ethics and safety protocols
""")
        
        # Add medical context from RAG if available
        if medical_context:
            prompt_parts.append(f"""
MEDICAL KNOWLEDGE BASE CONTEXT:
{medical_context}
""")
        
        # Add citations if available
        if citations:
            citations_text = "\n".join([
                f"- {cite.get('title', 'Unknown')} ({cite.get('source', 'Unknown source')})"
                for cite in citations[:5]  # Limit to top 5 citations
            ])
            prompt_parts.append(f"""
AUTHORITATIVE MEDICAL SOURCES:
{citations_text}
""")
        
        # Add user context if available
        if context and context.user_context:
            prompt_parts.append(f"""
USER CONTEXT:
- Previous interactions: {len(context.user_context.conversation_history) if context.user_context.conversation_history else 0}
- Medical interests: {', '.join(context.user_context.medical_interests) if context.user_context.medical_interests else 'General healthcare'}
""")
        
        # Add the user query
        prompt_parts.append(f"""
USER HEALTHCARE QUERY:
{user_query}

RESPONSE REQUIREMENTS:
1. Provide comprehensive, evidence-based medical information
2. Include confidence level (0.0-1.0)
3. Add appropriate medical disclaimers
4. Cite sources when available
5. Use clear, professional medical language
6. Structure response with reasoning steps
7. Recommend professional consultation when needed

Please provide a helpful, accurate, and safe healthcare response.
""")
        
        return "\n\n".join(prompt_parts)
    
    async def _generate_response(self, prompt: str) -> Any:
        """Generate response from Gemini model."""
        try:
            # Use async generation if available, otherwise use sync
            if hasattr(self.model, 'generate_content_async'):
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                    )
                )
            else:
                # Fallback to sync generation in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=self.temperature,
                            max_output_tokens=self.max_tokens,
                        )
                    )
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise
    
    def _process_healthcare_response(self, response: Any) -> Dict[str, Any]:
        """Process Gemini response for healthcare use."""
        start_time = datetime.utcnow()
        
        try:
            # Extract text content
            if hasattr(response, 'text'):
                content = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                content = response.candidates[0].content.parts[0].text
            else:
                content = str(response)
            
            # Check for safety flags
            safety_flags = []
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'safety_ratings'):
                    for rating in candidate.safety_ratings:
                        if rating.probability.name != "NEGLIGIBLE":
                            safety_flags.append(f"{rating.category.name}: {rating.probability.name}")
            
            # Extract reasoning steps (look for structured thinking)
            reasoning_steps = self._extract_reasoning_steps(content)
            
            # Determine confidence level
            confidence_level = self._calculate_confidence_level(content, safety_flags)
            
            # Ensure medical disclaimer
            medical_disclaimer = self._ensure_medical_disclaimer(content)
            
            # Extract citations used
            citations_used = self._extract_citations_used(content)
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "content": content,
                "reasoning_steps": reasoning_steps,
                "confidence_level": confidence_level,
                "medical_disclaimer": medical_disclaimer,
                "citations_used": citations_used,
                "safety_flags": safety_flags,
                "generation_time": generation_time
            }
            
        except Exception as e:
            logger.error(f"Error processing Gemini response: {e}")
            return {
                "content": "I apologize, but I encountered an error processing the medical information. Please consult with a healthcare professional.",
                "reasoning_steps": [f"Processing error: {str(e)}"],
                "confidence_level": 0.0,
                "medical_disclaimer": "This system cannot replace professional medical consultation.",
                "citations_used": [],
                "safety_flags": ["processing_error"],
                "generation_time": 0.0
            }
    
    def _extract_reasoning_steps(self, content: str) -> List[str]:
        """Extract reasoning steps from response content."""
        reasoning_steps = []
        
        # Look for numbered steps, bullet points, or structured thinking
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                line.startswith(('•', '-', '*')) or
                'step' in line.lower() or
                'first' in line.lower() or
                'second' in line.lower() or
                'analysis' in line.lower()):
                if len(line) > 10:  # Avoid very short lines
                    reasoning_steps.append(line)
        
        # If no structured steps found, create basic reasoning
        if not reasoning_steps:
            reasoning_steps = [
                "Analyzed healthcare query for medical context",
                "Reviewed available medical knowledge and evidence",
                "Formulated evidence-based response with appropriate disclaimers"
            ]
        
        return reasoning_steps[:5]  # Limit to 5 steps
    
    def _calculate_confidence_level(self, content: str, safety_flags: List[str]) -> float:
        """Calculate confidence level based on content and safety."""
        base_confidence = 0.8  # Start with high confidence for Gemini
        
        # Reduce confidence for safety flags
        if safety_flags:
            base_confidence -= 0.2
        
        # Increase confidence for medical terms and structured responses
        medical_indicators = [
            'evidence', 'study', 'research', 'clinical', 'medical',
            'treatment', 'diagnosis', 'symptoms', 'healthcare'
        ]
        
        medical_score = sum(1 for term in medical_indicators if term.lower() in content.lower())
        confidence_boost = min(0.2, medical_score * 0.02)
        
        # Check for uncertainty indicators
        uncertainty_indicators = [
            'may', 'might', 'could', 'possibly', 'uncertain',
            'consult', 'see a doctor', 'medical professional'
        ]
        
        uncertainty_score = sum(1 for term in uncertainty_indicators if term.lower() in content.lower())
        confidence_reduction = min(0.3, uncertainty_score * 0.05)
        
        final_confidence = base_confidence + confidence_boost - confidence_reduction
        return max(0.1, min(1.0, final_confidence))
    
    def _ensure_medical_disclaimer(self, content: str) -> str:
        """Ensure appropriate medical disclaimer is present."""
        disclaimer_keywords = [
            'disclaimer', 'not replace', 'consult', 'medical professional',
            'healthcare provider', 'doctor'
        ]
        
        has_disclaimer = any(keyword in content.lower() for keyword in disclaimer_keywords)
        
        if not has_disclaimer:
            return "This information is for educational purposes only and does not replace professional medical advice. Please consult with a healthcare provider for personalized medical guidance."
        
        return "Medical disclaimer included in response."
    
    def _extract_citations_used(self, content: str) -> List[str]:
        """Extract citations mentioned in the response."""
        citations = []
        
        # Look for common citation patterns
        citation_patterns = [
            'according to', 'research shows', 'studies indicate',
            'WHO', 'CDC', 'NIH', 'PubMed', 'journal', 'study'
        ]
        
        for pattern in citation_patterns:
            if pattern.lower() in content.lower():
                citations.append(f"Referenced: {pattern}")
        
        return citations[:3]  # Limit to 3 citations
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Gemini API connection."""
        try:
            test_prompt = "Hello, this is a test of the healthcare AI system. Please respond with a brief acknowledgment."
            response = await self._generate_response(test_prompt)
            
            return {
                "status": "success",
                "model": self.model_name,
                "response_preview": str(response)[:100] + "..." if len(str(response)) > 100 else str(response),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model": self.model_name,
                "timestamp": datetime.utcnow().isoformat()
            }


# Factory function for creating Gemini client
def create_gemini_client(api_key: Optional[str] = None) -> Optional[GeminiClient]:
    """
    Create Gemini client with error handling.
    
    Args:
        api_key: Optional API key override
        
    Returns:
        GeminiClient instance or None if unavailable
    """
    try:
        if not GEMINI_AVAILABLE:
            logger.warning("Gemini integration not available - google-generativeai package not installed")
            return None
        
        return GeminiClient(api_key)
        
    except Exception as e:
        logger.error(f"Failed to create Gemini client: {e}")
        return None