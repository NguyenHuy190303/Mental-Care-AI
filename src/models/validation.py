"""
Data validation and serialization utilities.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import ValidationError
import json

from .core import (
    UserInput, AnalyzedInput, RAGResults, Citation, 
    AgentResponse, MedicalImage, UserContext, ProcessingContext
)
from .database import (
    UserCreate, UserResponse, ConversationCreate, ConversationResponse,
    UsageMetricCreate, UsageMetricResponse, FeedbackCreate, FeedbackResponse
)

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates and serializes data models."""
    
    @staticmethod
    def validate_user_input(data: Dict[str, Any]) -> UserInput:
        """
        Validate and create UserInput model.
        
        Args:
            data: Raw input data
            
        Returns:
            Validated UserInput instance
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            return UserInput(**data)
        except ValidationError as e:
            logger.error(f"UserInput validation failed: {e}")
            raise
    
    @staticmethod
    def validate_analyzed_input(data: Dict[str, Any]) -> AnalyzedInput:
        """
        Validate and create AnalyzedInput model.
        
        Args:
            data: Raw analyzed input data
            
        Returns:
            Validated AnalyzedInput instance
        """
        try:
            return AnalyzedInput(**data)
        except ValidationError as e:
            logger.error(f"AnalyzedInput validation failed: {e}")
            raise
    
    @staticmethod
    def validate_rag_results(data: Dict[str, Any]) -> RAGResults:
        """
        Validate and create RAGResults model.
        
        Args:
            data: Raw RAG results data
            
        Returns:
            Validated RAGResults instance
        """
        try:
            return RAGResults(**data)
        except ValidationError as e:
            logger.error(f"RAGResults validation failed: {e}")
            raise
    
    @staticmethod
    def validate_citation(data: Dict[str, Any]) -> Citation:
        """
        Validate and create Citation model.
        
        Args:
            data: Raw citation data
            
        Returns:
            Validated Citation instance
        """
        try:
            return Citation(**data)
        except ValidationError as e:
            logger.error(f"Citation validation failed: {e}")
            raise
    
    @staticmethod
    def validate_agent_response(data: Dict[str, Any]) -> AgentResponse:
        """
        Validate and create AgentResponse model.
        
        Args:
            data: Raw agent response data
            
        Returns:
            Validated AgentResponse instance
        """
        try:
            return AgentResponse(**data)
        except ValidationError as e:
            logger.error(f"AgentResponse validation failed: {e}")
            raise
    
    @staticmethod
    def validate_medical_image(data: Dict[str, Any]) -> MedicalImage:
        """
        Validate and create MedicalImage model.
        
        Args:
            data: Raw medical image data
            
        Returns:
            Validated MedicalImage instance
        """
        try:
            return MedicalImage(**data)
        except ValidationError as e:
            logger.error(f"MedicalImage validation failed: {e}")
            raise
    
    @staticmethod
    def validate_user_context(data: Dict[str, Any]) -> UserContext:
        """
        Validate and create UserContext model.
        
        Args:
            data: Raw user context data
            
        Returns:
            Validated UserContext instance
        """
        try:
            return UserContext(**data)
        except ValidationError as e:
            logger.error(f"UserContext validation failed: {e}")
            raise
    
    @staticmethod
    def validate_processing_context(data: Dict[str, Any]) -> ProcessingContext:
        """
        Validate and create ProcessingContext model.
        
        Args:
            data: Raw processing context data
            
        Returns:
            Validated ProcessingContext instance
        """
        try:
            return ProcessingContext(**data)
        except ValidationError as e:
            logger.error(f"ProcessingContext validation failed: {e}")
            raise


class DataSerializer:
    """Serializes data models to various formats."""
    
    @staticmethod
    def to_dict(model: Union[UserInput, AnalyzedInput, RAGResults, Citation, AgentResponse]) -> Dict[str, Any]:
        """
        Convert Pydantic model to dictionary.
        
        Args:
            model: Pydantic model instance
            
        Returns:
            Dictionary representation
        """
        return model.dict()
    
    @staticmethod
    def to_json(model: Union[UserInput, AnalyzedInput, RAGResults, Citation, AgentResponse]) -> str:
        """
        Convert Pydantic model to JSON string.
        
        Args:
            model: Pydantic model instance
            
        Returns:
            JSON string representation
        """
        return model.json()
    
    @staticmethod
    def from_json(json_str: str, model_class) -> Any:
        """
        Create Pydantic model from JSON string.
        
        Args:
            json_str: JSON string
            model_class: Pydantic model class
            
        Returns:
            Model instance
        """
        try:
            return model_class.parse_raw(json_str)
        except ValidationError as e:
            logger.error(f"JSON deserialization failed for {model_class.__name__}: {e}")
            raise
    
    @staticmethod
    def sanitize_for_storage(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize data for database storage.
        
        Args:
            data: Raw data dictionary
            
        Returns:
            Sanitized data dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, datetime):
                sanitized[key] = value.isoformat()
            elif isinstance(value, (list, dict)):
                sanitized[key] = json.dumps(value, default=str)
            elif value is None:
                sanitized[key] = None
            else:
                sanitized[key] = str(value)
        
        return sanitized
    
    @staticmethod
    def prepare_for_chromadb(
        content: str,
        metadata: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Prepare data for ChromaDB storage.
        
        Args:
            content: Document content
            metadata: Document metadata
            
        Returns:
            Tuple of (content, sanitized_metadata)
        """
        # ChromaDB metadata must be simple types
        sanitized_metadata = {}
        
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                sanitized_metadata[key] = value
            elif isinstance(value, datetime):
                sanitized_metadata[key] = value.isoformat()
            elif isinstance(value, list):
                # Convert list to comma-separated string
                sanitized_metadata[key] = ",".join(str(item) for item in value)
            else:
                sanitized_metadata[key] = str(value)
        
        return content, sanitized_metadata


