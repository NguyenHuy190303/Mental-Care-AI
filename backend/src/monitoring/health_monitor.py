"""
Health Monitoring System for Mental Health Agent
Provides comprehensive health checks, metrics collection, and system monitoring.
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import aioredis
import aiohttp

from ..database import get_db_session
from ..tools.chromadb_integration import ChromaDBManager

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class ComponentHealth:
    """Health status of a system component."""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        response_time: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.status = status
        self.response_time = response_time
        self.error_message = error_message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class SystemMetrics:
    """System performance metrics."""
    
    def __init__(self):
        self.cpu_usage = psutil.cpu_percent()
        self.memory_usage = psutil.virtual_memory().percent
        self.disk_usage = psutil.disk_usage('/').percent
        self.load_average = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        self.timestamp = datetime.utcnow()


class HealthMonitor:
    """Comprehensive health monitoring system."""
    
    def __init__(
        self,
        check_interval: int = 30,
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Interval between health checks in seconds
            alert_thresholds: Thresholds for alerting on metrics
        """
        self.check_interval = check_interval
        self.alert_thresholds = alert_thresholds or {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'response_time': 5.0,
            'error_rate': 0.05
        }
        
        self.health_history: List[Dict[str, Any]] = []
        self.metrics_history: List[SystemMetrics] = []
        self.last_check_time = None
        self.is_monitoring = False
        
        logger.info("Health monitor initialized")
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.is_monitoring:
            logger.warning("Health monitoring already running")
            return
        
        self.is_monitoring = True
        logger.info("Starting health monitoring")
        
        while self.is_monitoring:
            try:
                await self.perform_health_check()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.is_monitoring = False
        logger.info("Health monitoring stopped")
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        start_time = time.time()
        
        # Check all components
        component_checks = await asyncio.gather(
            self._check_database_health(),
            self._check_redis_health(),
            self._check_chromadb_health(),
            self._check_ai_model_health(),
            self._check_disk_space(),
            self._check_memory_usage(),
            return_exceptions=True
        )
        
        # Process results
        components = {}
        overall_status = HealthStatus.HEALTHY
        
        for check in component_checks:
            if isinstance(check, ComponentHealth):
                components[check.name] = {
                    'status': check.status.value,
                    'response_time': check.response_time,
                    'error_message': check.error_message,
                    'metadata': check.metadata,
                    'timestamp': check.timestamp.isoformat()
                }
                
                # Update overall status
                if check.status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                elif check.status == HealthStatus.UNHEALTHY and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.UNHEALTHY
                elif check.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            else:
                logger.error(f"Health check failed: {check}")
        
        # Collect system metrics
        system_metrics = SystemMetrics()
        self.metrics_history.append(system_metrics)
        
        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Create health report
        health_report = {
            'overall_status': overall_status.value,
            'timestamp': datetime.utcnow().isoformat(),
            'check_duration': time.time() - start_time,
            'components': components,
            'system_metrics': {
                'cpu_usage': system_metrics.cpu_usage,
                'memory_usage': system_metrics.memory_usage,
                'disk_usage': system_metrics.disk_usage,
                'load_average': system_metrics.load_average
            }
        }
        
        # Store in history
        self.health_history.append(health_report)
        
        # Keep only last 100 health checks
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]
        
        self.last_check_time = datetime.utcnow()
        
        # Check for alerts
        await self._check_alerts(health_report)
        
        return health_report
    
    async def _check_database_health(self) -> ComponentHealth:
        """Check database health."""
        start_time = time.time()
        
        try:
            async with get_db_session() as session:
                # Simple query to test connection
                result = await session.execute(text("SELECT 1"))
                await result.fetchone()
                
                # Check connection pool status
                pool = session.bind.pool
                pool_status = {
                    'size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': pool.invalid()
                }
                
                response_time = time.time() - start_time
                
                # Determine status based on response time and pool usage
                if response_time > 2.0:
                    status = HealthStatus.DEGRADED
                elif pool.checkedout() / pool.size() > 0.8:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.HEALTHY
                
                return ComponentHealth(
                    name="database",
                    status=status,
                    response_time=response_time,
                    metadata=pool_status
                )
                
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_redis_health(self) -> ComponentHealth:
        """Check Redis health."""
        start_time = time.time()
        
        try:
            # This would need to be configured with your Redis connection
            # For now, we'll simulate the check
            redis_client = None  # Would be actual Redis client
            
            if redis_client:
                await redis_client.ping()
                info = await redis_client.info()
                
                response_time = time.time() - start_time
                
                # Check memory usage
                memory_usage = info.get('used_memory_rss', 0) / info.get('maxmemory', 1)
                
                if memory_usage > 0.9:
                    status = HealthStatus.DEGRADED
                elif response_time > 1.0:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.HEALTHY
                
                return ComponentHealth(
                    name="redis",
                    status=status,
                    response_time=response_time,
                    metadata={'memory_usage': memory_usage}
                )
            else:
                # Redis not configured or available
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    response_time=time.time() - start_time,
                    error_message="Redis not configured"
                )
                
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_chromadb_health(self) -> ComponentHealth:
        """Check ChromaDB health."""
        start_time = time.time()
        
        try:
            chromadb_manager = ChromaDBManager()
            
            # Test connection with heartbeat
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{chromadb_manager.host}:{chromadb_manager.port}/api/v1/heartbeat",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        
                        # Get collection stats
                        stats = await chromadb_manager.get_collection_stats()
                        
                        status = HealthStatus.HEALTHY
                        if response_time > 2.0:
                            status = HealthStatus.DEGRADED
                        
                        return ComponentHealth(
                            name="chromadb",
                            status=status,
                            response_time=response_time,
                            metadata=stats
                        )
                    else:
                        return ComponentHealth(
                            name="chromadb",
                            status=HealthStatus.UNHEALTHY,
                            response_time=time.time() - start_time,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            return ComponentHealth(
                name="chromadb",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_ai_model_health(self) -> ComponentHealth:
        """Check AI model health."""
        start_time = time.time()
        
        try:
            # Test OpenAI API with a simple request
            import openai
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Health check"}],
                max_tokens=5,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            if response_time > 5.0:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return ComponentHealth(
                name="ai_model",
                status=status,
                response_time=response_time,
                metadata={'model': 'gpt-3.5-turbo'}
            )
            
        except Exception as e:
            return ComponentHealth(
                name="ai_model",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_disk_space(self) -> ComponentHealth:
        """Check disk space."""
        try:
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            if usage_percent > 95:
                status = HealthStatus.CRITICAL
            elif usage_percent > 90:
                status = HealthStatus.UNHEALTHY
            elif usage_percent > 80:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return ComponentHealth(
                name="disk_space",
                status=status,
                metadata={
                    'usage_percent': usage_percent,
                    'free_gb': disk_usage.free / (1024**3),
                    'total_gb': disk_usage.total / (1024**3)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                error_message=str(e)
            )
    
    async def _check_memory_usage(self) -> ComponentHealth:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent > 95:
                status = HealthStatus.CRITICAL
            elif usage_percent > 90:
                status = HealthStatus.UNHEALTHY
            elif usage_percent > 80:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return ComponentHealth(
                name="memory",
                status=status,
                metadata={
                    'usage_percent': usage_percent,
                    'available_gb': memory.available / (1024**3),
                    'total_gb': memory.total / (1024**3)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                error_message=str(e)
            )
    
    async def _check_alerts(self, health_report: Dict[str, Any]):
        """Check if any alerts should be triggered."""
        alerts = []
        
        # Check system metrics against thresholds
        metrics = health_report['system_metrics']
        
        for metric, value in metrics.items():
            if metric in self.alert_thresholds and value > self.alert_thresholds[metric]:
                alerts.append({
                    'type': 'metric_threshold',
                    'metric': metric,
                    'value': value,
                    'threshold': self.alert_thresholds[metric],
                    'severity': 'warning'
                })
        
        # Check component health
        for component_name, component_data in health_report['components'].items():
            if component_data['status'] in ['unhealthy', 'critical']:
                alerts.append({
                    'type': 'component_health',
                    'component': component_name,
                    'status': component_data['status'],
                    'error': component_data.get('error_message'),
                    'severity': 'critical' if component_data['status'] == 'critical' else 'warning'
                })
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"Health alert: {json.dumps(alert)}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        if not self.health_history:
            return {'status': 'no_data', 'message': 'No health checks performed yet'}
        
        latest = self.health_history[-1]
        
        # Calculate uptime and availability
        healthy_checks = sum(1 for check in self.health_history if check['overall_status'] == 'healthy')
        availability = (healthy_checks / len(self.health_history)) * 100
        
        return {
            'current_status': latest['overall_status'],
            'last_check': latest['timestamp'],
            'availability_percent': round(availability, 2),
            'total_checks': len(self.health_history),
            'components': latest['components'],
            'system_metrics': latest['system_metrics']
        }
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for the specified number of hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            {
                'timestamp': metric.timestamp.isoformat(),
                'cpu_usage': metric.cpu_usage,
                'memory_usage': metric.memory_usage,
                'disk_usage': metric.disk_usage,
                'load_average': metric.load_average
            }
            for metric in self.metrics_history
            if metric.timestamp > cutoff_time
        ]


# Global health monitor instance
health_monitor = HealthMonitor()
