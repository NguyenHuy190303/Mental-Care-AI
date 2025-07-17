"""
Monitoring API endpoints for Mental Health Agent.
Provides health checks, metrics, and system status information.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from ..monitoring import health_monitor, error_handler
from ..monitoring.logging_config import get_logger
from .auth import get_current_user
from ..models.database import User

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
logger = get_logger("api.monitoring")

# Simple admin check function
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin privileges."""
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


@router.get("/health", summary="System Health Check")
async def health_check() -> Dict[str, Any]:
    """
    Perform a comprehensive system health check.
    
    Returns:
        Health status of all system components
    """
    try:
        health_report = await health_monitor.perform_health_check()
        
        # Determine HTTP status code based on health
        status_code = 200
        if health_report['overall_status'] == 'critical':
            status_code = 503  # Service Unavailable
        elif health_report['overall_status'] == 'unhealthy':
            status_code = 503
        elif health_report['overall_status'] == 'degraded':
            status_code = 200  # Still available but degraded
        
        return JSONResponse(
            content=health_report,
            status_code=status_code
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                'overall_status': 'critical',
                'error': 'Health check system failure',
                'timestamp': datetime.utcnow().isoformat()
            },
            status_code=503
        )


@router.get("/health/summary", summary="Health Summary")
async def health_summary() -> Dict[str, Any]:
    """
    Get a summary of system health and availability.
    
    Returns:
        Health summary with availability metrics
    """
    try:
        summary = health_monitor.get_health_summary()
        return summary
    except Exception as e:
        logger.error(f"Failed to get health summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health summary")