class ValidationUtils:
    """Utility functions for data validation."""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email format is valid."""
        import re
        pattern = r'^[^@]+@[^@]+\.[^@]+$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL format is valid."""
        return url.startswith(('http://', 'https://'))
    
    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input.
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            text = str(text)
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Trim whitespace
        text = text.strip()
        
        # Truncate if necessary
        if max_length and len(text) > max_length:
            text = text[:max_length].rstrip()
        
        return text
    
    @staticmethod
    def validate_confidence_score(score: float) -> bool:
        """Check if confidence score is valid (0.0 to 1.0)."""
        return isinstance(score, (int, float)) and 0.0 <= score <= 1.0
    
    @staticmethod
    def validate_urgency_level(level: int) -> bool:
        """Check if urgency level is valid (1 to 10)."""
        return isinstance(level, int) and 1 <= level <= 10
    
    @staticmethod
    def extract_medical_entities(text: str) -> List[str]:
        """
        Extract medical entities from text (placeholder implementation).
        
        Args:
            text: Input text
            
        Returns:
            List of medical entities
        """
        # This is a placeholder - in production, use a proper NER model
        medical_keywords = [
            'symptom', 'diagnosis', 'treatment', 'medication', 'therapy',
            'pain', 'fever', 'headache', 'anxiety', 'depression', 'stress'
        ]
        
        entities = []
        text_lower = text.lower()
        
        for keyword in medical_keywords:
            if keyword in text_lower:
                entities.append(keyword)
        
        return list(set(entities))  # Remove duplicates
    
    @staticmethod
    def classify_intent(text: str) -> str:
        """
        Classify user intent (placeholder implementation).
        
        Args:
            text: Input text
            
        Returns:
            Classified intent
        """
        # This is a placeholder - in production, use a proper intent classifier
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['help', 'crisis', 'emergency', 'suicide']):
            return 'crisis'
        elif any(word in text_lower for word in ['symptom', 'pain', 'feel', 'hurt']):
            return 'symptom_description'
        elif any(word in text_lower for word in ['medication', 'drug', 'pill', 'prescription']):
            return 'medication_query'
        elif any(word in text_lower for word in ['sad', 'depressed', 'anxious', 'worried']):
            return 'emotional_support'
        elif '?' in text:
            return 'medical_question'
        else:
            return 'general_inquiry'


# Global validator and serializer instances
validator = DataValidator()
serializer = DataSerializer()
validation_utils = ValidationUtils()