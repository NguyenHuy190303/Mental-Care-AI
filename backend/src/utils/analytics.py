"""
Analytics utilities for patient progress tracking.

This module provides functions for calculating trends, wellness scores,
and other analytics for the patient progress dashboard.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def calculate_trend(values: List[float], min_points: int = 3) -> Optional[str]:
    """
    Calculate trend direction from a series of values.
    
    Args:
        values: List of numeric values in chronological order
        min_points: Minimum number of points required for trend calculation
        
    Returns:
        Trend direction: "improving", "declining", "stable", or None
    """
    if not values or len(values) < min_points:
        return None
    
    try:
        # Use linear regression to determine trend
        x = np.arange(len(values))
        y = np.array(values)
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Determine trend based on slope and statistical significance
        if p_value > 0.05:  # Not statistically significant
            return "stable"
        
        if slope > 0.1:  # Positive trend
            return "improving"
        elif slope < -0.1:  # Negative trend
            return "declining"
        else:
            return "stable"
            
    except Exception as e:
        logger.error(f"Error calculating trend: {e}")
        return None


def calculate_wellness_score(progress_metrics: Dict[str, List[float]]) -> Optional[float]:
    """
    Calculate overall wellness score from various progress metrics.
    
    Args:
        progress_metrics: Dictionary of metric types to value lists
        
    Returns:
        Wellness score between 0.0 and 10.0, or None if insufficient data
    """
    if not progress_metrics:
        return None
    
    try:
        weighted_scores = []
        weights = {
            'mood_score': 0.3,
            'anxiety_level': 0.25,  # Inverted - lower is better
            'depression_score': 0.25,  # Inverted - lower is better
            'engagement_score': 0.15,
            'coping_skills': 0.05
        }
        
        for metric_type, values in progress_metrics.items():
            if not values:
                continue
                
            # Get recent average (last 5 values or all if fewer)
            recent_values = values[-5:] if len(values) >= 5 else values
            avg_value = np.mean(recent_values)
            
            # Normalize and weight the score
            weight = weights.get(metric_type, 0.1)
            
            if metric_type in ['anxiety_level', 'depression_score']:
                # For these metrics, lower is better (invert scale)
                normalized_score = 10.0 - min(10.0, max(0.0, avg_value))
            else:
                # For these metrics, higher is better
                normalized_score = min(10.0, max(0.0, avg_value))
            
            weighted_scores.append(normalized_score * weight)
        
        if not weighted_scores:
            return None
        
        # Calculate final wellness score
        wellness_score = sum(weighted_scores) / sum(weights.values()) * len(weighted_scores)
        return round(min(10.0, max(0.0, wellness_score)), 1)
        
    except Exception as e:
        logger.error(f"Error calculating wellness score: {e}")
        return None


def calculate_engagement_metrics(session_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate engagement metrics from session data.
    
    Args:
        session_data: List of session dictionaries
        
    Returns:
        Dictionary of engagement metrics
    """
    if not session_data:
        return {}
    
    try:
        metrics = {
            'avg_session_duration': 0.0,
            'message_frequency': 0.0,
            'response_time': 0.0,
            'completion_rate': 0.0,
            'consistency_score': 0.0
        }
        
        durations = []
        message_counts = []
        response_times = []
        completed_sessions = 0
        
        for session in session_data:
            if session.get('duration_minutes'):
                durations.append(session['duration_minutes'])
            
            if session.get('message_count'):
                message_counts.append(session['message_count'])
            
            if session.get('avg_response_time_seconds'):
                response_times.append(session['avg_response_time_seconds'])
            
            if session.get('end_time'):
                completed_sessions += 1
        
        # Calculate metrics
        if durations:
            metrics['avg_session_duration'] = np.mean(durations)
        
        if message_counts:
            metrics['message_frequency'] = np.mean(message_counts)
        
        if response_times:
            metrics['response_time'] = np.mean(response_times)
        
        metrics['completion_rate'] = completed_sessions / len(session_data) * 100
        
        # Calculate consistency score based on session frequency
        if len(session_data) >= 2:
            session_dates = [
                datetime.fromisoformat(s['start_time'].replace('Z', '+00:00'))
                for s in session_data if s.get('start_time')
            ]
            if len(session_dates) >= 2:
                session_dates.sort()
                intervals = [
                    (session_dates[i] - session_dates[i-1]).days
                    for i in range(1, len(session_dates))
                ]
                # Lower variance in intervals = higher consistency
                if intervals:
                    variance = np.var(intervals)
                    metrics['consistency_score'] = max(0, 100 - variance * 2)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating engagement metrics: {e}")
        return {}


