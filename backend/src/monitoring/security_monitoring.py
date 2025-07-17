"""
Advanced Security Monitoring and Alerting System
Monitors for security threats, crisis intervention failures, and anomalous behavior.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import hashlib

from ..monitoring.logging_config import get_logger

logger = get_logger("monitoring.security")


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(str, Enum):
    """Types of security alerts."""
    CRISIS_INTERVENTION_FAILURE = "crisis_intervention_failure"
    DATA_BREACH_INDICATOR = "data_breach_indicator"
    UNUSUAL_USER_BEHAVIOR = "unusual_user_behavior"
    AI_MODEL_DEGRADATION = "ai_model_degradation"
    AUTHENTICATION_ANOMALY = "authentication_anomaly"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    PROMPT_INJECTION_ATTEMPT = "prompt_injection_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SYSTEM_PERFORMANCE = "system_performance"
    COMPLIANCE_VIOLATION = "compliance_violation"


@dataclass
class SecurityAlert:
    """Security alert data structure."""
    
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None


class SecurityMonitor:
    """Advanced security monitoring system."""
    
    def __init__(self):
        """Initialize security monitor."""
        self.active_alerts = {}
        self.alert_history = []
        self.user_behavior_baselines = {}
        self.system_metrics_history = []
        
        # Thresholds for various alerts
        self.thresholds = {
            'crisis_response_time': 5.0,  # seconds
            'failed_auth_attempts': 5,    # per hour
            'unusual_access_pattern': 0.8, # confidence threshold
            'ai_response_time': 10.0,     # seconds
            'error_rate': 0.05,           # 5%
            'memory_usage': 0.85,         # 85%
            'cpu_usage': 0.80,            # 80%
        }
    
    async def monitor_crisis_intervention(
        self,
        user_id: str,
        crisis_detected: bool,
        response_time: float,
        intervention_successful: bool,
        metadata: Dict[str, Any]
    ):
        """Monitor crisis intervention effectiveness."""
        try:
            # Check for crisis intervention failures
            if crisis_detected and not intervention_successful:
                await self._create_alert(
                    AlertType.CRISIS_INTERVENTION_FAILURE,
                    AlertSeverity.CRITICAL,
                    "Crisis Intervention Failed",
                    f"Crisis detected for user {user_id} but intervention failed",
                    user_id=user_id,
                    metadata={
                        'response_time': response_time,
                        'crisis_metadata': metadata
                    }
                )
            
            # Check for slow crisis response
            if crisis_detected and response_time > self.thresholds['crisis_response_time']:
                await self._create_alert(
                    AlertType.SYSTEM_PERFORMANCE,
                    AlertSeverity.HIGH,
                    "Slow Crisis Response",
                    f"Crisis response took {response_time:.2f}s (threshold: {self.thresholds['crisis_response_time']}s)",
                    user_id=user_id,
                    metadata={'response_time': response_time}
                )
            
            # Log successful interventions for monitoring
            if crisis_detected and intervention_successful:
                logger.info("Crisis intervention successful",
                          user_id=user_id,
                          response_time=response_time)
                
        except Exception as e:
            logger.error(f"Crisis intervention monitoring failed: {e}")
    
    async def monitor_user_behavior(
        self,
        user_id: str,
        action: str,
        metadata: Dict[str, Any]
    ):
        """Monitor for unusual user behavior patterns."""
        try:
            # Get or create user baseline
            if user_id not in self.user_behavior_baselines:
                self.user_behavior_baselines[user_id] = {
                    'actions': {},
                    'session_patterns': {},
                    'last_activity': None,
                    'risk_score': 0.0
                }
            
            baseline = self.user_behavior_baselines[user_id]
            current_time = datetime.utcnow()
            
            # Update action counts
            if action not in baseline['actions']:
                baseline['actions'][action] = {'count': 0, 'last_seen': current_time}
            
            baseline['actions'][action]['count'] += 1
            baseline['actions'][action]['last_seen'] = current_time
            
            # Detect unusual patterns
            anomaly_score = await self._calculate_behavior_anomaly(user_id, action, metadata)
            
            if anomaly_score > self.thresholds['unusual_access_pattern']:
                await self._create_alert(
                    AlertType.UNUSUAL_USER_BEHAVIOR,
                    AlertSeverity.MEDIUM,
                    "Unusual User Behavior Detected",
                    f"User {user_id} showing unusual behavior pattern",
                    user_id=user_id,
                    metadata={
                        'action': action,
                        'anomaly_score': anomaly_score,
                        'behavior_metadata': metadata
                    }
                )
            
            baseline['last_activity'] = current_time
            
        except Exception as e:
            logger.error(f"User behavior monitoring failed: {e}")
    
    async def monitor_authentication(
        self,
        user_id: Optional[str],
        auth_type: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        metadata: Dict[str, Any]
    ):
        """Monitor authentication events for anomalies."""
        try:
            # Track failed authentication attempts
            if not success:
                failed_key = f"failed_auth:{ip_address}"
                
                # Count recent failures
                recent_failures = await self._count_recent_events(
                    failed_key,
                    timedelta(hours=1)
                )
                
                if recent_failures >= self.thresholds['failed_auth_attempts']:
                    await self._create_alert(
                        AlertType.AUTHENTICATION_ANOMALY,
                        AlertSeverity.HIGH,
                        "Multiple Failed Authentication Attempts",
                        f"IP {ip_address} has {recent_failures} failed auth attempts in the last hour",
                        metadata={
                            'ip_address': ip_address,
                            'user_agent': user_agent,
                            'failed_attempts': recent_failures
                        }
                    )
            
            # Monitor for unusual login patterns
            if success and user_id:
                await self._check_login_anomalies(user_id, ip_address, user_agent, metadata)
                
        except Exception as e:
            logger.error(f"Authentication monitoring failed: {e}")
    
    async def monitor_ai_model_performance(
        self,
        model_name: str,
        response_time: float,
        error_occurred: bool,
        quality_score: Optional[float] = None,
        metadata: Dict[str, Any] = None
    ):
        """Monitor AI model performance and degradation."""
        try:
            # Check response time
            if response_time > self.thresholds['ai_response_time']:
                await self._create_alert(
                    AlertType.AI_MODEL_DEGRADATION,
                    AlertSeverity.MEDIUM,
                    "AI Model Slow Response",
                    f"Model {model_name} response time: {response_time:.2f}s",
                    metadata={
                        'model_name': model_name,
                        'response_time': response_time,
                        'threshold': self.thresholds['ai_response_time']
                    }
                )
            
            # Check for errors
            if error_occurred:
                error_rate = await self._calculate_model_error_rate(model_name)
                
                if error_rate > self.thresholds['error_rate']:
                    await self._create_alert(
                        AlertType.AI_MODEL_DEGRADATION,
                        AlertSeverity.HIGH,
                        "High AI Model Error Rate",
                        f"Model {model_name} error rate: {error_rate:.2%}",
                        metadata={
                            'model_name': model_name,
                            'error_rate': error_rate,
                            'threshold': self.thresholds['error_rate']
                        }
                    )
            
            # Check quality degradation
            if quality_score is not None and quality_score < 0.7:
                await self._create_alert(
                    AlertType.AI_MODEL_DEGRADATION,
                    AlertSeverity.MEDIUM,
                    "AI Model Quality Degradation",
                    f"Model {model_name} quality score: {quality_score:.2f}",
                    metadata={
                        'model_name': model_name,
                        'quality_score': quality_score
                    }
                )
                
        except Exception as e:
            logger.error(f"AI model monitoring failed: {e}")
    
    async def monitor_data_access(
        self,
        user_id: str,
        data_type: str,
        operation: str,
        sensitive_data: bool = False,
        metadata: Dict[str, Any] = None
    ):
        """Monitor data access for potential breaches."""
        try:
            # Monitor sensitive data access
            if sensitive_data:
                access_pattern = await self._analyze_data_access_pattern(
                    user_id, data_type, operation
                )
                
                if access_pattern['suspicious']:
                    await self._create_alert(
                        AlertType.DATA_BREACH_INDICATOR,
                        AlertSeverity.HIGH,
                        "Suspicious Data Access Pattern",
                        f"User {user_id} showing suspicious access to {data_type}",
                        user_id=user_id,
                        metadata={
                            'data_type': data_type,
                            'operation': operation,
                            'pattern_analysis': access_pattern,
                            'access_metadata': metadata
                        }
                    )
            
            # Log all sensitive data access
            logger.info("Sensitive data access",
                       user_id=user_id,
                       data_type=data_type,
                       operation=operation,
                       sensitive=sensitive_data)
                       
        except Exception as e:
            logger.error(f"Data access monitoring failed: {e}")
    
    async def monitor_system_resources(
        self,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float,
        network_io: Dict[str, float]
    ):
        """Monitor system resource usage."""
        try:
            # Check CPU usage
            if cpu_usage > self.thresholds['cpu_usage']:
                await self._create_alert(
                    AlertType.SYSTEM_PERFORMANCE,
                    AlertSeverity.MEDIUM,
                    "High CPU Usage",
                    f"CPU usage: {cpu_usage:.1%}",
                    metadata={'cpu_usage': cpu_usage}
                )
            
            # Check memory usage
            if memory_usage > self.thresholds['memory_usage']:
                await self._create_alert(
                    AlertType.SYSTEM_PERFORMANCE,
                    AlertSeverity.MEDIUM,
                    "High Memory Usage",
                    f"Memory usage: {memory_usage:.1%}",
                    metadata={'memory_usage': memory_usage}
                )
            
            # Store metrics for trend analysis
            self.system_metrics_history.append({
                'timestamp': datetime.utcnow(),
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_io': network_io
            })
            
            # Keep only last 24 hours of metrics
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.system_metrics_history = [
                metric for metric in self.system_metrics_history
                if metric['timestamp'] > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"System resource monitoring failed: {e}")
    
    async def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create and process security alert."""
        alert_id = hashlib.sha256(
            f"{alert_type}:{title}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            organization_id=organization_id,
            metadata=metadata or {}
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Send notifications based on severity
        await self._send_alert_notification(alert)
        
        # Log alert
        logger.warning(f"Security alert created: {title}",
                      alert_id=alert_id,
                      alert_type=alert_type.value,
                      severity=severity.value,
                      user_id=user_id)
    
    async def _send_alert_notification(self, alert: SecurityAlert):
        """Send alert notification to appropriate channels."""
        try:
            # For CRITICAL alerts, send immediate notifications
            if alert.severity == AlertSeverity.CRITICAL:
                # Send to emergency response team
                await self._send_emergency_notification(alert)
            
            # Send to security team for HIGH and above
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                await self._send_security_team_notification(alert)
            
            # Log all alerts to monitoring system
            await self._send_to_monitoring_system(alert)
            
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
    
    async def _send_emergency_notification(self, alert: SecurityAlert):
        """Send emergency notification for critical alerts."""
        # Implementation would send to emergency channels
        # (Slack, PagerDuty, SMS, etc.)
        logger.critical(f"EMERGENCY ALERT: {alert.title}",
                       alert_id=alert.alert_id,
                       description=alert.description)
    
    async def _send_security_team_notification(self, alert: SecurityAlert):
        """Send notification to security team."""
        # Implementation would send to security team channels
        logger.error(f"SECURITY ALERT: {alert.title}",
                    alert_id=alert.alert_id,
                    description=alert.description)
    
    async def _send_to_monitoring_system(self, alert: SecurityAlert):
        """Send alert to monitoring system (Prometheus, etc.)."""
        # Implementation would send metrics to monitoring system
        pass
    
    async def _calculate_behavior_anomaly(
        self,
        user_id: str,
        action: str,
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate behavior anomaly score."""
        # Simplified anomaly detection
        # In production, use ML-based anomaly detection
        
        baseline = self.user_behavior_baselines[user_id]
        
        # Check for unusual time patterns
        current_hour = datetime.utcnow().hour
        if 'usual_hours' not in baseline:
            baseline['usual_hours'] = {}
        
        if current_hour not in baseline['usual_hours']:
            baseline['usual_hours'][current_hour] = 0
        baseline['usual_hours'][current_hour] += 1
        
        # Calculate anomaly based on time
        total_actions = sum(baseline['usual_hours'].values())
        hour_frequency = baseline['usual_hours'][current_hour] / total_actions
        
        # Low frequency = higher anomaly
        time_anomaly = 1.0 - hour_frequency
        
        return min(time_anomaly, 1.0)
    
    async def _count_recent_events(self, event_key: str, time_window: timedelta) -> int:
        """Count recent events for rate limiting."""
        # Implementation would use Redis or similar for distributed counting
        # For now, return a placeholder
        return 0
    
    async def _check_login_anomalies(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        metadata: Dict[str, Any]
    ):
        """Check for login anomalies."""
        # Implementation would check for:
        # - New IP addresses
        # - New devices/user agents
        # - Unusual geographic locations
        # - Time-based anomalies
        pass
    
    async def _calculate_model_error_rate(self, model_name: str) -> float:
        """Calculate AI model error rate."""
        # Implementation would calculate error rate from recent requests
        # For now, return a placeholder
        return 0.01
    
    async def _analyze_data_access_pattern(
        self,
        user_id: str,
        data_type: str,
        operation: str
    ) -> Dict[str, Any]:
        """Analyze data access patterns for suspicious activity."""
        # Implementation would analyze:
        # - Volume of data accessed
        # - Frequency of access
        # - Time patterns
        # - Data sensitivity
        
        return {
            'suspicious': False,
            'confidence': 0.0,
            'reasons': []
        }
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[SecurityAlert]:
        """Get active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    async def resolve_alert(self, alert_id: str, resolution_notes: str):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_notes = resolution_notes
            
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert.title}",
                       alert_id=alert_id,
                       resolution_notes=resolution_notes)


# Global security monitor instance
security_monitor = SecurityMonitor()
