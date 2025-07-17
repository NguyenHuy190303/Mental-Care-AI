"""
Advanced Analytics and Metrics Collection for Mental Health Agent
Comprehensive analytics system for user engagement, safety incidents, and system performance.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload

from ..database import get_db_session
from ..models.database import User, UserInteraction, FeedbackEntry, SafetyIncident
from ..monitoring.logging_config import get_logger

logger = get_logger("analytics.metrics")


class MetricType(str, Enum):
    """Types of metrics collected."""
    USER_ENGAGEMENT = "user_engagement"
    SAFETY_INCIDENT = "safety_incident"
    CONVERSATION_QUALITY = "conversation_quality"
    SYSTEM_PERFORMANCE = "system_performance"
    COMPLIANCE_AUDIT = "compliance_audit"
    RLHF_PERFORMANCE = "rlhf_performance"


class TimeRange(str, Enum):
    """Time range options for analytics."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class MetricPoint:
    """Individual metric data point."""
    
    metric_id: str
    metric_type: MetricType
    timestamp: datetime
    value: float
    dimensions: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report."""
    
    report_id: str
    time_range: TimeRange
    start_date: datetime
    end_date: datetime
    metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime


class AdvancedMetricsCollector:
    """Advanced metrics collection and analytics system."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metric_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def collect_user_engagement_metrics(
        self,
        time_range: TimeRange = TimeRange.DAY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Collect comprehensive user engagement metrics."""
        logger.info(f"Collecting user engagement metrics for {time_range.value}")
        
        if not start_date:
            start_date = self._get_start_date(time_range)
        if not end_date:
            end_date = datetime.utcnow()
        
        try:
            async with get_db_session() as session:
                # Active users
                active_users_query = select(func.count(func.distinct(UserInteraction.user_id))).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date
                    )
                )
                active_users = await session.scalar(active_users_query)
                
                # Total interactions
                total_interactions_query = select(func.count(UserInteraction.id)).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date
                    )
                )
                total_interactions = await session.scalar(total_interactions_query)
                
                # Average session length
                session_length_query = select(
                    func.avg(
                        func.extract('epoch', UserInteraction.updated_at - UserInteraction.created_at)
                    )
                ).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date,
                        UserInteraction.updated_at.isnot(None)
                    )
                )
                avg_session_length = await session.scalar(session_length_query) or 0
                
                # User retention (returning users)
                retention_query = select(
                    func.count(func.distinct(UserInteraction.user_id))
                ).where(
                    and_(
                        UserInteraction.user_id.in_(
                            select(UserInteraction.user_id).where(
                                UserInteraction.created_at < start_date
                            )
                        ),
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date
                    )
                )
                returning_users = await session.scalar(retention_query)
                
                # Peak usage hours
                hourly_usage_query = select(
                    func.extract('hour', UserInteraction.created_at).label('hour'),
                    func.count(UserInteraction.id).label('count')
                ).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date
                    )
                ).group_by(func.extract('hour', UserInteraction.created_at))
                
                hourly_usage_result = await session.execute(hourly_usage_query)
                hourly_usage = {int(row.hour): row.count for row in hourly_usage_result}
                
                # Most common interaction types
                interaction_types_query = select(
                    UserInteraction.input_type,
                    func.count(UserInteraction.id).label('count')
                ).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date
                    )
                ).group_by(UserInteraction.input_type)
                
                interaction_types_result = await session.execute(interaction_types_query)
                interaction_types = {row.input_type: row.count for row in interaction_types_result}
                
                return {
                    "active_users": active_users or 0,
                    "total_interactions": total_interactions or 0,
                    "avg_session_length_seconds": round(avg_session_length, 2),
                    "returning_users": returning_users or 0,
                    "retention_rate": round((returning_users / max(active_users, 1)) * 100, 2),
                    "interactions_per_user": round((total_interactions or 0) / max(active_users, 1), 2),
                    "hourly_usage_distribution": hourly_usage,
                    "interaction_types_distribution": interaction_types,
                    "time_range": time_range.value,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to collect user engagement metrics: {e}")
            return {"error": str(e)}
    
    async def collect_safety_incident_metrics(
        self,
        time_range: TimeRange = TimeRange.DAY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Collect safety incident and crisis intervention metrics."""
        logger.info(f"Collecting safety incident metrics for {time_range.value}")
        
        if not start_date:
            start_date = self._get_start_date(time_range)
        if not end_date:
            end_date = datetime.utcnow()
        
        try:
            async with get_db_session() as session:
                # Crisis interventions
                crisis_query = select(func.count(UserInteraction.id)).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date,
                        UserInteraction.metadata['crisis_detected'].astext.cast(text('boolean')) == True
                    )
                )
                crisis_interventions = await session.scalar(crisis_query) or 0
                
                # Safety warnings issued
                safety_warnings_query = select(func.count(UserInteraction.id)).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date,
                        UserInteraction.metadata['safety_warnings_count'].astext.cast(text('integer')) > 0
                    )
                )
                safety_warnings = await session.scalar(safety_warnings_query) or 0
                
                # Emergency resource provisions
                emergency_resources_query = select(func.count(UserInteraction.id)).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date,
                        UserInteraction.metadata['emergency_resources_provided'].astext.cast(text('boolean')) == True
                    )
                )
                emergency_resources = await session.scalar(emergency_resources_query) or 0
                
                # Safety feedback
                safety_feedback_query = select(func.count(FeedbackEntry.id)).where(
                    and_(
                        FeedbackEntry.created_at >= start_date,
                        FeedbackEntry.created_at <= end_date,
                        FeedbackEntry.feedback_type == 'safety'
                    )
                )
                safety_feedback_count = await session.scalar(safety_feedback_query) or 0
                
                # Crisis response time analysis
                crisis_response_times_query = select(
                    UserInteraction.metadata['response_time'].astext.cast(text('float'))
                ).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date,
                        UserInteraction.metadata['crisis_detected'].astext.cast(text('boolean')) == True,
                        UserInteraction.metadata['response_time'].isnot(None)
                    )
                )
                
                crisis_response_times_result = await session.execute(crisis_response_times_query)
                crisis_response_times = [row[0] for row in crisis_response_times_result if row[0] is not None]
                
                avg_crisis_response_time = sum(crisis_response_times) / len(crisis_response_times) if crisis_response_times else 0
                
                return {
                    "crisis_interventions": crisis_interventions,
                    "safety_warnings_issued": safety_warnings,
                    "emergency_resources_provided": emergency_resources,
                    "safety_feedback_reports": safety_feedback_count,
                    "avg_crisis_response_time_seconds": round(avg_crisis_response_time, 2),
                    "crisis_response_times_distribution": {
                        "under_2_seconds": len([t for t in crisis_response_times if t < 2]),
                        "2_to_5_seconds": len([t for t in crisis_response_times if 2 <= t < 5]),
                        "over_5_seconds": len([t for t in crisis_response_times if t >= 5])
                    },
                    "safety_incident_rate": round((crisis_interventions / max(1, await self._get_total_interactions(start_date, end_date))) * 100, 4),
                    "time_range": time_range.value,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to collect safety incident metrics: {e}")
            return {"error": str(e)}
    
    async def collect_conversation_quality_metrics(
        self,
        time_range: TimeRange = TimeRange.DAY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Collect conversation quality and satisfaction metrics."""
        logger.info(f"Collecting conversation quality metrics for {time_range.value}")
        
        if not start_date:
            start_date = self._get_start_date(time_range)
        if not end_date:
            end_date = datetime.utcnow()
        
        try:
            async with get_db_session() as session:
                # Average feedback ratings
                avg_rating_query = select(func.avg(FeedbackEntry.rating)).where(
                    and_(
                        FeedbackEntry.created_at >= start_date,
                        FeedbackEntry.created_at <= end_date,
                        FeedbackEntry.rating.isnot(None)
                    )
                )
                avg_rating = await session.scalar(avg_rating_query) or 0
                
                # Feedback distribution
                rating_distribution_query = select(
                    FeedbackEntry.rating,
                    func.count(FeedbackEntry.id).label('count')
                ).where(
                    and_(
                        FeedbackEntry.created_at >= start_date,
                        FeedbackEntry.created_at <= end_date,
                        FeedbackEntry.rating.isnot(None)
                    )
                ).group_by(FeedbackEntry.rating)
                
                rating_distribution_result = await session.execute(rating_distribution_query)
                rating_distribution = {row.rating: row.count for row in rating_distribution_result}
                
                # Conversation length analysis
                conversation_length_query = select(
                    func.char_length(UserInteraction.user_input).label('input_length'),
                    func.char_length(UserInteraction.agent_response).label('response_length')
                ).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date,
                        UserInteraction.user_input.isnot(None),
                        UserInteraction.agent_response.isnot(None)
                    )
                )
                
                conversation_lengths_result = await session.execute(conversation_length_query)
                conversation_lengths = [(row.input_length, row.response_length) for row in conversation_lengths_result]
                
                avg_input_length = sum(length[0] for length in conversation_lengths) / len(conversation_lengths) if conversation_lengths else 0
                avg_response_length = sum(length[1] for length in conversation_lengths) / len(conversation_lengths) if conversation_lengths else 0
                
                # Confidence score analysis
                confidence_scores_query = select(
                    UserInteraction.metadata['confidence_level'].astext.cast(text('float'))
                ).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date,
                        UserInteraction.metadata['confidence_level'].isnot(None)
                    )
                )
                
                confidence_scores_result = await session.execute(confidence_scores_query)
                confidence_scores = [row[0] for row in confidence_scores_result if row[0] is not None]
                
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                
                return {
                    "average_user_rating": round(avg_rating, 2),
                    "rating_distribution": rating_distribution,
                    "total_feedback_entries": sum(rating_distribution.values()),
                    "avg_input_length_chars": round(avg_input_length, 2),
                    "avg_response_length_chars": round(avg_response_length, 2),
                    "avg_confidence_score": round(avg_confidence, 3),
                    "high_confidence_responses": len([s for s in confidence_scores if s >= 0.8]),
                    "low_confidence_responses": len([s for s in confidence_scores if s < 0.5]),
                    "satisfaction_rate": round((len([r for r in rating_distribution.keys() if r >= 4]) / max(1, len(rating_distribution))) * 100, 2),
                    "time_range": time_range.value,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to collect conversation quality metrics: {e}")
            return {"error": str(e)}
    
    async def collect_rlhf_performance_metrics(
        self,
        time_range: TimeRange = TimeRange.WEEK,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Collect RLHF (Reinforcement Learning from Human Feedback) performance metrics."""
        logger.info(f"Collecting RLHF performance metrics for {time_range.value}")
        
        if not start_date:
            start_date = self._get_start_date(time_range)
        if not end_date:
            end_date = datetime.utcnow()
        
        try:
            from ..feedback.rlhf_processor import rlhf_processor
            
            # Get RLHF metrics
            rlhf_metrics = await rlhf_processor.get_rlhf_metrics(
                days=(end_date - start_date).days
            )
            
            # Additional analysis
            async with get_db_session() as session:
                # Feedback collection rate
                feedback_rate_query = select(
                    func.count(FeedbackEntry.id).label('feedback_count'),
                    func.count(func.distinct(FeedbackEntry.interaction_id)).label('interactions_with_feedback')
                ).where(
                    and_(
                        FeedbackEntry.created_at >= start_date,
                        FeedbackEntry.created_at <= end_date
                    )
                )
                
                feedback_rate_result = await session.execute(feedback_rate_query)
                feedback_rate_data = feedback_rate_result.fetchone()
                
                total_interactions = await self._get_total_interactions(start_date, end_date)
                feedback_collection_rate = (feedback_rate_data.interactions_with_feedback / max(1, total_interactions)) * 100
                
                return {
                    "rlhf_datapoints": rlhf_metrics.get("total_datapoints", 0),
                    "quality_distribution": rlhf_metrics.get("quality_distribution", {}),
                    "average_feedback_score": rlhf_metrics.get("average_feedback_score", 0),
                    "feedback_collection_rate": round(feedback_collection_rate, 2),
                    "total_feedback_entries": feedback_rate_data.feedback_count,
                    "interactions_with_feedback": feedback_rate_data.interactions_with_feedback,
                    "model_improvement_indicators": {
                        "high_quality_responses": rlhf_metrics.get("quality_distribution", {}).get("excellent", 0),
                        "low_quality_responses": rlhf_metrics.get("quality_distribution", {}).get("poor", 0) + rlhf_metrics.get("quality_distribution", {}).get("harmful", 0)
                    },
                    "time_range": time_range.value,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to collect RLHF performance metrics: {e}")
            return {"error": str(e)}
    
    async def generate_comprehensive_analytics_report(
        self,
        time_range: TimeRange = TimeRange.DAY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AnalyticsReport:
        """Generate comprehensive analytics report."""
        logger.info(f"Generating comprehensive analytics report for {time_range.value}")
        
        if not start_date:
            start_date = self._get_start_date(time_range)
        if not end_date:
            end_date = datetime.utcnow()
        
        try:
            # Collect all metrics
            user_engagement = await self.collect_user_engagement_metrics(time_range, start_date, end_date)
            safety_incidents = await self.collect_safety_incident_metrics(time_range, start_date, end_date)
            conversation_quality = await self.collect_conversation_quality_metrics(time_range, start_date, end_date)
            rlhf_performance = await self.collect_rlhf_performance_metrics(time_range, start_date, end_date)
            
            # Combine metrics
            metrics = {
                "user_engagement": user_engagement,
                "safety_incidents": safety_incidents,
                "conversation_quality": conversation_quality,
                "rlhf_performance": rlhf_performance
            }
            
            # Generate insights
            insights = self._generate_insights(metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics)
            
            return AnalyticsReport(
                report_id=str(uuid.uuid4()),
                time_range=time_range,
                start_date=start_date,
                end_date=end_date,
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to generate analytics report: {e}")
            raise
    
    def _get_start_date(self, time_range: TimeRange) -> datetime:
        """Get start date based on time range."""
        now = datetime.utcnow()
        
        if time_range == TimeRange.HOUR:
            return now - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            return now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            return now - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            return now - timedelta(days=30)
        elif time_range == TimeRange.QUARTER:
            return now - timedelta(days=90)
        elif time_range == TimeRange.YEAR:
            return now - timedelta(days=365)
        else:
            return now - timedelta(days=1)
    
    async def _get_total_interactions(self, start_date: datetime, end_date: datetime) -> int:
        """Get total interactions in time range."""
        try:
            async with get_db_session() as session:
                query = select(func.count(UserInteraction.id)).where(
                    and_(
                        UserInteraction.created_at >= start_date,
                        UserInteraction.created_at <= end_date
                    )
                )
                return await session.scalar(query) or 0
        except Exception:
            return 0
    
    def _generate_insights(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate insights from metrics."""
        insights = []
        
        try:
            user_engagement = metrics.get("user_engagement", {})
            safety_incidents = metrics.get("safety_incidents", {})
            conversation_quality = metrics.get("conversation_quality", {})
            
            # User engagement insights
            if user_engagement.get("retention_rate", 0) > 70:
                insights.append("High user retention rate indicates strong user satisfaction and engagement")
            elif user_engagement.get("retention_rate", 0) < 30:
                insights.append("Low user retention rate suggests need for improved user experience")
            
            # Safety insights
            if safety_incidents.get("avg_crisis_response_time_seconds", 0) < 2:
                insights.append("Excellent crisis response time - meeting safety standards")
            elif safety_incidents.get("avg_crisis_response_time_seconds", 0) > 5:
                insights.append("Crisis response time exceeds target - optimization needed")
            
            # Quality insights
            if conversation_quality.get("average_user_rating", 0) > 4:
                insights.append("High user satisfaction with conversation quality")
            elif conversation_quality.get("average_user_rating", 0) < 3:
                insights.append("User satisfaction below target - quality improvements needed")
            
            # Peak usage insights
            hourly_usage = user_engagement.get("hourly_usage_distribution", {})
            if hourly_usage:
                peak_hour = max(hourly_usage.keys(), key=lambda k: hourly_usage[k])
                insights.append(f"Peak usage occurs at hour {peak_hour} - consider resource scaling")
            
        except Exception as e:
            logger.warning(f"Error generating insights: {e}")
            insights.append("Unable to generate detailed insights due to data processing error")
        
        return insights
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations from metrics."""
        recommendations = []
        
        try:
            user_engagement = metrics.get("user_engagement", {})
            safety_incidents = metrics.get("safety_incidents", {})
            conversation_quality = metrics.get("conversation_quality", {})
            rlhf_performance = metrics.get("rlhf_performance", {})
            
            # User engagement recommendations
            if user_engagement.get("retention_rate", 0) < 50:
                recommendations.append("Implement user onboarding improvements and engagement features")
            
            if user_engagement.get("interactions_per_user", 0) < 3:
                recommendations.append("Develop strategies to encourage longer conversations and return visits")
            
            # Safety recommendations
            if safety_incidents.get("avg_crisis_response_time_seconds", 0) > 3:
                recommendations.append("Optimize crisis detection algorithms for faster response times")
            
            # Quality recommendations
            if conversation_quality.get("average_user_rating", 0) < 3.5:
                recommendations.append("Review and improve conversation quality through RLHF training")
            
            if conversation_quality.get("avg_confidence_score", 0) < 0.7:
                recommendations.append("Enhance knowledge base and improve model confidence scoring")
            
            # RLHF recommendations
            if rlhf_performance.get("feedback_collection_rate", 0) < 20:
                recommendations.append("Increase feedback collection through improved UX and incentives")
            
            # General recommendations
            recommendations.extend([
                "Continue monitoring safety metrics and crisis intervention effectiveness",
                "Regularly update knowledge base with latest mental health resources",
                "Conduct periodic compliance audits for GDPR and HIPAA requirements",
                "Implement A/B testing for conversation flow improvements"
            ])
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            recommendations.append("Review system metrics manually due to processing error")
        
        return recommendations


# Global metrics collector instance
metrics_collector = AdvancedMetricsCollector()