@router.get("/metrics", summary="System Metrics")
async def get_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours of metrics to retrieve"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get system metrics for the specified time period.
    
    Args:
        hours: Number of hours of metrics to retrieve (1-168)
        current_user: Current authenticated admin user
        
    Returns:
        System metrics including CPU, memory, disk usage
    """
    try:
        metrics_history = health_monitor.get_metrics_history(hours=hours)
        
        # Calculate aggregated metrics
        if metrics_history:
            avg_cpu = sum(m['cpu_usage'] for m in metrics_history) / len(metrics_history)
            avg_memory = sum(m['memory_usage'] for m in metrics_history) / len(metrics_history)
            avg_disk = sum(m['disk_usage'] for m in metrics_history) / len(metrics_history)
            max_cpu = max(m['cpu_usage'] for m in metrics_history)
            max_memory = max(m['memory_usage'] for m in metrics_history)
        else:
            avg_cpu = avg_memory = avg_disk = max_cpu = max_memory = 0
        
        return {
            'period_hours': hours,
            'data_points': len(metrics_history),
            'aggregated_metrics': {
                'avg_cpu_usage': round(avg_cpu, 2),
                'avg_memory_usage': round(avg_memory, 2),
                'avg_disk_usage': round(avg_disk, 2),
                'max_cpu_usage': round(max_cpu, 2),
                'max_memory_usage': round(max_memory, 2)
            },
            'metrics_history': metrics_history
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/errors", summary="Error Statistics")
async def get_error_stats(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get error statistics and metrics.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        Error statistics and metrics
    """
    try:
        error_metrics = error_handler.get_error_metrics()
        
        return {
            'error_metrics': error_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get error statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve error statistics")


@router.get("/status", summary="System Status")
async def system_status() -> Dict[str, Any]:
    """
    Get overall system status for public consumption.
    
    Returns:
        Basic system status information
    """
    try:
        # Get basic health info without sensitive details
        health_summary = health_monitor.get_health_summary()
        
        # Simplified status for public consumption
        public_status = {
            'status': health_summary.get('current_status', 'unknown'),
            'availability': health_summary.get('availability_percent', 0),
            'last_updated': health_summary.get('last_check', datetime.utcnow().isoformat()),
            'services': {
                'api': 'operational',
                'ai_model': 'operational',
                'database': 'operational'
            }
        }
        
        # Update service status based on component health
        if 'components' in health_summary:
            components = health_summary['components']
            
            if 'database' in components:
                db_status = components['database']['status']
                public_status['services']['database'] = 'operational' if db_status == 'healthy' else 'degraded'
            
            if 'ai_model' in components:
                ai_status = components['ai_model']['status']
                public_status['services']['ai_model'] = 'operational' if ai_status == 'healthy' else 'degraded'
        
        return public_status
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return {
            'status': 'unknown',
            'availability': 0,
            'last_updated': datetime.utcnow().isoformat(),
            'services': {
                'api': 'unknown',
                'ai_model': 'unknown',
                'database': 'unknown'
            }
        }


@router.post("/alerts/test", summary="Test Alert System")
async def test_alerts(
    alert_type: str = Query(..., description="Type of alert to test"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Test the alerting system.
    
    Args:
        alert_type: Type of alert to test (health, error, security)
        current_user: Current authenticated admin user
        
    Returns:
        Test result
    """
    try:
        if alert_type == "health":
            # Simulate a health alert
            from ..monitoring.error_handler import MentalHealthError, ErrorSeverity, ErrorCategory
            
            test_error = MentalHealthError(
                message="Test health alert",
                error_code="TEST_HEALTH_ALERT",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH
            )
            
            await error_handler._send_alert(test_error, None)
            
        elif alert_type == "error":
            # Simulate an error alert
            logger.critical("Test error alert triggered by admin", user_id=current_user.id)
            
        elif alert_type == "security":
            # Simulate a security alert
            logger.critical(
                "Test security alert triggered by admin",
                user_id=current_user.id,
                event_type="security_test",
                alert_level="high"
            )
            
        else:
            raise HTTPException(status_code=400, detail="Invalid alert type")
        
        return {
            'message': f'Test {alert_type} alert sent successfully',
            'timestamp': datetime.utcnow().isoformat(),
            'triggered_by': current_user.id
        }
        
    except Exception as e:
        logger.error(f"Failed to test alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to test alert system")


@router.get("/logs/recent", summary="Recent Log Entries")
async def get_recent_logs(
    level: Optional[str] = Query(None, description="Log level filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of log entries to retrieve"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get recent log entries (admin only).
    
    Args:
        level: Log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        limit: Number of log entries to retrieve
        current_user: Current authenticated admin user
        
    Returns:
        Recent log entries
    """
    try:
        # This would typically read from log files or a log aggregation system
        # For now, return a placeholder response
        
        return {
            'message': 'Log retrieval not implemented yet',
            'note': 'This endpoint would return recent log entries in production',
            'filters': {
                'level': level,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")


@router.get("/performance", summary="Performance Metrics")
async def get_performance_metrics(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get performance metrics for the system.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        Performance metrics
    """
    try:
        # Get latest health check for response times
        health_summary = health_monitor.get_health_summary()
        
        performance_data = {
            'response_times': {},
            'throughput': {
                'requests_per_minute': 0,  # Would be calculated from actual metrics
                'successful_requests': 0,
                'failed_requests': 0
            },
            'resource_usage': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Extract response times from health check
        if 'components' in health_summary:
            for component, data in health_summary['components'].items():
                if 'response_time' in data and data['response_time']:
                    performance_data['response_times'][component] = data['response_time']
        
        # Extract resource usage
        if 'system_metrics' in health_summary:
            performance_data['resource_usage'] = health_summary['system_metrics']
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


@router.post("/maintenance", summary="Maintenance Mode")
async def toggle_maintenance_mode(
    enable: bool = Query(..., description="Enable or disable maintenance mode"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Toggle maintenance mode for the system.
    
    Args:
        enable: Whether to enable or disable maintenance mode
        current_user: Current authenticated admin user
        
    Returns:
        Maintenance mode status
    """
    try:
        # This would typically set a flag in Redis or database
        # For now, just log the action
        
        action = "enabled" if enable else "disabled"
        logger.info(
            f"Maintenance mode {action} by admin",
            user_id=current_user.id,
            maintenance_mode=enable,
            event_type="maintenance_mode_change"
        )
        
        return {
            'maintenance_mode': enable,
            'message': f'Maintenance mode {action}',
            'changed_by': current_user.id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to toggle maintenance mode: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle maintenance mode")
