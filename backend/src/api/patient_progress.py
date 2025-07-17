"""
Patient Progress API endpoints for healthcare-compliant dashboard.

This module provides REST API endpoints for patient progress tracking,
session analytics, and provider oversight functionality.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from ..database import get_db_session
from ..models.patient_progress import (
    PatientSession, ProgressMetric, TreatmentMilestone, SessionAlert, ProviderNote,
    PatientSessionCreate, PatientSessionResponse, ProgressMetricCreate, ProgressMetricResponse,
    TreatmentMilestoneCreate, TreatmentMilestoneResponse, SessionAlertResponse,
    PatientProgressSummary, MoodLevel, SessionType, ProgressMetricType, AlertLevel
)
from ..models.database import User
from .auth import get_current_user
from ..utils.encryption import encrypt_data, decrypt_data
from ..utils.analytics import calculate_trend, calculate_wellness_score
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/patient-progress", tags=["Patient Progress"])


# Session Management Endpoints

@router.post("/sessions", response_model=PatientSessionResponse)
async def create_patient_session(
    session_data: PatientSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new patient session."""
    try:
        # Create new session record
        db_session = PatientSession(
            user_id=current_user.id,
            session_id=session_data.session_id,
            session_type=session_data.session_type.value,
            start_time=session_data.start_time,
            pre_session_mood=session_data.pre_session_mood.value if session_data.pre_session_mood else None,
            anxiety_level=session_data.anxiety_level,
            depression_indicators=session_data.depression_indicators,
            goals_discussed=session_data.goals_discussed
        )
        
        db.add(db_session)
        await db.commit()
        await db.refresh(db_session)
        
        logger.info(f"Created patient session {db_session.id} for user {current_user.id}")
        return PatientSessionResponse.model_validate(db_session)
        
    except Exception as e:
        logger.error(f"Error creating patient session: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create patient session"
        )


