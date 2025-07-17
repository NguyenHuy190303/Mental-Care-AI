"""
Core Pydantic data models for the Mental Health Agent system.
"""

from datetime import datetime, date
from typing import Dict, List, Any, Union, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class InputType(str, Enum):
    """Enumeration for different input types."""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"


class UrgencyLevel(int, Enum):
    """Enumeration for urgency levels (1-10 scale)."""
    LOW = 1
    MODERATE = 5
    HIGH = 8
    CRITICAL = 10


class UserInput(BaseModel):
    """Model for user input data."""
    user_id: str = Field(..., description="Unique identifier for the user")
    session_id: str = Field(..., description="Session identifier for conversation tracking")
    type: InputType = Field(..., description="Type of input (text, image, voice)")
    content: Union[str, bytes] = Field(..., description="The actual input content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the input was received")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('user_id', 'session_id')
    @classmethod
    def validate_ids(cls, v):
        if not v or not v.strip():
            raise ValueError("ID fields cannot be empty")
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if isinstance(v, str) and not v.strip():
            raise ValueError("Text content cannot be empty")
        return v

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: v.decode('utf-8', errors='ignore')
        }
    )


class AnalyzedInput(BaseModel):
    """Model for analyzed user input with extracted information."""
    text: str = Field(..., description="Processed text content")
    intent: str = Field(..., description="Classified intent of the input")
    medical_entities: List[str] = Field(default_factory=list, description="Extracted medical entities")
    urgency_level: int = Field(..., ge=1, le=10, description="Urgency level (1-10)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the analysis")
    emotional_context: Optional[str] = Field(None, description="Detected emotional context")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()
    
    @field_validator('intent')
    @classmethod
    def validate_intent(cls, v):
        allowed_intents = [
            "medical_question", "emotional_support", "crisis", 
            "general_inquiry", "symptom_description", "medication_query"
        ]
        if v not in allowed_intents:
            raise ValueError(f"Intent must be one of: {allowed_intents}")
        return v


class Citation(BaseModel):
    """Model for scientific citations and references."""
    source: str = Field(..., description="Source database or publication")
    title: str = Field(..., description="Title of the referenced work")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    publication_date: Optional[date] = Field(None, description="Publication date")
    url: str = Field(..., description="URL to the source")
    excerpt: str = Field(..., description="Relevant excerpt from the source")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        allowed_sources = ["pubmed", "who", "cdc", "nih", "mayo_clinic", "webmd"]
        if v.lower() not in allowed_sources:
            raise ValueError(f"Source must be one of: {allowed_sources}")
        return v.lower()


class MedicalImage(BaseModel):
    """Model for medical images and visual references."""
    url: str = Field(..., description="URL to the image")
    caption: str = Field(..., description="Image caption or description")
    source: str = Field(..., description="Source of the image")
    license: str = Field(..., description="License information")
    alt_text: str = Field(..., description="Alternative text for accessibility")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to the query")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class Document(BaseModel):
    """Model for retrieved documents from RAG system."""
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    source: str = Field(..., description="Document source")


class RAGResults(BaseModel):
    """Model for RAG search results."""
    documents: List[Document] = Field(default_factory=list, description="Retrieved documents")
    citations: List[Citation] = Field(default_factory=list, description="Extracted citations")
    confidence_scores: List[float] = Field(default_factory=list, description="Confidence scores")
    search_metadata: Dict[str, Any] = Field(default_factory=dict, description="Search metadata")
    query_embedding: Optional[List[float]] = Field(None, description="Query embedding vector")
    
    @field_validator('confidence_scores')
    @classmethod
    def validate_confidence_scores(cls, v):
        for score in v:
            if not 0.0 <= score <= 1.0:
                raise ValueError("All confidence scores must be between 0.0 and 1.0")
        return v


class UserContext(BaseModel):
    """Model for user context and conversation history."""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    compressed_history: str = Field(default="", description="Compressed conversation history")
    user_profile: Dict[str, Any] = Field(default_factory=dict, description="User profile data")
    session_context: Dict[str, Any] = Field(default_factory=dict, description="Session-specific context")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ProcessingContext(BaseModel):
    """Model for processing context passed between tools."""
    user_input: UserInput
    analyzed_input: Optional[AnalyzedInput] = None
    rag_results: Optional[RAGResults] = None
    user_context: Optional[UserContext] = None
    medical_images: List[MedicalImage] = Field(default_factory=list)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Model for the final agent response."""
    content: str = Field(..., description="Main response content")
    citations: List[Citation] = Field(default_factory=list, description="Supporting citations")
    medical_images: List[MedicalImage] = Field(default_factory=list, description="Relevant medical images")
    reasoning_steps: List[str] = Field(default_factory=list, description="Chain-of-thought reasoning steps")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Overall confidence level")
    safety_warnings: List[str] = Field(default_factory=list, description="Safety warnings")
    medical_disclaimer: str = Field(..., description="Medical disclaimer text")
    response_metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Response content cannot be empty")
        return v.strip()
    
    @field_validator('medical_disclaimer')
    @classmethod
    def validate_disclaimer(cls, v):
        if not v or not v.strip():
            raise ValueError("Medical disclaimer is required")
        return v.strip()


class ErrorResponse(BaseModel):
    """Model for error responses."""
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    suggested_action: str = Field(..., description="Suggested action for the user")
    emergency_resources: List[str] = Field(default_factory=list, description="Emergency resources if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ValidationResult(BaseModel):
    """Model for validation results."""
    is_valid: bool = Field(..., description="Whether the validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Validation confidence")