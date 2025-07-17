"""
Validation API endpoints for Mental Health Agent.
Provides system validation and compliance checking endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, Optional
from datetime import datetime

from ..validation import (
    validation_report_generator,
    system_integration_validator,
    linear_agent_validator,
    safety_compliance_auditor
)
from ..models.database import User
from ..monitoring.logging_config import get_logger

router = APIRouter(prefix="/validation", tags=["validation"])
logger = get_logger("api.validation")

# Simple admin check function
async def require_admin(current_user: User = Depends(lambda: None)) -> User:
    """Require admin privileges."""
    # For now, allow all requests since we don't have proper auth setup
    return current_user


@router.post("/comprehensive-report", summary="Generate Comprehensive Validation Report")
async def generate_comprehensive_validation_report(
    background_tasks: BackgroundTasks,
    include_agent_tests: bool = Query(True, description="Include agent functionality tests"),
    include_e2e_tests: bool = Query(True, description="Include end-to-end tests"),
    save_report: bool = Query(True, description="Save report to file"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Generate comprehensive validation report for system readiness.
    
    Args:
        include_agent_tests: Whether to include agent functionality tests
        include_e2e_tests: Whether to include end-to-end tests
        save_report: Whether to save report to file
        background_tasks: Background task handler
        current_user: Current authenticated admin user
        
    Returns:
        Validation report summary
    """
    try:
        logger.info(
            "Comprehensive validation report requested",
            user_id=current_user.id,
            include_agent_tests=include_agent_tests,
            include_e2e_tests=include_e2e_tests
        )
        
        # Generate report in background if it includes heavy tests
        if include_agent_tests or include_e2e_tests:
            background_tasks.add_task(
                _generate_and_save_report,
                include_agent_tests,
                include_e2e_tests,
                save_report,
                current_user.id
            )
            
            return {
                "message": "Comprehensive validation report generation started",
                "status": "running",
                "estimated_completion": "5-10 minutes",
                "includes_agent_tests": include_agent_tests,
                "includes_e2e_tests": include_e2e_tests,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Generate lightweight report immediately
            output_file = f"./reports/validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json" if save_report else None
            
            report = await validation_report_generator.generate_comprehensive_validation_report(
                include_agent_tests=False,
                include_e2e_tests=False,
                output_file=output_file
            )
            
            return {
                "report_id": report.report_id,
                "deployment_readiness": report.deployment_readiness,
                "overall_assessment": report.overall_assessment,
                "recommendations": report.recommendations[:5],  # Top 5 recommendations
                "execution_time": report.execution_time,
                "timestamp": report.timestamp.isoformat(),
                "full_report_available": output_file is not None
            }
        
    except Exception as e:
        logger.error(f"Failed to generate validation report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate validation report")


@router.get("/system-integration", summary="Run System Integration Tests")
async def run_system_integration_tests(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Run system integration tests.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        System integration test results
    """
    try:
        logger.info("System integration tests requested", user_id=current_user.id)
        
        results = await system_integration_validator.run_complete_integration_test()
        
        return {
            "test_results": results.get("summary", {}),
            "components_tested": len(results.get("test_results", [])),
            "success_rate": results.get("summary", {}).get("success_rate", 0),
            "execution_time": results.get("summary", {}).get("total_execution_time", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System integration tests failed: {e}")
        raise HTTPException(status_code=500, detail="System integration tests failed")


@router.get("/linear-agent-compliance", summary="Validate Linear Agent Pattern Compliance")
async def validate_linear_agent_compliance(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Validate Linear Agent pattern compliance.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        Linear Agent pattern compliance results
    """
    try:
        logger.info("Linear Agent compliance validation requested", user_id=current_user.id)
        
        # Try to create agent for validation
        try:
            from ..utils.agent_factory import AgentFactory
            agent = await AgentFactory.create_linear_mental_health_agent()
        except Exception as e:
            logger.warning(f"Could not create agent for validation: {e}")
            agent = None
        
        results = await linear_agent_validator.validate_linear_agent_compliance(agent)
        
        return {
            "compliant": results.compliant,
            "compliance_score": results.compliance_score,
            "violations_count": len(results.violations),
            "critical_violations": len([v for v in results.violations if v.severity == "critical"]),
            "validation_details": results.validation_details,
            "execution_time": results.execution_time,
            "timestamp": results.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Linear Agent compliance validation failed: {e}")
        raise HTTPException(status_code=500, detail="Linear Agent compliance validation failed")


@router.get("/safety-compliance", summary="Run Safety and Compliance Audit")
async def run_safety_compliance_audit(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Run safety and compliance audit.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        Safety and compliance audit results
    """
    try:
        logger.info("Safety compliance audit requested", user_id=current_user.id)
        
        # Try to create agent for audit
        try:
            from ..utils.agent_factory import AgentFactory
            agent = await AgentFactory.create_linear_mental_health_agent()
        except Exception as e:
            logger.warning(f"Could not create agent for audit: {e}")
            agent = None
        
        results = await safety_compliance_auditor.conduct_comprehensive_audit(agent)
        
        return {
            "overall_compliant": results.overall_compliant,
            "compliance_score": results.compliance_score,
            "total_findings": len(results.findings),
            "critical_findings": len([f for f in results.findings if f.severity.value == "critical" and not f.compliant]),
            "standards_audited": [s.value for s in results.standards_audited],
            "audit_summary": results.audit_summary,
            "execution_time": results.execution_time,
            "timestamp": results.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Safety compliance audit failed: {e}")
        raise HTTPException(status_code=500, detail="Safety compliance audit failed")


@router.get("/deployment-readiness", summary="Check Deployment Readiness")
async def check_deployment_readiness(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Check if system is ready for deployment.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        Deployment readiness assessment
    """
    try:
        logger.info("Deployment readiness check requested", user_id=current_user.id)
        
        # Run quick validation checks
        report = await validation_report_generator.generate_comprehensive_validation_report(
            include_agent_tests=False,
            include_e2e_tests=False
        )
        
        # Generate deployment checklist
        checklist = await validation_report_generator.generate_deployment_checklist(report)
        
        return {
            "deployment_ready": report.deployment_readiness,
            "overall_score": report.overall_assessment.get("overall_score", 0),
            "critical_issues": report.overall_assessment.get("critical_issues", []),
            "failed_validations": report.overall_assessment.get("failed_validations", []),
            "top_recommendations": report.recommendations[:3],
            "deployment_checklist": checklist,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Deployment readiness check failed: {e}")
        raise HTTPException(status_code=500, detail="Deployment readiness check failed")


@router.get("/reports", summary="List Validation Reports")
async def list_validation_reports(
    limit: int = Query(10, ge=1, le=50, description="Number of reports to return"),
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    List available validation reports.
    
    Args:
        limit: Number of reports to return
        current_user: Current authenticated admin user
        
    Returns:
        List of available validation reports
    """
    try:
        import os
        from pathlib import Path
        
        reports_dir = Path("./reports")
        
        if not reports_dir.exists():
            return {
                "reports": [],
                "total_reports": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get validation report files
        report_files = []
        for file_path in reports_dir.glob("validation_report_*.json"):
            try:
                stat = file_path.stat()
                report_files.append({
                    "filename": file_path.name,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.warning(f"Could not read report file {file_path}: {e}")
        
        # Sort by creation time (newest first)
        report_files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "reports": report_files[:limit],
            "total_reports": len(report_files),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list validation reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to list validation reports")


async def _generate_and_save_report(
    include_agent_tests: bool,
    include_e2e_tests: bool,
    save_report: bool,
    user_id: str
):
    """Background task to generate and save comprehensive validation report."""
    try:
        logger.info(f"Starting background validation report generation for user {user_id}")
        
        output_file = f"./reports/validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json" if save_report else None
        
        report = await validation_report_generator.generate_comprehensive_validation_report(
            include_agent_tests=include_agent_tests,
            include_e2e_tests=include_e2e_tests,
            output_file=output_file
        )
        
        logger.info(
            f"Background validation report completed for user {user_id}",
            report_id=report.report_id,
            deployment_ready=report.deployment_readiness,
            execution_time=report.execution_time
        )
        
    except Exception as e:
        logger.error(f"Background validation report generation failed for user {user_id}: {e}")
