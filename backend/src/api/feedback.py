"""
Feedback API endpoints for Mental Health Agent.
Handles user feedback collection and RLHF data processing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..feedback.feedback_collector import (
    FeedbackCollector, FeedbackData, FeedbackType, FeedbackRating,
    InteractionFeedback, feedback_collector
)
from ..feedback.rlhf_processor import RLHFProcessor, rlhf_processor
from ..testing.test_runner import MentalHealthTestRunner
from ..testing.test_scenarios import TestScenarioType
from .auth import get_current_user
from ..models.database import User
from ..monitoring.logging_config import get_logger

router = APIRouter(prefix="/feedback", tags=["feedback"])
logger = get_logger("api.feedback")

# Simple admin check function
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin privileges."""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


@router.post("/submit", summary="Submit User Feedback")
async def submit_feedback(
    feedback_data: FeedbackData,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit user feedback for an interaction.
    
    Args:
        feedback_data: Structured feedback data
        background_tasks: Background task handler
        current_user: Current authenticated user
        
    Returns:
        Feedback submission confirmation
    """
    try:
        # Validate user ID matches current user
        if feedback_data.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot submit feedback for another user")
        
        # Collect feedback
        feedback_id = await feedback_collector.collect_feedback(
            feedback_data=feedback_data,
            store_immediately=True
        )
        
        # Log feedback submission
        logger.info(
            "Feedback submitted",
            feedback_id=feedback_id,
            feedback_type=feedback_data.feedback_type.value,
            user_id=current_user.id,
            session_id=feedback_data.session_id,
            has_rating=feedback_data.rating is not None
        )
        
        return {
            "feedback_id": feedback_id,
            "message": "Feedback submitted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.post("/interaction", summary="Submit Interaction Feedback")
async def submit_interaction_feedback(
    interaction_id: str,
    interaction_feedback: InteractionFeedback,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit detailed feedback for a specific interaction.
    
    Args:
        interaction_id: ID of the interaction being rated
        interaction_feedback: Detailed interaction feedback
        current_user: Current authenticated user
        
    Returns:
        Feedback submission confirmation
    """
    try:
        # Get user's session ID (would typically be from request context)
        session_id = getattr(current_user, 'current_session_id', 'unknown')
        
        # Collect interaction feedback
        feedback_id = await feedback_collector.collect_interaction_feedback(
            user_id=current_user.id,
            session_id=session_id,
            interaction_id=interaction_id,
            interaction_feedback=interaction_feedback
        )
        
        logger.info(
            "Interaction feedback submitted",
            feedback_id=feedback_id,
            interaction_id=interaction_id,
            user_id=current_user.id,
            overall_rating=interaction_feedback.overall_rating
        )
        
        return {
            "feedback_id": feedback_id,
            "interaction_id": interaction_id,
            "message": "Interaction feedback submitted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to submit interaction feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit interaction feedback")


@router.post("/safety", summary="Submit Safety Feedback")
async def submit_safety_feedback(
    safety_concern: str,
    severity: str = Query(..., regex="^(low|medium|high|critical)$"),
    context: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit safety-related feedback or concerns.
    
    Args:
        safety_concern: Description of the safety concern
        severity: Severity level (low, medium, high, critical)
        context: Additional context information
        current_user: Current authenticated user
        
    Returns:
        Safety feedback submission confirmation
    """
    try:
        session_id = getattr(current_user, 'current_session_id', 'unknown')
        
        # Collect safety feedback
        feedback_id = await feedback_collector.collect_safety_feedback(
            user_id=current_user.id,
            session_id=session_id,
            safety_concern=safety_concern,
            severity=severity,
            context=context or {}
        )
        
        logger.warning(
            "Safety feedback submitted",
            feedback_id=feedback_id,
            severity=severity,
            user_id=current_user.id,
            session_id=session_id
        )
        
        return {
            "feedback_id": feedback_id,
            "message": "Safety feedback submitted successfully. Thank you for helping us improve safety.",
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to submit safety feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit safety feedback")


@router.get("/summary", summary="Get Feedback Summary")
async def get_feedback_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    feedback_type: Optional[FeedbackType] = Query(None, description="Filter by feedback type"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get feedback summary for the current user.
    
    Args:
        days: Number of days to include in summary
        feedback_type: Optional feedback type filter
        current_user: Current authenticated user
        
    Returns:
        Feedback summary statistics
    """
    try:
        summary = await feedback_collector.get_feedback_summary(
            user_id=current_user.id,
            feedback_type=feedback_type,
            days=days
        )
        
        return {
            "user_id": current_user.id,
            "period_days": days,
            "feedback_type_filter": feedback_type.value if feedback_type else None,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get feedback summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback summary")


@router.get("/admin/summary", summary="Get Admin Feedback Summary")
async def get_admin_feedback_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    feedback_type: Optional[FeedbackType] = Query(None, description="Filter by feedback type"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive feedback summary for administrators.
    
    Args:
        days: Number of days to include in summary
        feedback_type: Optional feedback type filter
        current_user: Current authenticated admin user
        
    Returns:
        Comprehensive feedback summary
    """
    try:
        # Get overall summary (all users)
        summary = await feedback_collector.get_feedback_summary(
            user_id=None,  # All users
            feedback_type=feedback_type,
            days=days
        )
        
        return {
            "period_days": days,
            "feedback_type_filter": feedback_type.value if feedback_type else None,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat(),
            "requested_by": current_user.id
        }
        
    except Exception as e:
        logger.error(f"Failed to get admin feedback summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback summary")


@router.post("/admin/rlhf/process", summary="Process RLHF Data")
async def process_rlhf_data(
    background_tasks: BackgroundTasks,
    days: int = Query(30, ge=1, le=365, description="Number of days of data to process"),
    min_feedback_count: int = Query(2, ge=1, le=10, description="Minimum feedback count per interaction"),
    include_safety_feedback: bool = Query(True, description="Include safety-related feedback"),
    export_format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Process feedback data for RLHF training.
    
    Args:
        days: Number of days of data to process
        min_feedback_count: Minimum feedback count per interaction
        include_safety_feedback: Whether to include safety feedback
        export_format: Format for data export
        background_tasks: Background task handler
        current_user: Current authenticated admin user
        
    Returns:
        RLHF processing status
    """
    try:
        # Process RLHF data
        dataset = await rlhf_processor.process_feedback_for_rlhf(
            days=days,
            min_feedback_count=min_feedback_count,
            include_safety_feedback=include_safety_feedback
        )
        
        # Export dataset in background
        background_tasks.add_task(
            rlhf_processor.export_dataset,
            dataset=dataset,
            format=export_format
        )
        
        logger.info(
            "RLHF data processed",
            datapoints_created=len(dataset),
            days=days,
            requested_by=current_user.id
        )
        
        return {
            "message": "RLHF data processed successfully",
            "datapoints_created": len(dataset),
            "quality_distribution": dataset.get_quality_distribution(),
            "average_score": dataset.get_average_score(),
            "processing_parameters": {
                "days": days,
                "min_feedback_count": min_feedback_count,
                "include_safety_feedback": include_safety_feedback
            },
            "export_format": export_format,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to process RLHF data: {e}")
        raise HTTPException(status_code=500, detail="Failed to process RLHF data")


@router.get("/admin/rlhf/metrics", summary="Get RLHF Metrics")
async def get_rlhf_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get RLHF metrics and statistics.
    
    Args:
        days: Number of days to analyze
        current_user: Current authenticated admin user
        
    Returns:
        RLHF metrics and statistics
    """
    try:
        metrics = await rlhf_processor.get_rlhf_metrics(days=days)
        
        return {
            "period_days": days,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "requested_by": current_user.id
        }
        
    except Exception as e:
        logger.error(f"Failed to get RLHF metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve RLHF metrics")


@router.post("/admin/test/run", summary="Run Agent Tests")
async def run_agent_tests(
    background_tasks: BackgroundTasks,
    test_type: str = Query("all", regex="^(all|crisis|safety|normal)$", description="Type of tests to run"),
    include_crisis: bool = Query(True, description="Include crisis scenarios"),
    include_safety: bool = Query(True, description="Include safety scenarios"),
    include_edge_cases: bool = Query(True, description="Include edge cases"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Run comprehensive agent tests.
    
    Args:
        test_type: Type of tests to run
        include_crisis: Include crisis scenarios
        include_safety: Include safety scenarios
        include_edge_cases: Include edge cases
        background_tasks: Background task handler
        current_user: Current authenticated admin user
        
    Returns:
        Test execution status
    """
    try:
        # This would need the actual agent instance
        # For now, return a placeholder response
        
        logger.info(
            "Agent tests initiated",
            test_type=test_type,
            include_crisis=include_crisis,
            include_safety=include_safety,
            include_edge_cases=include_edge_cases,
            requested_by=current_user.id
        )
        
        return {
            "message": "Agent tests initiated successfully",
            "test_type": test_type,
            "parameters": {
                "include_crisis": include_crisis,
                "include_safety": include_safety,
                "include_edge_cases": include_edge_cases
            },
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Test runner integration pending - this endpoint will execute comprehensive tests when agent instance is available"
        }
        
    except Exception as e:
        logger.error(f"Failed to run agent tests: {e}")
        raise HTTPException(status_code=500, detail="Failed to run agent tests")


@router.get("/types", summary="Get Feedback Types")
async def get_feedback_types() -> Dict[str, Any]:
    """
    Get available feedback types and ratings.
    
    Returns:
        Available feedback types and rating scales
    """
    return {
        "feedback_types": [
            {
                "value": feedback_type.value,
                "name": feedback_type.value.replace("_", " ").title(),
                "description": f"Feedback about {feedback_type.value.replace('_', ' ')}"
            }
            for feedback_type in FeedbackType
        ],
        "rating_scale": [
            {
                "value": rating.value,
                "name": rating.name.replace("_", " ").title(),
                "description": f"Rating level {rating.value}"
            }
            for rating in FeedbackRating
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
