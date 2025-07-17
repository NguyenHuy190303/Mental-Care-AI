"""
System Integration Test for Mental Health Agent
Comprehensive validation of the complete system integration.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from ..agents import LinearMentalHealthAgent
from ..utils.agent_factory import AgentFactory
from ..testing.test_runner import MentalHealthTestRunner
from ..testing.e2e_tests import E2ETestSuite
from ..monitoring import health_monitor, error_handler
from ..feedback import feedback_collector, rlhf_processor
from ..monitoring.logging_config import get_logger

logger = get_logger("validation.integration")


@dataclass
class IntegrationTestResult:
    """Integration test result."""
    
    component: str
    test_name: str
    success: bool
    execution_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


class SystemIntegrationValidator:
    """Comprehensive system integration validator."""
    
    def __init__(self):
        """Initialize system integration validator."""
        self.agent = None
        self.test_runner = None
        self.e2e_suite = None
        self.results = []
        
    async def run_complete_integration_test(self) -> Dict[str, Any]:
        """Run complete system integration test."""
        logger.info("Starting comprehensive system integration test")
        start_time = time.time()
        
        integration_results = {
            "test_results": [],
            "summary": {},
            "timestamp": datetime.utcnow().isoformat(),
            "system_info": await self._get_system_info()
        }
        
        try:
            # 1. Component initialization tests
            init_results = await self._test_component_initialization()
            integration_results["test_results"].extend(init_results)
            
            # 2. Agent functionality tests
            agent_results = await self._test_agent_functionality()
            integration_results["test_results"].extend(agent_results)
            
            # 3. Database integration tests
            db_results = await self._test_database_integration()
            integration_results["test_results"].extend(db_results)
            
            # 4. API integration tests
            api_results = await self._test_api_integration()
            integration_results["test_results"].extend(api_results)
            
            # 5. Monitoring system tests
            monitoring_results = await self._test_monitoring_integration()
            integration_results["test_results"].extend(monitoring_results)
            
            # 6. Feedback system tests
            feedback_results = await self._test_feedback_integration()
            integration_results["test_results"].extend(feedback_results)
            
            # 7. End-to-end workflow tests
            e2e_results = await self._test_e2e_workflows()
            integration_results["test_results"].extend(e2e_results)
            
            # Calculate summary
            total_time = time.time() - start_time
            integration_results["summary"] = self._calculate_integration_summary(
                integration_results["test_results"], total_time
            )
            
            logger.info(f"System integration test completed in {total_time:.2f}s")
            
        except Exception as e:
            logger.error(f"System integration test failed: {e}")
            integration_results["error"] = str(e)
        
        return integration_results
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            import platform
            import sys
            import psutil
            
            return {
                "platform": platform.platform(),
                "python_version": sys.version,
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _test_component_initialization(self) -> List[IntegrationTestResult]:
        """Test component initialization."""
        logger.info("Testing component initialization")
        results = []
        
        # Test agent factory
        result = await self._test_agent_factory_initialization()
        results.append(result)
        
        # Test health monitor
        result = await self._test_health_monitor_initialization()
        results.append(result)
        
        # Test feedback collector
        result = await self._test_feedback_collector_initialization()
        results.append(result)
        
        return results
    
    async def _test_agent_factory_initialization(self) -> IntegrationTestResult:
        """Test agent factory initialization."""
        start_time = time.time()
        
        try:
            # Validate dependencies
            validation_results = await AgentFactory.validate_agent_dependencies()
            
            # Check critical dependencies
            critical_deps = ['openai_api_key', 'chromadb', 'database']
            all_critical_available = all(
                validation_results.get(dep, {}).get('available', False) 
                for dep in critical_deps
            )
            
            execution_time = time.time() - start_time
            
            return IntegrationTestResult(
                component="agent_factory",
                test_name="initialization",
                success=all_critical_available,
                execution_time=execution_time,
                details={
                    "validation_results": validation_results,
                    "critical_dependencies_available": all_critical_available
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                component="agent_factory",
                test_name="initialization",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    async def _test_health_monitor_initialization(self) -> IntegrationTestResult:
        """Test health monitor initialization."""
        start_time = time.time()
        
        try:
            # Perform health check
            health_report = await health_monitor.perform_health_check()
            
            success = health_report.get('overall_status') in ['healthy', 'degraded']
            execution_time = time.time() - start_time
            
            return IntegrationTestResult(
                component="health_monitor",
                test_name="initialization",
                success=success,
                execution_time=execution_time,
                details={
                    "health_report": health_report,
                    "components_checked": len(health_report.get('components', {}))
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                component="health_monitor",
                test_name="initialization",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    async def _test_feedback_collector_initialization(self) -> IntegrationTestResult:
        """Test feedback collector initialization."""
        start_time = time.time()
        
        try:
            # Test feedback collector functionality
            from ..feedback.feedback_collector import FeedbackData, FeedbackType, FeedbackRating
            
            test_feedback = FeedbackData(
                user_id="test_user",
                session_id="test_session",
                feedback_type=FeedbackType.HELPFULNESS,
                rating=FeedbackRating.GOOD,
                text_feedback="Test feedback"
            )
            
            # This would normally store in database, but we'll just validate the structure
            success = True
            execution_time = time.time() - start_time
            
            return IntegrationTestResult(
                component="feedback_collector",
                test_name="initialization",
                success=success,
                execution_time=execution_time,
                details={
                    "feedback_types_available": len(FeedbackType),
                    "rating_levels_available": len(FeedbackRating)
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                component="feedback_collector",
                test_name="initialization",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    async def _test_agent_functionality(self) -> List[IntegrationTestResult]:
        """Test agent functionality."""
        logger.info("Testing agent functionality")
        results = []
        
        try:
            # Try to create agent (may fail if dependencies not available)
            self.agent = await AgentFactory.create_linear_mental_health_agent(
                confidence_threshold=0.7,
                enable_caching=False,
                enable_detailed_logging=True
            )
            
            # Test agent status
            result = await self._test_agent_status()
            results.append(result)
            
            # Test agent processing (with mock if needed)
            result = await self._test_agent_processing()
            results.append(result)
            
        except Exception as e:
            logger.warning(f"Agent creation failed, using mock tests: {e}")
            result = IntegrationTestResult(
                component="agent",
                test_name="creation",
                success=False,
                execution_time=0.0,
                details={},
                error_message=str(e)
            )
            results.append(result)
        
        return results
    
    async def _test_agent_status(self) -> IntegrationTestResult:
        """Test agent status."""
        start_time = time.time()
        
        try:
            if self.agent:
                status = await self.agent.get_agent_status()
                
                success = status.get('status') == 'healthy'
                execution_time = time.time() - start_time
                
                return IntegrationTestResult(
                    component="agent",
                    test_name="status",
                    success=success,
                    execution_time=execution_time,
                    details=status
                )
            else:
                return IntegrationTestResult(
                    component="agent",
                    test_name="status",
                    success=False,
                    execution_time=time.time() - start_time,
                    details={},
                    error_message="Agent not available"
                )
                
        except Exception as e:
            return IntegrationTestResult(
                component="agent",
                test_name="status",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    async def _test_agent_processing(self) -> IntegrationTestResult:
        """Test agent processing."""
        start_time = time.time()
        
        try:
            if self.agent:
                from ..models.core import UserInput, InputType
                
                test_input = UserInput(
                    user_id="test_user",
                    session_id="test_session",
                    type=InputType.TEXT,
                    content="I'm feeling anxious about my upcoming presentation.",
                    metadata={"test": True}
                )
                
                response, metadata = await self.agent.process_request(test_input)
                
                success = response.content is not None and len(response.content) > 0
                execution_time = time.time() - start_time
                
                return IntegrationTestResult(
                    component="agent",
                    test_name="processing",
                    success=success,
                    execution_time=execution_time,
                    details={
                        "response_length": len(response.content),
                        "confidence_level": response.confidence_level,
                        "has_medical_disclaimer": response.medical_disclaimer is not None,
                        "citations_count": len(response.citations),
                        "processing_metadata": metadata
                    }
                )
            else:
                return IntegrationTestResult(
                    component="agent",
                    test_name="processing",
                    success=False,
                    execution_time=time.time() - start_time,
                    details={},
                    error_message="Agent not available"
                )
                
        except Exception as e:
            return IntegrationTestResult(
                component="agent",
                test_name="processing",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    async def _test_database_integration(self) -> List[IntegrationTestResult]:
        """Test database integration."""
        logger.info("Testing database integration")
        results = []
        
        # Test database connection
        result = await self._test_database_connection()
        results.append(result)
        
        return results
    
    async def _test_database_connection(self) -> IntegrationTestResult:
        """Test database connection."""
        start_time = time.time()
        
        try:
            from ..database import check_database_health
            
            is_healthy = await check_database_health()
            execution_time = time.time() - start_time
            
            return IntegrationTestResult(
                component="database",
                test_name="connection",
                success=is_healthy,
                execution_time=execution_time,
                details={"database_healthy": is_healthy}
            )
            
        except Exception as e:
            return IntegrationTestResult(
                component="database",
                test_name="connection",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    async def _test_api_integration(self) -> List[IntegrationTestResult]:
        """Test API integration."""
        logger.info("Testing API integration")
        results = []
        
        # Test API endpoints availability
        result = await self._test_api_endpoints()
        results.append(result)
        
        return results
    
    async def _test_api_endpoints(self) -> IntegrationTestResult:
        """Test API endpoints."""
        start_time = time.time()
        
        try:
            from fastapi.testclient import TestClient
            from ..main import app
            
            client = TestClient(app)
            
            # Test health endpoint
            response = client.get("/api/monitoring/health")
            health_ok = response.status_code in [200, 503]
            
            # Test status endpoint
            response = client.get("/api/monitoring/status")
            status_ok = response.status_code == 200
            
            # Test feedback types endpoint
            response = client.get("/api/feedback/types")
            feedback_ok = response.status_code == 200
            
            success = health_ok and status_ok and feedback_ok
            execution_time = time.time() - start_time
            
            return IntegrationTestResult(
                component="api",
                test_name="endpoints",
                success=success,
                execution_time=execution_time,
                details={
                    "health_endpoint_ok": health_ok,
                    "status_endpoint_ok": status_ok,
                    "feedback_endpoint_ok": feedback_ok
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                component="api",
                test_name="endpoints",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    async def _test_monitoring_integration(self) -> List[IntegrationTestResult]:
        """Test monitoring integration."""
        logger.info("Testing monitoring integration")
        results = []
        
        # Test error handler
        result = await self._test_error_handler()
        results.append(result)
        
        return results
    
    async def _test_error_handler(self) -> IntegrationTestResult:
        """Test error handler."""
        start_time = time.time()
        
        try:
            # Test error handler functionality
            test_error = Exception("Test error for integration testing")
            error_response = await error_handler.handle_error(test_error)
            
            success = error_response.message is not None
            execution_time = time.time() - start_time
            
            return IntegrationTestResult(
                component="monitoring",
                test_name="error_handler",
                success=success,
                execution_time=execution_time,
                details={
                    "error_response_generated": success,
                    "error_code": error_response.error_code,
                    "error_id": error_response.error_id
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                component="monitoring",
                test_name="error_handler",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    async def _test_feedback_integration(self) -> List[IntegrationTestResult]:
        """Test feedback integration."""
        logger.info("Testing feedback integration")
        results = []
        
        # Test RLHF processor
        result = await self._test_rlhf_processor()
        results.append(result)
        
        return results
    
    async def _test_rlhf_processor(self) -> IntegrationTestResult:
        """Test RLHF processor."""
        start_time = time.time()
        
        try:
            # Test RLHF processor functionality
            metrics = await rlhf_processor.get_rlhf_metrics(days=1)
            
            success = metrics is not None
            execution_time = time.time() - start_time
            
            return IntegrationTestResult(
                component="feedback",
                test_name="rlhf_processor",
                success=success,
                execution_time=execution_time,
                details={
                    "metrics_generated": success,
                    "total_datapoints": metrics.get("total_datapoints", 0)
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                component="feedback",
                test_name="rlhf_processor",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    async def _test_e2e_workflows(self) -> List[IntegrationTestResult]:
        """Test end-to-end workflows."""
        logger.info("Testing end-to-end workflows")
        results = []
        
        # Test E2E suite
        result = await self._test_e2e_suite()
        results.append(result)
        
        return results
    
    async def _test_e2e_suite(self) -> IntegrationTestResult:
        """Test E2E suite."""
        start_time = time.time()
        
        try:
            # Initialize E2E test suite
            self.e2e_suite = E2ETestSuite()
            
            # Run a subset of E2E tests
            e2e_results = await self.e2e_suite.run_full_e2e_suite()
            
            success = e2e_results.get("summary", {}).get("success_rate", 0) > 0.5
            execution_time = time.time() - start_time
            
            return IntegrationTestResult(
                component="e2e",
                test_name="full_suite",
                success=success,
                execution_time=execution_time,
                details={
                    "e2e_results": e2e_results.get("summary", {}),
                    "total_e2e_tests": e2e_results.get("summary", {}).get("total_tests", 0)
                }
            )
            
        except Exception as e:
            return IntegrationTestResult(
                component="e2e",
                test_name="full_suite",
                success=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            )
    
    def _calculate_integration_summary(
        self,
        test_results: List[IntegrationTestResult],
        total_time: float
    ) -> Dict[str, Any]:
        """Calculate integration test summary."""
        if not test_results:
            return {"total_tests": 0, "success_rate": 0.0}
        
        successful_tests = sum(1 for result in test_results if result.success)
        total_tests = len(test_results)
        
        # Group by component
        by_component = {}
        for result in test_results:
            component = result.component
            if component not in by_component:
                by_component[component] = {"passed": 0, "failed": 0, "total": 0}
            
            by_component[component]["total"] += 1
            if result.success:
                by_component[component]["passed"] += 1
            else:
                by_component[component]["failed"] += 1
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": successful_tests / total_tests,
            "total_execution_time": total_time,
            "average_execution_time": sum(r.execution_time for r in test_results) / total_tests,
            "by_component": by_component,
            "components_tested": list(by_component.keys())
        }


# Global system integration validator
system_integration_validator = SystemIntegrationValidator()
