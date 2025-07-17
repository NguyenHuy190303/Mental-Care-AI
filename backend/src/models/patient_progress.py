"""
Patient Progress Tracking Models for Healthcare-Compliant Dashboard.

This module defines data models for comprehensive patient progress tracking,
including session analytics, mood tracking, treatment timelines, and provider oversight.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, 
    ForeignKey, UUID, DECIMAL, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, ConfigDict, validator

from .database import Base


class MoodLevel(str, Enum):
    """Standardized mood levels for tracking."""
    VERY_LOW = "very_low"
    LOW = "low" 
    NEUTRAL = "neutral"
    GOOD = "good"
    VERY_GOOD = "very_good"


class SessionType(str, Enum):
    """Types of therapy sessions."""
    INITIAL_ASSESSMENT = "initial_assessment"
    REGULAR_SESSION = "regular_session"
    CRISIS_INTERVENTION = "crisis_intervention"
    FOLLOW_UP = "follow_up"
    CHECK_IN = "check_in"


class ProgressMetricType(str, Enum):
    """Types of progress metrics."""
    MOOD_SCORE = "mood_score"
    ANXIETY_LEVEL = "anxiety_level"
    DEPRESSION_SCORE = "depression_score"
    ENGAGEMENT_SCORE = "engagement_score"
    WELLNESS_INDEX = "wellness_index"
    COPING_SKILLS = "coping_skills"


class AlertLevel(str, Enum):
    """Alert levels for provider notifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Database Models

class PatientSession(Base):
    """Enhanced session tracking with clinical metrics."""
    __tablename__ = "patient_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Session details
    session_type = Column(String(50), nullable=False, default=SessionType.REGULAR_SESSION.value)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Clinical metrics
    pre_session_mood = Column(String(20), nullable=True)  # MoodLevel enum
    post_session_mood = Column(String(20), nullable=True)
    mood_improvement = Column(Float, nullable=True)  # -2.0 to +2.0 scale
    
    # Engagement metrics
    message_count = Column(Integer, default=0)
    avg_response_time_seconds = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Clinical assessments
    anxiety_level = Column(Integer, nullable=True)  # 1-10 scale
    depression_indicators = Column(Integer, nullable=True)  # 1-10 scale
    crisis_risk_level = Column(Integer, default=1)  # 1-5 scale
    
    # Session outcomes
    goals_discussed = Column(JSON, nullable=True)
    coping_strategies_used = Column(JSON, nullable=True)
    homework_assigned = Column(Text, nullable=True)
    next_session_recommended = Column(Boolean, default=False)
    
    # Provider notes (encrypted)
    encrypted_clinical_notes = Column(Text, nullable=True)
    provider_assessment = Column(JSON, nullable=True)
    
    # Metadata
    session_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="patient_sessions")
    progress_metrics = relationship("ProgressMetric", back_populates="session")
    session_alerts = relationship("SessionAlert", back_populates="session")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_patient_sessions_user_date', 'user_id', 'start_time'),
        Index('idx_patient_sessions_session_id', 'session_id'),
        CheckConstraint('crisis_risk_level >= 1 AND crisis_risk_level <= 5', name='valid_crisis_risk'),
        CheckConstraint('engagement_score >= 0.0 AND engagement_score <= 1.0', name='valid_engagement'),
    )
    
    def __repr__(self):
        return f"<PatientSession(id={self.id}, user_id={self.user_id}, type={self.session_type})>"


class ProgressMetric(Base):
    """Individual progress metrics for detailed tracking."""
    __tablename__ = "progress_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("patient_sessions.id"), nullable=True)
    
    # Metric details
    metric_type = Column(String(50), nullable=False)  # ProgressMetricType enum
    metric_value = Column(Float, nullable=False)
    metric_scale_min = Column(Float, default=0.0)
    metric_scale_max = Column(Float, default=10.0)
    
    # Context
    measurement_context = Column(String(100), nullable=True)  # "pre_session", "post_session", "daily_check"
    notes = Column(Text, nullable=True)
    
    # Metadata
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    recorded_by = Column(String(50), default="patient")  # "patient", "provider", "system"
    
    # Relationships
    user = relationship("User", back_populates="progress_metrics")
    session = relationship("PatientSession", back_populates="progress_metrics")
    
    # Indexes
    __table_args__ = (
        Index('idx_progress_metrics_user_type_date', 'user_id', 'metric_type', 'recorded_at'),
        Index('idx_progress_metrics_session', 'session_id'),
    )
    
    def __repr__(self):
        return f"<ProgressMetric(id={self.id}, type={self.metric_type}, value={self.metric_value})>"


class TreatmentMilestone(Base):
    """Treatment milestones and goals tracking."""
    __tablename__ = "treatment_milestones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Milestone details
    milestone_type = Column(String(50), nullable=False)  # "goal_set", "goal_achieved", "breakthrough", "setback"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Progress tracking
    target_date = Column(DateTime(timezone=True), nullable=True)
    achieved_date = Column(DateTime(timezone=True), nullable=True)
    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    
    # Clinical context
    related_session_id = Column(UUID(as_uuid=True), nullable=True)
    provider_notes = Column(Text, nullable=True)
    patient_reflection = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    priority_level = Column(Integer, default=3)  # 1-5 scale
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="treatment_milestones")
    
    def __repr__(self):
        return f"<TreatmentMilestone(id={self.id}, title='{self.title}', progress={self.progress_percentage}%)>"