@router.put("/sessions/{session_id}/complete")
async def complete_patient_session(
    session_id: str,
    post_session_mood: Optional[MoodLevel] = None,
    engagement_score: Optional[float] = None,
    clinical_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Complete a patient session with post-session data."""
    try:
        # Find the session
        result = await db.execute(
            select(PatientSession).where(
                and_(
                    PatientSession.session_id == session_id,
                    PatientSession.user_id == current_user.id
                )
            )
        )
        db_session = result.scalar_one_or_none()
        
        if not db_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Update session with completion data
        db_session.end_time = datetime.utcnow()
        if db_session.start_time:
            duration = db_session.end_time - db_session.start_time
            db_session.duration_minutes = int(duration.total_seconds() / 60)
        
        if post_session_mood:
            db_session.post_session_mood = post_session_mood.value
            
            # Calculate mood improvement if pre-session mood exists
            if db_session.pre_session_mood:
                mood_values = {
                    MoodLevel.VERY_LOW: 1, MoodLevel.LOW: 2, MoodLevel.NEUTRAL: 3,
                    MoodLevel.GOOD: 4, MoodLevel.VERY_GOOD: 5
                }
                pre_value = mood_values.get(MoodLevel(db_session.pre_session_mood), 3)
                post_value = mood_values.get(post_session_mood, 3)
                db_session.mood_improvement = post_value - pre_value
        
        if engagement_score is not None:
            db_session.engagement_score = max(0.0, min(1.0, engagement_score))
        
        if clinical_notes:
            db_session.encrypted_clinical_notes = encrypt_data(clinical_notes)
        
        await db.commit()
        await db.refresh(db_session)
        
        logger.info(f"Completed patient session {session_id} for user {current_user.id}")
        return PatientSessionResponse.model_validate(db_session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing patient session: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete patient session"
        )


@router.get("/sessions", response_model=List[PatientSessionResponse])
async def get_patient_sessions(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    session_type: Optional[SessionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get patient sessions with filtering options."""
    try:
        query = select(PatientSession).where(PatientSession.user_id == current_user.id)
        
        # Apply filters
        if session_type:
            query = query.where(PatientSession.session_type == session_type.value)
        
        if start_date:
            query = query.where(PatientSession.start_time >= start_date)
        
        if end_date:
            query = query.where(PatientSession.start_time <= end_date)
        
        # Order by most recent first
        query = query.order_by(desc(PatientSession.start_time))
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        return [PatientSessionResponse.model_validate(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Error fetching patient sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch patient sessions"
        )


# Progress Metrics Endpoints

@router.post("/metrics", response_model=ProgressMetricResponse)
async def create_progress_metric(
    metric_data: ProgressMetricCreate,
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new progress metric."""
    try:
        # Find session if provided
        db_session_id = None
        if session_id:
            result = await db.execute(
                select(PatientSession.id).where(
                    and_(
                        PatientSession.session_id == session_id,
                        PatientSession.user_id == current_user.id
                    )
                )
            )
            db_session_id = result.scalar_one_or_none()
        
        # Create progress metric
        db_metric = ProgressMetric(
            user_id=current_user.id,
            session_id=db_session_id,
            metric_type=metric_data.metric_type.value,
            metric_value=metric_data.metric_value,
            metric_scale_min=metric_data.metric_scale_min,
            metric_scale_max=metric_data.metric_scale_max,
            measurement_context=metric_data.measurement_context,
            notes=metric_data.notes,
            recorded_by=metric_data.recorded_by
        )
        
        db.add(db_metric)
        await db.commit()
        await db.refresh(db_metric)
        
        logger.info(f"Created progress metric {db_metric.id} for user {current_user.id}")
        return ProgressMetricResponse.model_validate(db_metric)
        
    except Exception as e:
        logger.error(f"Error creating progress metric: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create progress metric"
        )


@router.get("/metrics", response_model=List[ProgressMetricResponse])
async def get_progress_metrics(
    metric_type: Optional[ProgressMetricType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get progress metrics with filtering options."""
    try:
        query = select(ProgressMetric).where(ProgressMetric.user_id == current_user.id)
        
        # Apply filters
        if metric_type:
            query = query.where(ProgressMetric.metric_type == metric_type.value)
        
        if start_date:
            query = query.where(ProgressMetric.recorded_at >= start_date)
        
        if end_date:
            query = query.where(ProgressMetric.recorded_at <= end_date)
        
        # Order by most recent first
        query = query.order_by(desc(ProgressMetric.recorded_at)).limit(limit)
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        return [ProgressMetricResponse.model_validate(metric) for metric in metrics]
        
    except Exception as e:
        logger.error(f"Error fetching progress metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch progress metrics"
        )


# Treatment Milestones Endpoints

@router.post("/milestones", response_model=TreatmentMilestoneResponse)
async def create_treatment_milestone(
    milestone_data: TreatmentMilestoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new treatment milestone."""
    try:
        db_milestone = TreatmentMilestone(
            user_id=current_user.id,
            milestone_type=milestone_data.milestone_type,
            title=milestone_data.title,
            description=milestone_data.description,
            target_date=milestone_data.target_date,
            priority_level=milestone_data.priority_level
        )
        
        db.add(db_milestone)
        await db.commit()
        await db.refresh(db_milestone)
        
        logger.info(f"Created treatment milestone {db_milestone.id} for user {current_user.id}")
        return TreatmentMilestoneResponse.model_validate(db_milestone)
        
    except Exception as e:
        logger.error(f"Error creating treatment milestone: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create treatment milestone"
        )


@router.get("/milestones", response_model=List[TreatmentMilestoneResponse])
async def get_treatment_milestones(
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get treatment milestones."""
    try:
        query = select(TreatmentMilestone).where(TreatmentMilestone.user_id == current_user.id)
        
        if active_only:
            query = query.where(TreatmentMilestone.is_active == True)
        
        query = query.order_by(desc(TreatmentMilestone.priority_level), asc(TreatmentMilestone.target_date))
        
        result = await db.execute(query)
        milestones = result.scalars().all()
        
        return [TreatmentMilestoneResponse.model_validate(milestone) for milestone in milestones]
        
    except Exception as e:
        logger.error(f"Error fetching treatment milestones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch treatment milestones"
        )


# Session Alerts Endpoints

@router.get("/alerts", response_model=List[SessionAlertResponse])
async def get_session_alerts(
    unresolved_only: bool = Query(True),
    alert_level: Optional[AlertLevel] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get session alerts for the current user."""
    try:
        query = select(SessionAlert).where(SessionAlert.user_id == current_user.id)

        if unresolved_only:
            query = query.where(SessionAlert.is_resolved == False)

        if alert_level:
            query = query.where(SessionAlert.alert_level == alert_level.value)

        query = query.order_by(desc(SessionAlert.created_at))

        result = await db.execute(query)
        alerts = result.scalars().all()

        return [SessionAlertResponse.model_validate(alert) for alert in alerts]

    except Exception as e:
        logger.error(f"Error fetching session alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch session alerts"
        )


# Progress Summary Endpoint

@router.get("/summary", response_model=PatientProgressSummary)
async def get_patient_progress_summary(
    days_back: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get comprehensive patient progress summary."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days_back)

        # Get session statistics
        session_stats = await db.execute(
            select(
                func.count(PatientSession.id).label('total_sessions'),
                func.avg(PatientSession.duration_minutes).label('avg_duration'),
                func.max(PatientSession.start_time).label('last_session')
            ).where(
                and_(
                    PatientSession.user_id == current_user.id,
                    PatientSession.start_time >= start_date
                )
            )
        )
        stats = session_stats.first()

        # Get active alerts count
        alert_count = await db.execute(
            select(func.count(SessionAlert.id)).where(
                and_(
                    SessionAlert.user_id == current_user.id,
                    SessionAlert.is_resolved == False
                )
            )
        )
        active_alerts = alert_count.scalar() or 0

        # Get recent milestones
        milestones_result = await db.execute(
            select(TreatmentMilestone).where(
                and_(
                    TreatmentMilestone.user_id == current_user.id,
                    TreatmentMilestone.is_active == True
                )
            ).order_by(desc(TreatmentMilestone.created_at)).limit(5)
        )
        recent_milestones = [
            TreatmentMilestoneResponse.model_validate(m)
            for m in milestones_result.scalars().all()
        ]

        # Get progress metrics grouped by type
        metrics_result = await db.execute(
            select(ProgressMetric).where(
                and_(
                    ProgressMetric.user_id == current_user.id,
                    ProgressMetric.recorded_at >= start_date
                )
            ).order_by(ProgressMetric.recorded_at)
        )

        progress_metrics = {}
        mood_values = []
        engagement_values = []

        for metric in metrics_result.scalars().all():
            metric_type = metric.metric_type
            if metric_type not in progress_metrics:
                progress_metrics[metric_type] = []
            progress_metrics[metric_type].append(metric.metric_value)

            # Collect specific metrics for trend analysis
            if metric_type == ProgressMetricType.MOOD_SCORE.value:
                mood_values.append(metric.metric_value)
            elif metric_type == ProgressMetricType.ENGAGEMENT_SCORE.value:
                engagement_values.append(metric.metric_value)

        # Calculate trends and wellness score
        mood_trend = calculate_trend(mood_values) if mood_values else None
        engagement_trend = calculate_trend(engagement_values) if engagement_values else None
        wellness_score = calculate_wellness_score(progress_metrics)

        return PatientProgressSummary(
            user_id=str(current_user.id),
            total_sessions=stats.total_sessions or 0,
            avg_session_duration=float(stats.avg_duration) if stats.avg_duration else None,
            current_mood_trend=mood_trend,
            wellness_score=wellness_score,
            engagement_trend=engagement_trend,
            active_alerts=active_alerts,
            recent_milestones=recent_milestones,
            progress_metrics=progress_metrics,
            last_session_date=stats.last_session,
            next_recommended_session=None  # This could be calculated based on treatment plan
        )

    except Exception as e:
        logger.error(f"Error generating progress summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate progress summary"
        )


# Provider Oversight Endpoints (for healthcare providers)

@router.get("/provider/patients", response_model=List[Dict[str, Any]])
async def get_provider_patients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get patient list for healthcare providers."""
    # This would require additional role-based access control
    # For now, returning empty list as placeholder
    return []


@router.get("/provider/alerts", response_model=List[SessionAlertResponse])
async def get_provider_alerts(
    alert_level: Optional[AlertLevel] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get alerts across all patients for healthcare providers."""
    # This would require additional role-based access control
    # For now, returning empty list as placeholder
    return []
