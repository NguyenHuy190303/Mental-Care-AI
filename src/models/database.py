"""
Database models using SQLAlchemy for PostgreSQL integration.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, DateTime, Integer, Float, Text, 
    Boolean, JSON, ForeignKey, DECIMAL, UUID
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, ConfigDict


Base = declarative_base()


class User(Base):
    """User table for authentication and user management."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Encrypted user profile data (GDPR/HIPAA compliant)
    encrypted_profile = Column(Text, nullable=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    usage_metrics = relationship("UsageMetric", back_populates="user", cascade="all, delete-orphan")
    feedback_data = relationship("FeedbackData", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Conversation(Base):
    """Conversation history table."""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_type = Column(String(50), nullable=False)  # 'user' or 'agent'
    
    # Encrypted message content (HIPAA compliant)
    encrypted_user_message = Column(Text, nullable=True)
    encrypted_agent_response = Column(Text, nullable=True)
    
    # Citations and metadata (can be stored as JSON)
    citations = Column(JSON, nullable=True)
    reasoning_steps = Column(JSON, nullable=True)
    confidence_level = Column(Float, nullable=True)
    
    # User feedback
    feedback_score = Column(Integer, nullable=True)  # thumbs up/down: 1/-1
    feedback_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, session_id={self.session_id})>"


class UsageMetric(Base):
    """Usage analytics and cost tracking table."""
    __tablename__ = "usage_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # API and model usage
    endpoint = Column(String(255), nullable=False)
    model_used = Column(String(255), nullable=False)
    tokens_consumed = Column(Integer, nullable=False, default=0)
    response_time_ms = Column(Integer, nullable=False, default=0)
    cost_usd = Column(DECIMAL(10, 6), nullable=False, default=0.0)
    
    # Request metadata
    request_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_metrics")
    
    def __repr__(self):
        return f"<UsageMetric(id={self.id}, user_id={self.user_id}, model={self.model_used})>"


class FeedbackData(Base):
    """Feedback data for RLHF training."""
    __tablename__ = "feedback_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    
    # Feedback details
    feedback_type = Column(String(50), nullable=False)  # 'thumbs_up', 'thumbs_down', 'detailed'
    rating = Column(Integer, nullable=True)  # 1-5 scale
    feedback_text = Column(Text, nullable=True)
    
    # Context for the feedback
    user_query = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    
    # Safety flags
    safety_concern = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="feedback_data")
    
    def __repr__(self):
        return f"<FeedbackData(id={self.id}, user_id={self.user_id}, type={self.feedback_type})>"


# Pydantic models for API serialization
class UserCreate(BaseModel):
    """Pydantic model for user creation."""
    username: str = Field(..., min_length=3, max_length=255)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """Pydantic model for user response."""
    id: str
    username: str
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ConversationCreate(BaseModel):
    """Pydantic model for conversation creation."""
    session_id: str
    message_type: str = Field(..., pattern=r'^(user|agent)$')
    user_message: Optional[str] = None
    agent_response: Optional[str] = None
    citations: Optional[Dict[str, Any]] = None
    reasoning_steps: Optional[list] = None
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)


class ConversationResponse(BaseModel):
    """Pydantic model for conversation response."""
    id: str
    user_id: str
    session_id: str
    message_type: str
    citations: Optional[Dict[str, Any]] = None
    reasoning_steps: Optional[list] = None
    confidence_level: Optional[float] = None
    feedback_score: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class UsageMetricCreate(BaseModel):
    """Pydantic model for usage metric creation."""
    session_id: Optional[str] = None
    endpoint: str
    model_used: str
    tokens_consumed: int = Field(..., ge=0)
    response_time_ms: int = Field(..., ge=0)
    cost_usd: float = Field(..., ge=0.0)
    request_metadata: Optional[Dict[str, Any]] = None


class UsageMetricResponse(BaseModel):
    """Pydantic model for usage metric response."""
    id: str
    user_id: str
    session_id: Optional[str] = None
    endpoint: str
    model_used: str
    tokens_consumed: int
    response_time_ms: int
    cost_usd: float
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class FeedbackCreate(BaseModel):
    """Pydantic model for feedback creation."""
    conversation_id: str
    feedback_type: str = Field(..., pattern=r'^(thumbs_up|thumbs_down|detailed)$')
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_text: Optional[str] = None
    user_query: str
    agent_response: str
    safety_concern: bool = False


class FeedbackResponse(BaseModel):
    """Pydantic model for feedback response."""
    id: str
    user_id: str
    conversation_id: str
    feedback_type: str
    rating: Optional[int] = None
    feedback_text: Optional[str] = None
    safety_concern: bool
    escalated: bool
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )