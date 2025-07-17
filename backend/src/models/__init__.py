"""
Data models for the Mental Health Agent backend.
"""

from .core import (
    UserInput,
    AnalyzedInput,
    RAGResults,
    Citation,
    AgentResponse,
    MedicalImage,
    UserContext,
    ProcessingContext
)

from .database import (
    User,
    Conversation,
    UsageMetric,
    FeedbackData,
    UserCreate,
    UserResponse,
    ConversationCreate,
    ConversationResponse,
    UsageMetricCreate,
    UsageMetricResponse,
    FeedbackCreate,
    FeedbackResponse
)

__all__ = [
    # Core models
    "UserInput",
    "AnalyzedInput",
    "RAGResults",
    "Citation",
    "AgentResponse",
    "MedicalImage",
    "UserContext",
    "ProcessingContext",

    # Database models
    "User",
    "Conversation",
    "UsageMetric",
    "FeedbackData",

    # API models
    "UserCreate",
    "UserResponse",
    "ConversationCreate",
    "ConversationResponse",
    "UsageMetricCreate",
    "UsageMetricResponse",
    "FeedbackCreate",
    "FeedbackResponse"
]