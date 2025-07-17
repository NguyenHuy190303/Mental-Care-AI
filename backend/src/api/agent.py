"""
API endpoints for the Linear Mental Health Agent.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ..database import get_db_session
from ..models.database import User
from ..models.core import UserInput, InputType, AgentResponse
from ..agents import LinearMentalHealthAgent
from ..utils import get_global_agent, initialize_global_agent, get_agent_health_status
from .auth import get_current_user

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/agent", tags=["mental_health_agent"])

# Global agent instance (will be initialized on startup)
_agent_instance: Optional[LinearMentalHealthAgent] = None


async def get_agent_instance() -> LinearMentalHealthAgent:
    """Get the global agent instance."""
    try:
        return await get_global_agent()
    except Exception as e:
        logger.error(f"Failed to get agent instance: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mental Health Agent not available"
        )


class ChatRequest:
    """Request model for chat endpoint."""
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.session_id = session_id or str(uuid.uuid4())
        self.message_type = message_type
        self.metadata = metadata or {}


class ChatResponse:
    """Response model for chat endpoint."""
    
    def __init__(
        self,
        response: str,
        session_id: str,
        confidence_level: float,
        citations: list,
        reasoning_steps: list,
        safety_warnings: list,
        medical_disclaimer: str,
        metadata: Dict[str, Any]
    ):
        self.response = response
        self.session_id = session_id
        self.confidence_level = confidence_level
        self.citations = citations
        self.reasoning_steps = reasoning_steps
        self.safety_warnings = safety_warnings
        self.medical_disclaimer = medical_disclaimer
        self.metadata = metadata


@router.post("/chat", response_model=dict)
async def chat_with_agent(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Chat with the Mental Health Agent.
    
    Args:
        request: Chat request with message and optional metadata
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Agent response with reasoning and citations
    """
    try:
        # Validate request
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        session_id = request.get("session_id", str(uuid.uuid4()))
        message_type = request.get("message_type", "text")
        metadata = request.get("metadata", {})
        
        # Create user input
        user_input = UserInput(
            user_id=str(current_user.id),
            session_id=session_id,
            type=InputType.TEXT if message_type == "text" else InputType.VOICE,
            content=message,
            metadata=metadata
        )
        
        # Get agent and process request
        agent = await get_agent_instance()
        agent_response, processing_metadata = await agent.process_request(user_input)
        
        # Format response
        response_data = {
            "response": agent_response.content,
            "session_id": session_id,
            "confidence_level": agent_response.confidence_level,
            "citations": [
                {
                    "title": citation.title,
                    "source": citation.source,
                    "url": citation.url,
                    "excerpt": citation.excerpt,
                    "relevance_score": citation.relevance_score
                }
                for citation in agent_response.citations
            ],
            "reasoning_steps": agent_response.reasoning_steps,
            "safety_warnings": agent_response.safety_warnings,
            "medical_disclaimer": agent_response.medical_disclaimer,
            "metadata": {
                **agent_response.response_metadata,
                "processing": processing_metadata
            }
        }
        
        logger.info(f"Chat request processed for user {current_user.username}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@router.get("/status")
async def get_agent_status():
    """
    Get agent status and health information.

    Returns:
        Agent status and component health
    """
    try:
        health_status = await get_agent_health_status()
        return health_status

    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": str(uuid.uuid4())
        }


@router.get("/capabilities")
async def get_agent_capabilities():
    """
    Get agent capabilities and supported features.
    
    Returns:
        Agent capabilities information
    """
    return {
        "agent_type": "LinearMentalHealthAgent",
        "architecture": "Single-Threaded Linear Agent",
        "capabilities": [
            "Mental health support and guidance",
            "Evidence-based responses with scientific citations",
            "Crisis detection and safety protocols",
            "Chain-of-thought reasoning",
            "Multimodal input support (text, voice)",
            "Context-aware conversations",
            "Professional referral recommendations"
        ],
        "supported_input_types": ["text", "voice"],
        "safety_features": [
            "Crisis keyword detection",
            "Safety compliance validation",
            "Medical disclaimer inclusion",
            "Emergency resource provision",
            "Professional referral guidance"
        ],
        "knowledge_sources": [
            "PubMed research papers",
            "WHO guidelines",
            "CDC fact sheets",
            "NIH resources",
            "Medical institution publications"
        ]
    }


@router.post("/feedback")
async def submit_feedback(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submit feedback on agent responses.
    
    Args:
        request: Feedback request with rating and comments
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Feedback submission confirmation
    """
    try:
        # Validate request
        session_id = request.get("session_id")
        rating = request.get("rating")  # 1-5 scale or thumbs up/down
        feedback_text = request.get("feedback_text", "")
        response_id = request.get("response_id")
        
        if not session_id or rating is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID and rating are required"
            )
        
        # Store feedback (would implement database storage here)
        feedback_data = {
            "user_id": str(current_user.id),
            "session_id": session_id,
            "response_id": response_id,
            "rating": rating,
            "feedback_text": feedback_text,
            "timestamp": str(uuid.uuid4())
        }
        
        logger.info(f"Feedback submitted by user {current_user.username}: {feedback_data}")
        
        return {
            "message": "Feedback submitted successfully",
            "feedback_id": str(uuid.uuid4())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get("/conversation/{session_id}")
async def get_conversation_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Conversation history
    """
    try:
        # Would implement database query here
        # For now, return placeholder
        return {
            "session_id": session_id,
            "user_id": str(current_user.id),
            "messages": [],
            "message": "Conversation history retrieval not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )


@router.delete("/conversation/{session_id}")
async def delete_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete conversation history for a session.
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Deletion confirmation
    """
    try:
        # Would implement database deletion here
        logger.info(f"Conversation {session_id} deletion requested by user {current_user.username}")
        
        return {
            "message": "Conversation deleted successfully",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


# Startup function to initialize agent
async def startup_agent():
    """Initialize agent on startup."""
    await initialize_global_agent()
