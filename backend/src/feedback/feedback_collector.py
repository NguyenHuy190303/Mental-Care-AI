"""
Feedback Collection System for Mental Health Agent
Collects user feedback for RLHF (Reinforcement Learning from Human Feedback) and system improvement.
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from pydantic import BaseModel, Field, validator

from ..database import get_db_session
from ..models.database import FeedbackEntry, UserInteraction
from ..models.core import UserInput, AgentResponse
from ..monitoring.logging_config import get_logger

logger = get_logger("feedback.collector")


class FeedbackType(str, Enum):
    """Types of feedback that can be collected."""
    RESPONSE_QUALITY = "response_quality"
    HELPFULNESS = "helpfulness"
    ACCURACY = "accuracy"
    SAFETY = "safety"
    EMPATHY = "empathy"
    CLARITY = "clarity"
    OVERALL_SATISFACTION = "overall_satisfaction"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    CRISIS_HANDLING = "crisis_handling"


class FeedbackRating(int, Enum):
    """Standardized rating scale for feedback."""
    VERY_POOR = 1
    POOR = 2
    FAIR = 3
    GOOD = 4
    EXCELLENT = 5


class FeedbackData(BaseModel):
    """Structured feedback data model."""
    
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    interaction_id: Optional[str] = None
    feedback_type: FeedbackType
    rating: Optional[FeedbackRating] = None
    text_feedback: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('text_feedback')
    def validate_text_feedback(cls, v):
        if v and len(v) > 5000:
            raise ValueError('Text feedback must be less than 5000 characters')
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        # Ensure metadata doesn't contain sensitive information
        sensitive_keys = ['password', 'token', 'api_key', 'secret']
        for key in v.keys():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                raise ValueError(f'Metadata cannot contain sensitive key: {key}')
        return v


class InteractionFeedback(BaseModel):
    """Feedback specifically for agent interactions."""
    
    user_input: str
    agent_response: str
    response_helpful: Optional[bool] = None
    response_accurate: Optional[bool] = None
    response_empathetic: Optional[bool] = None
    response_clear: Optional[bool] = None
    response_safe: Optional[bool] = None
    overall_rating: Optional[FeedbackRating] = None
    improvement_suggestions: Optional[str] = None
    would_recommend: Optional[bool] = None
    crisis_handled_well: Optional[bool] = None
    
    class Config:
        schema_extra = {
            "example": {
                "user_input": "I'm feeling anxious about my job interview tomorrow",
                "agent_response": "It's natural to feel anxious before important events...",
                "response_helpful": True,
                "response_accurate": True,
                "response_empathetic": True,
                "response_clear": True,
                "response_safe": True,
                "overall_rating": 4,
                "improvement_suggestions": "Could provide more specific coping strategies",
                "would_recommend": True
            }
        }


class FeedbackCollector:
    """Main feedback collection system."""
    
    def __init__(self):
        """Initialize feedback collector."""
        self.feedback_cache: List[FeedbackData] = []
        self.batch_size = 10
        logger.info("Feedback collector initialized")
    
    async def collect_feedback(
        self,
        feedback_data: FeedbackData,
        store_immediately: bool = False
    ) -> str:
        """
        Collect feedback from users.
        
        Args:
            feedback_data: Structured feedback data
            store_immediately: Whether to store immediately or batch
            
        Returns:
            Feedback ID
        """
        try:
            # Validate and sanitize feedback
            sanitized_feedback = await self._sanitize_feedback(feedback_data)
            
            # Log feedback collection (without sensitive data)
            logger.info(
                "Feedback collected",
                feedback_id=sanitized_feedback.feedback_id,
                feedback_type=sanitized_feedback.feedback_type.value,
                user_id=sanitized_feedback.user_id,
                session_id=sanitized_feedback.session_id,
                has_rating=sanitized_feedback.rating is not None,
                has_text=sanitized_feedback.text_feedback is not None
            )
            
            if store_immediately:
                await self._store_feedback(sanitized_feedback)
            else:
                # Add to batch
                self.feedback_cache.append(sanitized_feedback)
                
                # Store batch if full
                if len(self.feedback_cache) >= self.batch_size:
                    await self._store_feedback_batch()
            
            return sanitized_feedback.feedback_id
            
        except Exception as e:
            logger.error(f"Failed to collect feedback: {e}")
            raise
    
    async def collect_interaction_feedback(
        self,
        user_id: str,
        session_id: str,
        interaction_id: str,
        interaction_feedback: InteractionFeedback
    ) -> str:
        """
        Collect feedback for a specific interaction.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            interaction_id: Interaction identifier
            interaction_feedback: Detailed interaction feedback
            
        Returns:
            Feedback ID
        """
        try:
            # Convert interaction feedback to structured feedback
            feedback_data = FeedbackData(
                user_id=user_id,
                session_id=session_id,
                interaction_id=interaction_id,
                feedback_type=FeedbackType.OVERALL_SATISFACTION,
                rating=interaction_feedback.overall_rating,
                text_feedback=interaction_feedback.improvement_suggestions,
                metadata={
                    'response_helpful': interaction_feedback.response_helpful,
                    'response_accurate': interaction_feedback.response_accurate,
                    'response_empathetic': interaction_feedback.response_empathetic,
                    'response_clear': interaction_feedback.response_clear,
                    'response_safe': interaction_feedback.response_safe,
                    'would_recommend': interaction_feedback.would_recommend,
                    'crisis_handled_well': interaction_feedback.crisis_handled_well,
                    'user_input_length': len(interaction_feedback.user_input),
                    'agent_response_length': len(interaction_feedback.agent_response)
                }
            )
            
            return await self.collect_feedback(feedback_data, store_immediately=True)
            
        except Exception as e:
            logger.error(f"Failed to collect interaction feedback: {e}")
            raise
    
    async def collect_safety_feedback(
        self,
        user_id: str,
        session_id: str,
        safety_concern: str,
        severity: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Collect safety-related feedback.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            safety_concern: Description of safety concern
            severity: Severity level (low, medium, high, critical)
            context: Additional context
            
        Returns:
            Feedback ID
        """
        try:
            feedback_data = FeedbackData(
                user_id=user_id,
                session_id=session_id,
                feedback_type=FeedbackType.SAFETY,
                text_feedback=safety_concern,
                metadata={
                    'severity': severity,
                    'context': context,
                    'requires_review': True
                }
            )
            
            # Safety feedback is always stored immediately
            feedback_id = await self.collect_feedback(feedback_data, store_immediately=True)
            
            # Log safety feedback separately
            logger.warning(
                "Safety feedback collected",
                feedback_id=feedback_id,
                severity=severity,
                user_id=user_id,
                session_id=session_id
            )
            
            return feedback_id
            
        except Exception as e:
            logger.error(f"Failed to collect safety feedback: {e}")
            raise
    
    async def _sanitize_feedback(self, feedback_data: FeedbackData) -> FeedbackData:
        """Sanitize feedback data to remove sensitive information."""
        sanitized = feedback_data.copy()
        
        # Remove or mask sensitive information from text feedback
        if sanitized.text_feedback:
            # Basic sanitization - in production, use more sophisticated methods
            sensitive_patterns = [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
            ]
            
            import re
            text = sanitized.text_feedback
            for pattern in sensitive_patterns:
                text = re.sub(pattern, '[REDACTED]', text)
            sanitized.text_feedback = text
        
        return sanitized
    
    async def _store_feedback(self, feedback_data: FeedbackData):
        """Store individual feedback in database."""
        try:
            async with get_db_session() as session:
                feedback_entry = FeedbackEntry(
                    feedback_id=feedback_data.feedback_id,
                    user_id=feedback_data.user_id,
                    session_id=feedback_data.session_id,
                    interaction_id=feedback_data.interaction_id,
                    feedback_type=feedback_data.feedback_type.value,
                    rating=feedback_data.rating.value if feedback_data.rating else None,
                    text_feedback=feedback_data.text_feedback,
                    metadata=feedback_data.metadata,
                    created_at=feedback_data.timestamp
                )
                
                session.add(feedback_entry)
                await session.commit()
                
                logger.debug(f"Feedback stored: {feedback_data.feedback_id}")
                
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")
            raise
    
    async def _store_feedback_batch(self):
        """Store batch of feedback entries."""
        if not self.feedback_cache:
            return
        
        try:
            async with get_db_session() as session:
                feedback_entries = [
                    FeedbackEntry(
                        feedback_id=feedback.feedback_id,
                        user_id=feedback.user_id,
                        session_id=feedback.session_id,
                        interaction_id=feedback.interaction_id,
                        feedback_type=feedback.feedback_type.value,
                        rating=feedback.rating.value if feedback.rating else None,
                        text_feedback=feedback.text_feedback,
                        metadata=feedback.metadata,
                        created_at=feedback.timestamp
                    )
                    for feedback in self.feedback_cache
                ]
                
                session.add_all(feedback_entries)
                await session.commit()
                
                logger.info(f"Stored batch of {len(feedback_entries)} feedback entries")
                
                # Clear cache
                self.feedback_cache.clear()
                
        except Exception as e:
            logger.error(f"Failed to store feedback batch: {e}")
            raise
    
    async def get_feedback_summary(
        self,
        user_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get feedback summary for analysis.
        
        Args:
            user_id: Filter by user ID (optional)
            feedback_type: Filter by feedback type (optional)
            days: Number of days to include
            
        Returns:
            Feedback summary statistics
        """
        try:
            async with get_db_session() as session:
                # Build query
                query = select(FeedbackEntry).where(
                    FeedbackEntry.created_at >= datetime.utcnow() - timedelta(days=days)
                )
                
                if user_id:
                    query = query.where(FeedbackEntry.user_id == user_id)
                
                if feedback_type:
                    query = query.where(FeedbackEntry.feedback_type == feedback_type.value)
                
                result = await session.execute(query)
                feedback_entries = result.scalars().all()
                
                # Calculate summary statistics
                total_feedback = len(feedback_entries)
                
                if total_feedback == 0:
                    return {
                        'total_feedback': 0,
                        'average_rating': None,
                        'feedback_by_type': {},
                        'rating_distribution': {}
                    }
                
                # Calculate average rating
                ratings = [f.rating for f in feedback_entries if f.rating is not None]
                average_rating = sum(ratings) / len(ratings) if ratings else None
                
                # Feedback by type
                feedback_by_type = {}
                for feedback in feedback_entries:
                    feedback_type = feedback.feedback_type
                    if feedback_type not in feedback_by_type:
                        feedback_by_type[feedback_type] = 0
                    feedback_by_type[feedback_type] += 1
                
                # Rating distribution
                rating_distribution = {}
                for rating in ratings:
                    if rating not in rating_distribution:
                        rating_distribution[rating] = 0
                    rating_distribution[rating] += 1
                
                return {
                    'total_feedback': total_feedback,
                    'average_rating': round(average_rating, 2) if average_rating else None,
                    'feedback_by_type': feedback_by_type,
                    'rating_distribution': rating_distribution,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Failed to get feedback summary: {e}")
            raise
    
    async def flush_cache(self):
        """Flush any remaining feedback in cache to database."""
        if self.feedback_cache:
            await self._store_feedback_batch()


# Global feedback collector instance
feedback_collector = FeedbackCollector()
