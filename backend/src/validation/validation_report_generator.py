"""
Validation Report Generator for Mental Health Agent
Generates comprehensive validation reports for system compliance and readiness.
"""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .system_integration_test import SystemIntegrationValidator
from .linear_agent_validator import LinearAgentPatternValidator
from .safety_compliance_audit import SafetyComplianceAuditor
from ..testing.test_runner import MentalHealthTestRunner
from ..testing.e2e_tests import E2ETestSuite
from ..utils.agent_factory import AgentFactory
from ..monitoring.logging_config import get_logger

logger = get_logger("validation.report_generator")


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    
    report_id: str
    timestamp: datetime
    system_info: Dict[str, Any]
    integration_test_results: Dict[str, Any]
    linear_agent_compliance: Dict[str, Any]
    safety_compliance_audit: Dict[str, Any]
    agent_test_results: Optional[Dict[str, Any]]
    e2e_test_results: Optional[Dict[str, Any]]
    overall_assessment: Dict[str, Any]
    recommendations: List[str]
    deployment_readiness: bool
    execution_time: float


class ValidationReportGenerator:
    """Generates comprehensive validation reports."""
    
    def __init__(self):
        """Initialize validation report generator."""
        self.system_validator = SystemIntegrationValidator()
        self.linear_validator = LinearAgentPatternValidator()
        self.safety_auditor = SafetyComplianceAuditor()
        
    async def generate_comprehensive_validation_report(
        self,
        include_agent_tests: bool = True,
        include_e2e_tests: bool = True,
        output_file: Optional[str] = None
    ) -> ValidationReport:
        """
        Generate comprehensive validation report.
        
        Args:
            include_agent_tests: Whether to include agent functionality tests
            include_e2e_tests: Whether to include end-to-end tests
            output_file: Optional output file path
            
        Returns:
            Complete validation report
        """
        logger.info("Starting comprehensive validation report generation")
        start_time = time.time()
        
        report_id = f"VALIDATION_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 1. System Integration Tests
            logger.info("Running system integration tests...")
            integration_results = await self.system_validator.run_complete_integration_test()
            
            # 2. Linear Agent Pattern Compliance
            logger.info("Validating Linear Agent pattern compliance...")
            agent = None
            try:
                agent = await AgentFactory.create_linear_mental_health_agent()
            except Exception as e:
                logger.warning(f"Could not create agent for validation: {e}")
            
            linear_compliance = await self.linear_validator.validate_linear_agent_compliance(agent)
            
            # 3. Safety and Compliance Audit
            logger.info("Conducting safety and compliance audit...")
            safety_audit = await self.safety_auditor.conduct_comprehensive_audit(agent)
            
            # 4. Agent Functionality Tests (optional)
            agent_test_results = None
            if include_agent_tests and agent:
                logger.info("Running agent functionality tests...")
                try:
                    test_runner = MentalHealthTestRunner(agent)
                    agent_test_results = await test_runner.run_all_tests()
                    agent_test_results = asdict(agent_test_results)
                except Exception as e:
                    logger.warning(f"Agent tests failed: {e}")
                    agent_test_results = {"error": str(e)}
            
            # 5. End-to-End Tests (optional)
            e2e_test_results = None
            if include_e2e_tests:
                logger.info("Running end-to-end tests...")
                try:
                    e2e_suite = E2ETestSuite()
                    e2e_test_results = await e2e_suite.run_full_e2e_suite()
                except Exception as e:
                    logger.warning(f"E2E tests failed: {e}")
                    e2e_test_results = {"error": str(e)}
            
            # 6. Overall Assessment
            overall_assessment = self._generate_overall_assessment(
                integration_results,
                asdict(linear_compliance),
                asdict(safety_audit),
                agent_test_results,
                e2e_test_results
            )
            
            # 7. Recommendations
            recommendations = self._generate_recommendations(
                integration_results,
                linear_compliance,
                safety_audit,
                agent_test_results,
                e2e_test_results
            )
            
            # 8. Deployment Readiness
            deployment_readiness = self._assess_deployment_readiness(overall_assessment)
            
            execution_time = time.time() - start_time
            
            # Create validation report
            report = ValidationReport(
                report_id=report_id,
                timestamp=datetime.utcnow(),
                system_info=integration_results.get("system_info", {}),
                integration_test_results=integration_results,
                linear_agent_compliance=asdict(linear_compliance),
                safety_compliance_audit=asdict(safety_audit),
                agent_test_results=agent_test_results,
                e2e_test_results=e2e_test_results,
                overall_assessment=overall_assessment,
                recommendations=recommendations,
                deployment_readiness=deployment_readiness,
                execution_time=execution_time
            )
            
            # Save report if output file specified
            if output_file:
                await self._save_report(report, output_file)
            
            logger.info(
                f"Validation report generated: {report_id} "
                f"(deployment ready: {deployment_readiness}, time: {execution_time:.2f}s)"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Validation report generation failed: {e}")
            
            # Return error report
            return ValidationReport(
                report_id=report_id,
                timestamp=datetime.utcnow(),
                system_info={"error": str(e)},
                integration_test_results={"error": str(e)},
                linear_agent_compliance={"error": str(e)},
                safety_compliance_audit={"error": str(e)},
                agent_test_results={"error": str(e)},
                e2e_test_results={"error": str(e)},
                overall_assessment={"status": "failed", "error": str(e)},
                recommendations=["Fix validation process errors"],
                deployment_readiness=False,
                execution_time=time.time() - start_time
            )
    
    def _generate_overall_assessment(
        self,
        integration_results: Dict[str, Any],
        linear_compliance: Dict[str, Any],
        safety_audit: Dict[str, Any],
        agent_test_results: Optional[Dict[str, Any]],
        e2e_test_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate overall system assessment."""
        
        assessment = {
            "status": "unknown",
            "scores": {},
            "critical_issues": [],
            "warnings": [],
            "passed_validations": [],
            "failed_validations": []
        }
        
        try:
            # Integration test assessment
            integration_success_rate = integration_results.get("summary", {}).get("success_rate", 0)
            assessment["scores"]["integration_tests"] = integration_success_rate
            
            if integration_success_rate >= 0.8:
                assessment["passed_validations"].append("System Integration Tests")
            else:
                assessment["failed_validations"].append("System Integration Tests")
                assessment["critical_issues"].append(f"Integration test success rate: {integration_success_rate:.1%}")
            
            # Linear agent compliance assessment
            linear_compliant = linear_compliance.get("compliant", False)
            linear_score = linear_compliance.get("compliance_score", 0)
            assessment["scores"]["linear_agent_compliance"] = linear_score
            
            if linear_compliant:
                assessment["passed_validations"].append("Linear Agent Pattern Compliance")
            else:
                assessment["failed_validations"].append("Linear Agent Pattern Compliance")
                violations = linear_compliance.get("violations", [])
                critical_violations = [v for v in violations if v.get("severity") == "critical"]
                if critical_violations:
                    assessment["critical_issues"].extend([v.get("description", "Unknown violation") for v in critical_violations])
            
            # Safety compliance assessment
            safety_compliant = safety_audit.get("overall_compliant", False)
            safety_score = safety_audit.get("compliance_score", 0)
            assessment["scores"]["safety_compliance"] = safety_score
            
            if safety_compliant:
                assessment["passed_validations"].append("Safety and Compliance Audit")
            else:
                assessment["failed_validations"].append("Safety and Compliance Audit")
                findings = safety_audit.get("findings", [])
                critical_findings = [f for f in findings if f.get("severity") == "critical" and not f.get("compliant", True)]
                if critical_findings:
                    assessment["critical_issues"].extend([f.get("description", "Unknown finding") for f in critical_findings])
            
            # Agent test assessment
            if agent_test_results and "error" not in agent_test_results:
                agent_success_rate = agent_test_results.get("success_rate", 0)
                assessment["scores"]["agent_tests"] = agent_success_rate
                
                if agent_success_rate >= 0.8:
                    assessment["passed_validations"].append("Agent Functionality Tests")
                else:
                    assessment["failed_validations"].append("Agent Functionality Tests")
                    assessment["warnings"].append(f"Agent test success rate: {agent_success_rate:.1%}")
            
            # E2E test assessment
            if e2e_test_results and "error" not in e2e_test_results:
                e2e_success_rate = e2e_test_results.get("summary", {}).get("success_rate", 0)
                assessment["scores"]["e2e_tests"] = e2e_success_rate
                
                if e2e_success_rate >= 0.7:
                    assessment["passed_validations"].append("End-to-End Tests")
                else:
                    assessment["failed_validations"].append("End-to-End Tests")
                    assessment["warnings"].append(f"E2E test success rate: {e2e_success_rate:.1%}")
            
            # Overall status determination
            if assessment["critical_issues"]:
                assessment["status"] = "critical_issues"
            elif assessment["failed_validations"]:
                assessment["status"] = "has_failures"
            elif assessment["warnings"]:
                assessment["status"] = "has_warnings"
            else:
                assessment["status"] = "passed"
            
            # Calculate overall score
            scores = [score for score in assessment["scores"].values() if isinstance(score, (int, float))]
            assessment["overall_score"] = sum(scores) / len(scores) if scores else 0
            
        except Exception as e:
            logger.error(f"Error generating overall assessment: {e}")
            assessment["status"] = "assessment_error"
            assessment["critical_issues"].append(f"Assessment generation failed: {str(e)}")
        
        return assessment
    
    def _generate_recommendations(
        self,
        integration_results: Dict[str, Any],
        linear_compliance,
        safety_audit,
        agent_test_results: Optional[Dict[str, Any]],
        e2e_test_results: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on validation results."""
        
        recommendations = []
        
        try:
            # Integration test recommendations
            integration_success_rate = integration_results.get("summary", {}).get("success_rate", 0)
            if integration_success_rate < 0.8:
                recommendations.append("Fix failing system integration tests before deployment")
            
            # Linear agent compliance recommendations
            if not linear_compliance.compliant:
                violations = linear_compliance.violations
                critical_violations = [v for v in violations if v.severity == "critical"]
                if critical_violations:
                    recommendations.append("Address critical Linear Agent pattern violations")
                recommendations.append("Review and fix Linear Agent pattern compliance issues")
            
            # Safety compliance recommendations
            if not safety_audit.overall_compliant:
                findings = safety_audit.findings
                critical_findings = [f for f in findings if f.severity.value == "critical" and not f.compliant]
                if critical_findings:
                    recommendations.append("Address critical safety and compliance issues immediately")
                recommendations.append("Complete safety and compliance audit remediation")
            
            # Agent test recommendations
            if agent_test_results and "error" not in agent_test_results:
                agent_success_rate = agent_test_results.get("success_rate", 0)
                if agent_success_rate < 0.8:
                    recommendations.append("Improve agent functionality test coverage and success rate")
            
            # E2E test recommendations
            if e2e_test_results and "error" not in e2e_test_results:
                e2e_success_rate = e2e_test_results.get("summary", {}).get("success_rate", 0)
                if e2e_success_rate < 0.7:
                    recommendations.append("Fix end-to-end test failures")
            
            # General recommendations
            recommendations.extend([
                "Ensure all environment variables are properly configured",
                "Verify OpenAI API key is valid and has sufficient quota",
                "Test crisis intervention system with real scenarios",
                "Validate medical disclaimer compliance",
                "Implement comprehensive monitoring and alerting",
                "Conduct security penetration testing",
                "Perform load testing under expected traffic",
                "Create disaster recovery procedures",
                "Train support staff on system operations",
                "Document all configuration and operational procedures"
            ])
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append(f"Fix recommendation generation process: {str(e)}")
        
        return recommendations
    
    def _assess_deployment_readiness(self, overall_assessment: Dict[str, Any]) -> bool:
        """Assess if system is ready for deployment."""
        
        try:
            # Critical issues block deployment
            if overall_assessment.get("critical_issues"):
                return False
            
            # Must pass core validations
            required_validations = [
                "System Integration Tests",
                "Linear Agent Pattern Compliance", 
                "Safety and Compliance Audit"
            ]
            
            passed_validations = overall_assessment.get("passed_validations", [])
            
            for validation in required_validations:
                if validation not in passed_validations:
                    return False
            
            # Overall score threshold
            overall_score = overall_assessment.get("overall_score", 0)
            if overall_score < 0.8:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error assessing deployment readiness: {e}")
            return False
    
    async def _save_report(self, report: ValidationReport, output_file: str):
        """Save validation report to file."""
        
        try:
            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert report to dict for JSON serialization
            report_dict = asdict(report)
            
            # Handle datetime serialization
            report_dict["timestamp"] = report.timestamp.isoformat()
            
            # Save as JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            logger.info(f"Validation report saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")
            raise
    
    async def generate_deployment_checklist(self, report: ValidationReport) -> Dict[str, Any]:
        """Generate deployment checklist based on validation report."""
        
        checklist = {
            "pre_deployment": [],
            "deployment": [],
            "post_deployment": [],
            "monitoring": []
        }
        
        # Pre-deployment checklist
        checklist["pre_deployment"] = [
            {"item": "All validation tests pass", "status": "passed" if report.deployment_readiness else "failed"},
            {"item": "Environment variables configured", "status": "pending"},
            {"item": "SSL certificates installed", "status": "pending"},
            {"item": "Database backups created", "status": "pending"},
            {"item": "Monitoring systems configured", "status": "pending"},
            {"item": "Crisis intervention system tested", "status": "pending"},
            {"item": "Security review completed", "status": "pending"}
        ]
        
        # Deployment checklist
        checklist["deployment"] = [
            {"item": "Deploy database services", "status": "pending"},
            {"item": "Deploy backend services", "status": "pending"},
            {"item": "Deploy frontend services", "status": "pending"},
            {"item": "Configure load balancer", "status": "pending"},
            {"item": "Verify service health", "status": "pending"},
            {"item": "Run smoke tests", "status": "pending"}
        ]
        
        # Post-deployment checklist
        checklist["post_deployment"] = [
            {"item": "Verify all endpoints accessible", "status": "pending"},
            {"item": "Test crisis intervention flow", "status": "pending"},
            {"item": "Verify monitoring alerts", "status": "pending"},
            {"item": "Test backup procedures", "status": "pending"},
            {"item": "Document deployment", "status": "pending"}
        ]
        
        # Monitoring checklist
        checklist["monitoring"] = [
            {"item": "Health check monitoring active", "status": "pending"},
            {"item": "Error rate monitoring active", "status": "pending"},
            {"item": "Performance monitoring active", "status": "pending"},
            {"item": "Security monitoring active", "status": "pending"},
            {"item": "Audit logging active", "status": "pending"}
        ]
        
        return checklist


# Global validation report generator
validation_report_generator = ValidationReportGenerator()