def detect_concerning_patterns(
    progress_metrics: Dict[str, List[float]],
    session_data: List[Dict[str, Any]],
    threshold_days: int = 7
) -> List[Dict[str, Any]]:
    """
    Detect concerning patterns that may require provider attention.
    
    Args:
        progress_metrics: Dictionary of metric types to value lists
        session_data: List of session dictionaries
        threshold_days: Number of days to look back for pattern detection
        
    Returns:
        List of concerning pattern alerts
    """
    alerts = []
    
    try:
        # Check for mood decline
        if 'mood_score' in progress_metrics:
            mood_values = progress_metrics['mood_score']
            if len(mood_values) >= 3:
                recent_mood = mood_values[-3:]
                if all(mood_values[i] > mood_values[i+1] for i in range(len(recent_mood)-1)):
                    alerts.append({
                        'type': 'mood_decline',
                        'severity': 'medium',
                        'description': 'Consistent mood decline detected over recent sessions',
                        'data': {'recent_values': recent_mood}
                    })
        
        # Check for increased anxiety
        if 'anxiety_level' in progress_metrics:
            anxiety_values = progress_metrics['anxiety_level']
            if anxiety_values:
                recent_avg = np.mean(anxiety_values[-5:]) if len(anxiety_values) >= 5 else np.mean(anxiety_values)
                if recent_avg >= 7.0:  # High anxiety threshold
                    alerts.append({
                        'type': 'high_anxiety',
                        'severity': 'high',
                        'description': f'Elevated anxiety levels detected (avg: {recent_avg:.1f}/10)',
                        'data': {'average_level': recent_avg}
                    })
        
        # Check for session engagement drop
        if session_data:
            recent_sessions = [
                s for s in session_data
                if s.get('start_time') and 
                datetime.fromisoformat(s['start_time'].replace('Z', '+00:00')) >= 
                datetime.utcnow() - timedelta(days=threshold_days)
            ]
            
            if len(recent_sessions) < len(session_data) * 0.3:  # Less than 30% of usual activity
                alerts.append({
                    'type': 'engagement_drop',
                    'severity': 'medium',
                    'description': 'Significant decrease in session engagement detected',
                    'data': {'recent_sessions': len(recent_sessions), 'total_sessions': len(session_data)}
                })
        
        # Check for crisis risk indicators
        crisis_indicators = 0
        if 'mood_score' in progress_metrics:
            recent_mood = progress_metrics['mood_score'][-1] if progress_metrics['mood_score'] else 5
            if recent_mood <= 2:
                crisis_indicators += 1
        
        if 'anxiety_level' in progress_metrics:
            recent_anxiety = progress_metrics['anxiety_level'][-1] if progress_metrics['anxiety_level'] else 5
            if recent_anxiety >= 8:
                crisis_indicators += 1
        
        if crisis_indicators >= 2:
            alerts.append({
                'type': 'crisis_risk',
                'severity': 'critical',
                'description': 'Multiple crisis risk indicators detected - immediate attention required',
                'data': {'indicators': crisis_indicators}
            })
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error detecting concerning patterns: {e}")
        return []


def calculate_progress_velocity(
    metric_values: List[float],
    time_points: List[datetime],
    target_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate the velocity of progress toward a target.
    
    Args:
        metric_values: List of metric values
        time_points: Corresponding timestamps
        target_value: Target value to reach (optional)
        
    Returns:
        Dictionary with velocity metrics
    """
    if len(metric_values) < 2 or len(metric_values) != len(time_points):
        return {}
    
    try:
        # Calculate rate of change
        time_diffs = [(time_points[i] - time_points[i-1]).days for i in range(1, len(time_points))]
        value_diffs = [metric_values[i] - metric_values[i-1] for i in range(1, len(metric_values))]
        
        # Average daily change
        daily_changes = [value_diffs[i] / max(1, time_diffs[i]) for i in range(len(time_diffs))]
        avg_daily_change = np.mean(daily_changes)
        
        result = {
            'avg_daily_change': avg_daily_change,
            'trend_direction': 'improving' if avg_daily_change > 0 else 'declining' if avg_daily_change < 0 else 'stable',
            'velocity_consistency': 1.0 - (np.std(daily_changes) / (abs(avg_daily_change) + 0.1))
        }
        
        # Calculate time to target if target is provided
        if target_value is not None and avg_daily_change != 0:
            current_value = metric_values[-1]
            days_to_target = (target_value - current_value) / avg_daily_change
            if days_to_target > 0:
                result['estimated_days_to_target'] = int(days_to_target)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating progress velocity: {e}")
        return {}


def generate_insights(
    progress_metrics: Dict[str, List[float]],
    session_data: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate actionable insights from patient data.
    
    Args:
        progress_metrics: Dictionary of metric types to value lists
        session_data: List of session dictionaries
        
    Returns:
        List of insight strings
    """
    insights = []
    
    try:
        # Analyze mood patterns
        if 'mood_score' in progress_metrics and progress_metrics['mood_score']:
            mood_trend = calculate_trend(progress_metrics['mood_score'])
            if mood_trend == 'improving':
                insights.append("Mood scores show consistent improvement - current strategies are effective")
            elif mood_trend == 'declining':
                insights.append("Mood scores indicate decline - consider adjusting treatment approach")
        
        # Analyze engagement
        engagement_metrics = calculate_engagement_metrics(session_data)
        if engagement_metrics.get('completion_rate', 0) < 70:
            insights.append("Session completion rate is low - consider shorter or more engaging sessions")
        
        if engagement_metrics.get('consistency_score', 0) > 80:
            insights.append("Excellent session consistency - maintaining regular engagement")
        
        # Analyze wellness score
        wellness_score = calculate_wellness_score(progress_metrics)
        if wellness_score and wellness_score >= 7.5:
            insights.append("Overall wellness score is strong - continue current treatment plan")
        elif wellness_score and wellness_score < 5.0:
            insights.append("Wellness score indicates need for intervention - consider treatment plan review")
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return []
