"""
Single-Threaded Linear Agent Pattern Compliance Validator
Validates that the Mental Health Agent follows the Single-Threaded Linear Agent pattern.
"""

import asyncio
import inspect
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from ..agents import LinearMentalHealthAgent
from ..models.core import UserInput, InputType
from ..monitoring.logging_config import get_logger

logger = get_logger("validation.linear_agent")


@dataclass
class PatternViolation:
    """Pattern violation details."""
    
    violation_type: str
    severity: str  # low, medium, high, critical
    description: str
    location: str
    recommendation: str


@dataclass
class LinearAgentValidationResult:
    """Linear agent validation result."""
    
    compliant: bool
    compliance_score: float
    violations: List[PatternViolation]
    validation_details: Dict[str, Any]
    execution_time: float
    timestamp: datetime


class LinearAgentPatternValidator:
    """Validates Single-Threaded Linear Agent pattern compliance."""
    
    def __init__(self):
        """Initialize pattern validator."""
        self.expected_pipeline_steps = [
            "input_validation",
            "input_analysis", 
            "context_retrieval",
            "safety_assessment",
            "knowledge_retrieval",
            "image_search",
            "reasoning_generation",
            "safety_validation",
            "response_formatting",
            "context_update"
        ]
        
        self.violations = []
        
    async def validate_linear_agent_compliance(
        self,
        agent: LinearMentalHealthAgent
    ) -> LinearAgentValidationResult:
        """
        Validate that the agent follows Single-Threaded Linear Agent pattern.
        
        Args:
            agent: Mental Health Agent instance to validate
            
        Returns:
            Validation result with compliance details
        """
        logger.info("Starting Linear Agent pattern compliance validation")
        start_time = time.time()
        
        self.violations = []
        validation_details = {}
        
        try:
            # 1. Validate sequential execution pattern
            sequential_result = await self._validate_sequential_execution(agent)
            validation_details["sequential_execution"] = sequential_result
            
            # 2. Validate single-threaded operation
            threading_result = await self._validate_single_threaded_operation(agent)
            validation_details["single_threaded"] = threading_result
            
            # 3. Validate tool-based architecture (no sub-agents)
            architecture_result = await self._validate_tool_based_architecture(agent)
            validation_details["tool_based_architecture"] = architecture_result
            
            # 4. Validate context integrity
            context_result = await self._validate_context_integrity(agent)
            validation_details["context_integrity"] = context_result
            
            # 5. Validate pipeline completeness
            pipeline_result = await self._validate_pipeline_completeness(agent)
            validation_details["pipeline_completeness"] = pipeline_result
            
            # 6. Validate error handling pattern
            error_handling_result = await self._validate_error_handling_pattern(agent)
            validation_details["error_handling"] = error_handling_result
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score()
            compliant = compliance_score >= 0.8 and not any(v.severity == "critical" for v in self.violations)
            
            execution_time = time.time() - start_time
            
            result = LinearAgentValidationResult(
                compliant=compliant,
                compliance_score=compliance_score,
                violations=self.violations.copy(),
                validation_details=validation_details,
                execution_time=execution_time,
                timestamp=datetime.utcnow()
            )
            
            logger.info(
                f"Linear Agent validation completed: {'COMPLIANT' if compliant else 'NON-COMPLIANT'} "
                f"(score: {compliance_score:.2f}, violations: {len(self.violations)})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Linear Agent validation failed: {e}")
            
            return LinearAgentValidationResult(
                compliant=False,
                compliance_score=0.0,
                violations=[PatternViolation(
                    violation_type="validation_error",
                    severity="critical",
                    description=f"Validation process failed: {str(e)}",
                    location="validator",
                    recommendation="Fix validation process"
                )],
                validation_details={"error": str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.utcnow()
            )
    
    async def _validate_sequential_execution(self, agent: LinearMentalHealthAgent) -> Dict[str, Any]:
        """Validate that the agent executes steps sequentially."""
        logger.debug("Validating sequential execution pattern")
        
        try:
            # Check if process_request method exists and follows sequential pattern
            if not hasattr(agent, 'process_request'):
                self.violations.append(PatternViolation(
                    violation_type="missing_main_method",
                    severity="critical",
                    description="Agent missing main process_request method",
                    location="LinearMentalHealthAgent",
                    recommendation="Implement process_request method as main entry point"
                ))
                return {"valid": False, "reason": "Missing main method"}
            
            # Analyze method implementation for sequential pattern
            method_source = inspect.getsource(agent.process_request)
            
            # Check for parallel execution patterns (asyncio.gather, concurrent.futures, etc.)
            parallel_patterns = ["asyncio.gather", "concurrent.futures", "threading.Thread", "multiprocessing"]
            for pattern in parallel_patterns:
                if pattern in method_source:
                    self.violations.append(PatternViolation(
                        violation_type="parallel_execution_detected",
                        severity="high",
                        description=f"Detected parallel execution pattern: {pattern}",
                        location="process_request method",
                        recommendation="Replace parallel execution with sequential tool calls"
                    ))
            
            # Check for proper sequential tool execution
            sequential_indicators = ["await", "step", "pipeline"]
            has_sequential_indicators = any(indicator in method_source for indicator in sequential_indicators)
            
            if not has_sequential_indicators:
                self.violations.append(PatternViolation(
                    violation_type="no_sequential_indicators",
                    severity="medium",
                    description="No clear sequential execution indicators found",
                    location="process_request method",
                    recommendation="Add clear sequential step execution pattern"
                ))
            
            return {
                "valid": len([v for v in self.violations if v.violation_type.startswith("parallel_")]) == 0,
                "sequential_indicators_found": has_sequential_indicators,
                "method_analyzed": True
            }
            
        except Exception as e:
            self.violations.append(PatternViolation(
                violation_type="sequential_validation_error",
                severity="medium",
                description=f"Could not validate sequential execution: {str(e)}",
                location="validator",
                recommendation="Ensure agent code is accessible for analysis"
            ))
            return {"valid": False, "error": str(e)}
    
    async def _validate_single_threaded_operation(self, agent: LinearMentalHealthAgent) -> Dict[str, Any]:
        """Validate single-threaded operation."""
        logger.debug("Validating single-threaded operation")
        
        try:
            # Test with multiple concurrent requests to ensure single-threaded processing
            test_input = UserInput(
                user_id="test_user",
                session_id="test_session",
                type=InputType.TEXT,
                content="Test message for threading validation",
                metadata={"test": "threading"}
            )
            
            # Record thread IDs during execution
            thread_ids = set()
            
            async def track_execution():
                import threading
                thread_ids.add(threading.current_thread().ident)
                try:
                    response, metadata = await agent.process_request(test_input)
                    return response
                except Exception as e:
                    logger.warning(f"Test execution failed: {e}")
                    return None
            
            # Run multiple concurrent requests
            tasks = [track_execution() for _ in range(3)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if all executions used the same thread (single-threaded)
            if len(thread_ids) > 1:
                self.violations.append(PatternViolation(
                    violation_type="multi_threaded_execution",
                    severity="high",
                    description=f"Agent used multiple threads: {thread_ids}",
                    location="process_request execution",
                    recommendation="Ensure all processing happens in single thread"
                ))
            
            successful_responses = [r for r in responses if not isinstance(r, Exception)]
            
            return {
                "valid": len(thread_ids) <= 1,
                "thread_ids_used": list(thread_ids),
                "successful_executions": len(successful_responses),
                "total_executions": len(tasks)
            }
            
        except Exception as e:
            self.violations.append(PatternViolation(
                violation_type="threading_validation_error",
                severity="medium",
                description=f"Could not validate threading: {str(e)}",
                location="validator",
                recommendation="Ensure agent is properly initialized for testing"
            ))
            return {"valid": False, "error": str(e)}
    
    async def _validate_tool_based_architecture(self, agent: LinearMentalHealthAgent) -> Dict[str, Any]:
        """Validate tool-based architecture (no autonomous sub-agents)."""
        logger.debug("Validating tool-based architecture")
        
        try:
            # Check agent attributes for tools vs sub-agents
            tools_found = []
            sub_agents_found = []
            
            for attr_name in dir(agent):
                if attr_name.startswith('_'):
                    continue
                    
                attr = getattr(agent, attr_name)
                
                # Check for tool-like objects
                if hasattr(attr, '__call__') and 'tool' in attr_name.lower():
                    tools_found.append(attr_name)
                
                # Check for agent-like objects (potential sub-agents)
                if hasattr(attr, 'process_request') and attr_name != 'process_request':
                    sub_agents_found.append(attr_name)
            
            # Validate that we have tools, not sub-agents
            if sub_agents_found:
                self.violations.append(PatternViolation(
                    violation_type="sub_agents_detected",
                    severity="critical",
                    description=f"Detected potential sub-agents: {sub_agents_found}",
                    location="LinearMentalHealthAgent attributes",
                    recommendation="Replace sub-agents with tools that don't have autonomous processing"
                ))
            
            # Check for expected tools
            expected_tools = ["rag_search_tool", "input_analysis_tool", "context_management", "safety_compliance_layer"]
            missing_tools = [tool for tool in expected_tools if not hasattr(agent, tool)]
            
            if missing_tools:
                self.violations.append(PatternViolation(
                    violation_type="missing_tools",
                    severity="medium",
                    description=f"Missing expected tools: {missing_tools}",
                    location="LinearMentalHealthAgent",
                    recommendation="Ensure all required tools are properly initialized"
                ))
            
            return {
                "valid": len(sub_agents_found) == 0,
                "tools_found": tools_found,
                "sub_agents_found": sub_agents_found,
                "missing_tools": missing_tools
            }
            
        except Exception as e:
            self.violations.append(PatternViolation(
                violation_type="architecture_validation_error",
                severity="medium",
                description=f"Could not validate architecture: {str(e)}",
                location="validator",
                recommendation="Ensure agent structure is accessible for analysis"
            ))
            return {"valid": False, "error": str(e)}
    
    async def _validate_context_integrity(self, agent: LinearMentalHealthAgent) -> Dict[str, Any]:
        """Validate context integrity throughout processing."""
        logger.debug("Validating context integrity")
        
        try:
            # Test that context is maintained throughout processing
            test_input = UserInput(
                user_id="context_test_user",
                session_id="context_test_session",
                type=InputType.TEXT,
                content="Test message for context validation",
                metadata={"context_test": True, "test_value": "12345"}
            )
            
            response, metadata = await agent.process_request(test_input)
            
            # Check if context information is preserved
            context_preserved = True
            context_details = {}
            
            # Check if user_id and session_id are preserved in metadata
            if metadata:
                context_details["metadata_present"] = True
                context_details["user_id_preserved"] = test_input.user_id in str(metadata)
                context_details["session_id_preserved"] = test_input.session_id in str(metadata)
            else:
                context_preserved = False
                context_details["metadata_present"] = False
            
            # Check if response contains context-aware information
            if response and response.content:
                context_details["response_generated"] = True
                context_details["response_length"] = len(response.content)
            else:
                context_preserved = False
                context_details["response_generated"] = False
            
            if not context_preserved:
                self.violations.append(PatternViolation(
                    violation_type="context_integrity_loss",
                    severity="medium",
                    description="Context information not properly maintained during processing",
                    location="process_request pipeline",
                    recommendation="Ensure context is passed through all pipeline steps"
                ))
            
            return {
                "valid": context_preserved,
                "context_details": context_details
            }
            
        except Exception as e:
            self.violations.append(PatternViolation(
                violation_type="context_validation_error",
                severity="medium",
                description=f"Could not validate context integrity: {str(e)}",
                location="validator",
                recommendation="Ensure agent can process test requests"
            ))
            return {"valid": False, "error": str(e)}
    
    async def _validate_pipeline_completeness(self, agent: LinearMentalHealthAgent) -> Dict[str, Any]:
        """Validate that all expected pipeline steps are present."""
        logger.debug("Validating pipeline completeness")
        
        try:
            # Check if agent has methods or attributes for each pipeline step
            pipeline_coverage = {}
            
            for step in self.expected_pipeline_steps:
                # Check for method or attribute related to this step
                step_found = False
                
                # Look for methods containing the step name
                for attr_name in dir(agent):
                    if step.replace("_", "") in attr_name.replace("_", "").lower():
                        step_found = True
                        break
                
                pipeline_coverage[step] = step_found
                
                if not step_found:
                    self.violations.append(PatternViolation(
                        violation_type="missing_pipeline_step",
                        severity="medium",
                        description=f"Pipeline step '{step}' not clearly implemented",
                        location="LinearMentalHealthAgent",
                        recommendation=f"Implement clear method or logic for {step} step"
                    ))
            
            coverage_percentage = sum(pipeline_coverage.values()) / len(pipeline_coverage)
            
            return {
                "valid": coverage_percentage >= 0.8,
                "coverage_percentage": coverage_percentage,
                "pipeline_coverage": pipeline_coverage,
                "missing_steps": [step for step, found in pipeline_coverage.items() if not found]
            }
            
        except Exception as e:
            self.violations.append(PatternViolation(
                violation_type="pipeline_validation_error",
                severity="medium",
                description=f"Could not validate pipeline: {str(e)}",
                location="validator",
                recommendation="Ensure agent structure is accessible for analysis"
            ))
            return {"valid": False, "error": str(e)}
    
    async def _validate_error_handling_pattern(self, agent: LinearMentalHealthAgent) -> Dict[str, Any]:
        """Validate error handling follows linear pattern."""
        logger.debug("Validating error handling pattern")
        
        try:
            # Test error handling with invalid input
            invalid_input = UserInput(
                user_id="",  # Invalid empty user ID
                session_id="error_test_session",
                type=InputType.TEXT,
                content="",  # Invalid empty content
                metadata={}
            )
            
            try:
                response, metadata = await agent.process_request(invalid_input)
                
                # Check if error was handled gracefully
                error_handled_gracefully = (
                    response is not None and 
                    hasattr(response, 'content') and 
                    response.content is not None
                )
                
                return {
                    "valid": error_handled_gracefully,
                    "graceful_degradation": error_handled_gracefully,
                    "response_generated": response is not None
                }
                
            except Exception as e:
                # Check if exception is properly structured
                error_properly_structured = hasattr(e, '__str__') and len(str(e)) > 0
                
                if not error_properly_structured:
                    self.violations.append(PatternViolation(
                        violation_type="poor_error_handling",
                        severity="medium",
                        description="Errors not properly structured or handled",
                        location="process_request error handling",
                        recommendation="Implement proper error handling with meaningful messages"
                    ))
                
                return {
                    "valid": error_properly_structured,
                    "exception_raised": True,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                }
                
        except Exception as e:
            self.violations.append(PatternViolation(
                violation_type="error_handling_validation_error",
                severity="low",
                description=f"Could not validate error handling: {str(e)}",
                location="validator",
                recommendation="Ensure agent can handle test error scenarios"
            ))
            return {"valid": False, "error": str(e)}
    
    def _calculate_compliance_score(self) -> float:
        """Calculate overall compliance score."""
        if not self.violations:
            return 1.0
        
        # Weight violations by severity
        severity_weights = {
            "low": 0.1,
            "medium": 0.3,
            "high": 0.6,
            "critical": 1.0
        }
        
        total_penalty = sum(severity_weights.get(v.severity, 0.5) for v in self.violations)
        max_possible_penalty = len(self.violations) * 1.0  # If all were critical
        
        # Calculate score (1.0 - normalized penalty)
        if max_possible_penalty == 0:
            return 1.0
        
        normalized_penalty = min(total_penalty / max_possible_penalty, 1.0)
        return max(0.0, 1.0 - normalized_penalty)


# Global linear agent validator
linear_agent_validator = LinearAgentPatternValidator()