class SessionAlert(Base):
    """Alerts and notifications for provider oversight."""
    __tablename__ = "session_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("patient_sessions.id"), nullable=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # "crisis_risk", "mood_decline", "engagement_drop", "missed_session"
    alert_level = Column(String(20), nullable=False)  # AlertLevel enum
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Alert context
    triggered_by = Column(String(100), nullable=True)  # What triggered the alert
    alert_data = Column(JSON, nullable=True)  # Additional alert context
    
    # Status tracking
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="session_alerts")
    session = relationship("PatientSession", back_populates="session_alerts")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_alerts_user_level', 'user_id', 'alert_level'),
        Index('idx_session_alerts_unresolved', 'is_resolved', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SessionAlert(id={self.id}, type={self.alert_type}, level={self.alert_level})>"


class ProviderNote(Base):
    """Clinical notes from healthcare providers."""
    __tablename__ = "provider_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("patient_sessions.id"), nullable=True)
    
    # Note details
    note_type = Column(String(50), nullable=False)  # "clinical_assessment", "treatment_plan", "progress_note"
    title = Column(String(255), nullable=True)
    
    # Encrypted content (HIPAA compliant)
    encrypted_content = Column(Text, nullable=False)
    
    # Clinical context
    assessment_scores = Column(JSON, nullable=True)
    treatment_recommendations = Column(JSON, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    
    # Provider information
    provider_id = Column(String(100), nullable=False)
    provider_role = Column(String(50), nullable=True)  # "psychiatrist", "psychologist", "therapist"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="provider_notes")
    
    def __repr__(self):
        return f"<ProviderNote(id={self.id}, type={self.note_type}, provider={self.provider_id})>"


# Pydantic Models for API Serialization

class PatientSessionCreate(BaseModel):
    """Pydantic model for creating patient sessions."""
    session_id: str
    session_type: SessionType = SessionType.REGULAR_SESSION
    start_time: datetime
    pre_session_mood: Optional[MoodLevel] = None
    anxiety_level: Optional[int] = Field(None, ge=1, le=10)
    depression_indicators: Optional[int] = Field(None, ge=1, le=10)
    goals_discussed: Optional[List[str]] = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class PatientSessionResponse(BaseModel):
    """Pydantic model for patient session response."""
    id: str
    user_id: str
    session_id: str
    session_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    pre_session_mood: Optional[str] = None
    post_session_mood: Optional[str] = None
    mood_improvement: Optional[float] = None
    message_count: int
    engagement_score: Optional[float] = None
    anxiety_level: Optional[int] = None
    depression_indicators: Optional[int] = None
    crisis_risk_level: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class ProgressMetricCreate(BaseModel):
    """Pydantic model for creating progress metrics."""
    metric_type: ProgressMetricType
    metric_value: float
    metric_scale_min: float = 0.0
    metric_scale_max: float = 10.0
    measurement_context: Optional[str] = None
    notes: Optional[str] = None
    recorded_by: str = "patient"


class ProgressMetricResponse(BaseModel):
    """Pydantic model for progress metric response."""
    id: str
    user_id: str
    session_id: Optional[str] = None
    metric_type: str
    metric_value: float
    metric_scale_min: float
    metric_scale_max: float
    measurement_context: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: datetime
    recorded_by: str

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class TreatmentMilestoneCreate(BaseModel):
    """Pydantic model for creating treatment milestones."""
    milestone_type: str
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    priority_level: int = Field(3, ge=1, le=5)


class TreatmentMilestoneResponse(BaseModel):
    """Pydantic model for treatment milestone response."""
    id: str
    user_id: str
    milestone_type: str
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    achieved_date: Optional[datetime] = None
    progress_percentage: float
    priority_level: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class SessionAlertResponse(BaseModel):
    """Pydantic model for session alert response."""
    id: str
    user_id: str
    session_id: Optional[str] = None
    alert_type: str
    alert_level: str
    title: str
    description: str
    is_acknowledged: bool
    is_resolved: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class PatientProgressSummary(BaseModel):
    """Comprehensive patient progress summary."""
    user_id: str
    total_sessions: int
    avg_session_duration: Optional[float] = None
    current_mood_trend: Optional[str] = None
    wellness_score: Optional[float] = None
    engagement_trend: Optional[str] = None
    active_alerts: int
    recent_milestones: List[TreatmentMilestoneResponse]
    progress_metrics: Dict[str, List[float]]  # metric_type -> values over time
    last_session_date: Optional[datetime] = None
    next_recommended_session: Optional[datetime] = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


# Update User model to include new relationships
# This would be added to the existing User model in database.py
"""
# Add these relationships to the existing User model:
patient_sessions = relationship("PatientSession", back_populates="user", cascade="all, delete-orphan")
progress_metrics = relationship("ProgressMetric", back_populates="user", cascade="all, delete-orphan")
treatment_milestones = relationship("TreatmentMilestone", back_populates="user", cascade="all, delete-orphan")
session_alerts = relationship("SessionAlert", back_populates="user", cascade="all, delete-orphan")
provider_notes = relationship("ProviderNote", back_populates="user", cascade="all, delete-orphan")
"""
