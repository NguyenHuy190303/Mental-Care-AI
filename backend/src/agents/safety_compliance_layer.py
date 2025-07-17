"""
Safety and Compliance Layer for medical AI responses.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum

from ..models.core import AgentResponse, UserInput, AnalyzedInput, ErrorResponse

logger = logging.getLogger(__name__)


class SafetyLevel(str, Enum):
    """Safety levels for content assessment."""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKED = "blocked"


class ComplianceCheck:
    """Represents a compliance check result."""
    
    def __init__(
        self,
        check_name: str,
        passed: bool,
        confidence: float,
        details: str = "",
        recommendations: List[str] = None
    ):
        self.check_name = check_name
        self.passed = passed
        self.confidence = confidence
        self.details = details
        self.recommendations = recommendations or []
        self.timestamp = datetime.utcnow()


class SafetyComplianceLayer:
    """Safety and compliance layer for medical AI responses."""
    
    def __init__(self):
        """Initialize safety compliance layer."""
        self.crisis_keywords = [
            "suicide", "kill myself", "end my life", "self-harm", "hurt myself",
            "overdose", "pills", "cutting", "razor", "jump", "bridge",
            "gun", "weapon", "die", "death", "hopeless", "worthless"
        ]
        
        self.emergency_resources = {
            "crisis_hotlines": [
                "National Suicide Prevention Lifeline: 988",
                "Crisis Text Line: Text HOME to 741741",
                "International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/"
            ],
            "emergency_services": [
                "Emergency Services: 911 (US), 999 (UK), 112 (EU)",
                "Local Emergency Room",
                "Mental Health Crisis Team"
            ],
            "professional_help": [
                "Contact your mental health provider",
                "Visit your primary care physician",
                "Contact a licensed therapist or counselor"
            ]
        }
        
        self.medical_disclaimer_template = (
            "⚠️ **Medical Disclaimer**: This AI assistant provides general mental health "
            "information and support. It is not a substitute for professional medical advice, "
            "diagnosis, or treatment. Always seek the advice of qualified mental health "
            "professionals with any questions you may have regarding a medical condition. "
            "If you are experiencing a mental health emergency, please contact emergency "
            "services or a crisis hotline immediately."
        )
        
        logger.info("Safety Compliance Layer initialized")
    
    async def assess_input_safety(self, user_input: UserInput, analyzed_input: AnalyzedInput) -> Tuple[SafetyLevel, List[str]]:
        """
        Assess the safety level of user input.
        
        Args:
            user_input: User input data
            analyzed_input: Analyzed input with intent and entities
            
        Returns:
            Tuple of (safety level, safety concerns)
        """
        safety_concerns = []
        safety_level = SafetyLevel.SAFE
        
        # Check for crisis indicators
        if self._contains_crisis_keywords(user_input.content):
            safety_concerns.append("Crisis keywords detected")
            safety_level = SafetyLevel.CRITICAL
        
        # Check urgency level
        if analyzed_input.urgency_level >= 9:
            safety_concerns.append("High urgency level detected")
            if safety_level != SafetyLevel.CRITICAL:
                safety_level = SafetyLevel.WARNING
        
        # Check intent
        if analyzed_input.intent == "crisis":
            safety_concerns.append("Crisis intent detected")
            safety_level = SafetyLevel.CRITICAL
        
        # Check for self-harm indicators
        if self._contains_self_harm_indicators(user_input.content):
            safety_concerns.append("Self-harm indicators detected")
            safety_level = SafetyLevel.CRITICAL
        
        # Check for substance abuse indicators
        if self._contains_substance_abuse_indicators(user_input.content):
            safety_concerns.append("Substance abuse indicators detected")
            if safety_level == SafetyLevel.SAFE:
                safety_level = SafetyLevel.CAUTION
        
        return safety_level, safety_concerns
    
    async def validate_response_safety(self, response: AgentResponse) -> List[ComplianceCheck]:
        """
        Validate response for safety and compliance.
        
        Args:
            response: Agent response to validate
            
        Returns:
            List of compliance check results
        """
        checks = []
        
        # Check for medical disclaimer
        disclaimer_check = self._check_medical_disclaimer(response)
        checks.append(disclaimer_check)
        
        # Check for appropriate crisis response
        crisis_check = self._check_crisis_response(response)
        checks.append(crisis_check)
        
        # Check for harmful content
        harmful_content_check = self._check_harmful_content(response)
        checks.append(harmful_content_check)
        
        # Check for medical advice boundaries
        medical_advice_check = self._check_medical_advice_boundaries(response)
        checks.append(medical_advice_check)
        
        # Check for professional referral
        referral_check = self._check_professional_referral(response)
        checks.append(referral_check)
        
        # Check confidence levels
        confidence_check = self._check_confidence_levels(response)
        checks.append(confidence_check)
        
        return checks
    
    async def enhance_response_safety(self, response: AgentResponse, safety_level: SafetyLevel) -> AgentResponse:
        """
        Enhance response with safety measures.
        
        Args:
            response: Original agent response
            safety_level: Assessed safety level
            
        Returns:
            Enhanced response with safety measures
        """
        enhanced_response = response.copy()
        
        # Add crisis resources if needed
        if safety_level in [SafetyLevel.CRITICAL, SafetyLevel.WARNING]:
            enhanced_response = self._add_crisis_resources(enhanced_response)
        
        # Ensure medical disclaimer is present
        if not self._has_medical_disclaimer(enhanced_response.content):
            enhanced_response.medical_disclaimer = self.medical_disclaimer_template
        
        # Add safety warnings
        if safety_level == SafetyLevel.CRITICAL:
            enhanced_response.safety_warnings.extend([
                "Crisis situation detected - immediate professional help recommended",
                "Emergency resources provided"
            ])
        elif safety_level == SafetyLevel.WARNING:
            enhanced_response.safety_warnings.append(
                "Concerning content detected - professional consultation recommended"
            )
        
        # Adjust confidence for safety
        if safety_level in [SafetyLevel.CRITICAL, SafetyLevel.WARNING]:
            enhanced_response.confidence_level = min(enhanced_response.confidence_level, 0.8)
        
        return enhanced_response
    
    def _contains_crisis_keywords(self, text: str) -> bool:
        """Check if text contains crisis keywords using advanced NLP."""
        text_lower = text.lower()

        # Basic keyword check (can be bypassed)
        basic_match = any(keyword in text_lower for keyword in self.crisis_keywords)

        # Advanced semantic analysis needed here
        # TODO: Implement ML-based crisis detection to prevent evasion
        # This should include:
        # - Semantic similarity analysis
        # - Context-aware detection
        # - Multi-language support
        # - Obfuscation detection (l3t sp34k, etc.)

        return basic_match
    
    def _contains_self_harm_indicators(self, text: str) -> bool:
        """Check for self-harm indicators."""
        self_harm_patterns = [
            r"hurt\s+myself",
            r"harm\s+myself",
            r"cut\s+myself",
            r"kill\s+myself",
            r"end\s+it\s+all",
            r"not\s+worth\s+living"
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in self_harm_patterns)
    
    def _contains_substance_abuse_indicators(self, text: str) -> bool:
        """Check for substance abuse indicators."""
        substance_keywords = [
            "overdose", "pills", "alcohol", "drugs", "addiction",
            "withdrawal", "relapse", "substance", "drinking problem"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in substance_keywords)
    
    def _check_medical_disclaimer(self, response: AgentResponse) -> ComplianceCheck:
        """Check if response has appropriate medical disclaimer."""
        has_disclaimer = (
            response.medical_disclaimer and 
            len(response.medical_disclaimer.strip()) > 50
        )
        
        return ComplianceCheck(
            check_name="medical_disclaimer",
            passed=has_disclaimer,
            confidence=1.0 if has_disclaimer else 0.0,
            details="Medical disclaimer present and adequate" if has_disclaimer else "Missing or inadequate medical disclaimer",
            recommendations=[] if has_disclaimer else ["Add comprehensive medical disclaimer"]
        )
    
    def _check_crisis_response(self, response: AgentResponse) -> ComplianceCheck:
        """Check if response appropriately handles crisis situations."""
        content_lower = response.content.lower()
        
        # Check for crisis resources
        has_crisis_resources = any(
            resource in content_lower 
            for resource_list in self.emergency_resources.values()
            for resource in resource_list
        )
        
        # Check for emergency guidance
        emergency_phrases = ["emergency", "crisis", "immediate help", "call 911", "hotline"]
        has_emergency_guidance = any(phrase in content_lower for phrase in emergency_phrases)
        
        crisis_appropriate = has_crisis_resources or has_emergency_guidance
        
        return ComplianceCheck(
            check_name="crisis_response",
            passed=crisis_appropriate,
            confidence=0.9 if crisis_appropriate else 0.3,
            details="Appropriate crisis response provided" if crisis_appropriate else "May need crisis resources",
            recommendations=[] if crisis_appropriate else ["Add crisis hotlines and emergency resources"]
        )
    
    def _check_harmful_content(self, response: AgentResponse) -> ComplianceCheck:
        """Check for potentially harmful content."""
        harmful_patterns = [
            r"you should.*harm",
            r"it's okay to.*hurt",
            r"try.*overdose",
            r"end.*life.*good",
            r"suicide.*solution"
        ]
        
        content_lower = response.content.lower()
        harmful_found = any(re.search(pattern, content_lower) for pattern in harmful_patterns)
        
        return ComplianceCheck(
            check_name="harmful_content",
            passed=not harmful_found,
            confidence=0.95 if not harmful_found else 0.1,
            details="No harmful content detected" if not harmful_found else "Potentially harmful content detected",
            recommendations=[] if not harmful_found else ["Remove harmful content", "Rewrite response with safety focus"]
        )
    
    def _check_medical_advice_boundaries(self, response: AgentResponse) -> ComplianceCheck:
        """Check if response stays within appropriate boundaries."""
        inappropriate_phrases = [
            "i diagnose", "you have", "take this medication", "stop taking",
            "increase dosage", "decrease dosage", "you definitely have",
            "this is definitely", "medical diagnosis"
        ]
        
        content_lower = response.content.lower()
        boundary_violation = any(phrase in content_lower for phrase in inappropriate_phrases)
        
        return ComplianceCheck(
            check_name="medical_boundaries",
            passed=not boundary_violation,
            confidence=0.9 if not boundary_violation else 0.2,
            details="Appropriate boundaries maintained" if not boundary_violation else "Potential boundary violation",
            recommendations=[] if not boundary_violation else ["Avoid diagnostic language", "Emphasize professional consultation"]
        )
    
    def _check_professional_referral(self, response: AgentResponse) -> ComplianceCheck:
        """Check if response includes appropriate professional referrals."""
        referral_phrases = [
            "consult", "professional", "therapist", "counselor", "doctor",
            "mental health provider", "seek help", "professional help"
        ]
        
        content_lower = response.content.lower()
        has_referral = any(phrase in content_lower for phrase in referral_phrases)
        
        return ComplianceCheck(
            check_name="professional_referral",
            passed=has_referral,
            confidence=0.8 if has_referral else 0.4,
            details="Professional referral included" if has_referral else "Consider adding professional referral",
            recommendations=[] if has_referral else ["Add recommendation to consult mental health professional"]
        )
    
    def _check_confidence_levels(self, response: AgentResponse) -> ComplianceCheck:
        """Check if confidence levels are appropriate."""
        appropriate_confidence = (
            0.3 <= response.confidence_level <= 0.9 and
            response.confidence_level is not None
        )
        
        return ComplianceCheck(
            check_name="confidence_levels",
            passed=appropriate_confidence,
            confidence=0.9 if appropriate_confidence else 0.5,
            details="Confidence level appropriate" if appropriate_confidence else "Confidence level may be inappropriate",
            recommendations=[] if appropriate_confidence else ["Adjust confidence level to appropriate range"]
        )
    
    def _has_medical_disclaimer(self, content: str) -> bool:
        """Check if content already has medical disclaimer."""
        disclaimer_indicators = [
            "medical disclaimer", "not a substitute", "professional advice",
            "qualified mental health", "emergency services"
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in disclaimer_indicators)
    
    def _add_crisis_resources(self, response: AgentResponse) -> AgentResponse:
        """Add crisis resources to response."""
        crisis_section = "\n\n🆘 **Immediate Help Resources:**\n"
        
        for category, resources in self.emergency_resources.items():
            crisis_section += f"\n**{category.replace('_', ' ').title()}:**\n"
            for resource in resources:
                crisis_section += f"• {resource}\n"
        
        response.content += crisis_section
        return response
    
    async def create_safety_error_response(self, error_message: str, safety_level: SafetyLevel) -> ErrorResponse:
        """
        Create error response for safety violations.
        
        Args:
            error_message: Error message
            safety_level: Safety level that triggered the error
            
        Returns:
            Error response with safety resources
        """
        emergency_resources = []
        
        if safety_level == SafetyLevel.CRITICAL:
            emergency_resources = [
                "National Suicide Prevention Lifeline: 988",
                "Crisis Text Line: Text HOME to 741741",
                "Emergency Services: 911"
            ]
        
        return ErrorResponse(
            message=error_message,
            error_code=f"SAFETY_{safety_level.value.upper()}",
            suggested_action="Please contact a mental health professional or crisis hotline for immediate assistance.",
            emergency_resources=emergency_resources
        )
    
    def get_compliance_summary(self, checks: List[ComplianceCheck]) -> Dict[str, Any]:
        """
        Get summary of compliance check results.
        
        Args:
            checks: List of compliance checks
            
        Returns:
            Compliance summary
        """
        total_checks = len(checks)
        passed_checks = sum(1 for check in checks if check.passed)
        
        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "compliance_rate": passed_checks / total_checks if total_checks > 0 else 0.0,
            "failed_checks": [check.check_name for check in checks if not check.passed],
            "recommendations": [
                rec for check in checks 
                for rec in check.recommendations
            ],
            "overall_safe": passed_checks == total_checks
        }
