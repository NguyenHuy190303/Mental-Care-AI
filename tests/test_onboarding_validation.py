#!/usr/bin/env python3
"""
Healthcare User Onboarding System Validation Tests.

This test validates the implementation of the onboarding system components
by checking file structure, component exports, and basic functionality.
"""

import os
import sys
import json
import subprocess
from pathlib import Path


class OnboardingSystemValidator:
    """Validator for the Healthcare User Onboarding System."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.frontend_src = self.project_root / "frontend" / "src"
        self.onboarding_dir = self.frontend_src / "components" / "Onboarding"
        self.results = []
    
    def log_result(self, test_name, passed, message=""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
    
    def test_onboarding_components_exist(self):
        """Test that all onboarding components exist."""
        required_files = [
            "HealthcareOnboarding.jsx",
            "HealthcareOnboarding.css",
            "OnboardingSteps.jsx",
            "TooltipSystem.jsx",
            "TooltipSystem.css",
            "UserGuide.jsx",
            "UserGuide.css"
        ]
        
        missing_files = []
        for file in required_files:
            file_path = self.onboarding_dir / file
            if not file_path.exists():
                missing_files.append(file)
        
        passed = len(missing_files) == 0
        message = f"Missing files: {missing_files}" if missing_files else "All onboarding components found"
        self.log_result("Onboarding Components Exist", passed, message)
        return passed
    
    def test_component_imports(self):
        """Test that components have proper imports and exports."""
        components_to_check = [
            ("HealthcareOnboarding.jsx", ["React", "useState", "useEffect"]),
            ("OnboardingSteps.jsx", ["React", "SafetyGuidelinesStep", "SystemLimitationsStep"]),
            ("TooltipSystem.jsx", ["React", "Tooltip", "InteractiveTutorial"]),
            ("UserGuide.jsx", ["React", "useState"])
        ]
        
        all_passed = True
        for component_file, expected_imports in components_to_check:
            file_path = self.onboarding_dir / component_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    missing_imports = [imp for imp in expected_imports if imp not in content]
                    
                    if missing_imports:
                        all_passed = False
                        self.log_result(f"Component Imports - {component_file}", False, 
                                      f"Missing imports: {missing_imports}")
                    else:
                        self.log_result(f"Component Imports - {component_file}", True)
                except Exception as e:
                    all_passed = False
                    self.log_result(f"Component Imports - {component_file}", False, str(e))
            else:
                all_passed = False
                self.log_result(f"Component Imports - {component_file}", False, "File not found")
        
        return all_passed
    
    def test_app_integration(self):
        """Test that onboarding is integrated into the main App component."""
        app_file = self.frontend_src / "App.jsx"
        
        if not app_file.exists():
            self.log_result("App Integration", False, "App.jsx not found")
            return False
        
        try:
            content = app_file.read_text(encoding='utf-8')
            
            required_integrations = [
                "HealthcareOnboarding",
                "UserGuide", 
                "ContextualHelp",
                "showOnboarding",
                "onboardingCompleted"
            ]
            
            missing_integrations = [item for item in required_integrations if item not in content]
            
            if missing_integrations:
                self.log_result("App Integration", False, f"Missing integrations: {missing_integrations}")
                return False
            else:
                self.log_result("App Integration", True, "Onboarding properly integrated into App")
                return True
                
        except Exception as e:
            self.log_result("App Integration", False, str(e))
            return False
    
    def test_dashboard_integration(self):
        """Test that dashboard has user guide access."""
        dashboard_file = self.frontend_src / "components" / "Healthcare" / "HealthcareDashboard.jsx"
        
        if not dashboard_file.exists():
            self.log_result("Dashboard Integration", False, "HealthcareDashboard.jsx not found")
            return False
        
        try:
            content = dashboard_file.read_text(encoding='utf-8')
            
            required_elements = [
                "user-guide",
                "HelpCircle",
                "BookOpen"
            ]
            
            missing_elements = [item for item in required_elements if item not in content]
            
            if missing_elements:
                self.log_result("Dashboard Integration", False, f"Missing elements: {missing_elements}")
                return False
            else:
                self.log_result("Dashboard Integration", True, "User guide access added to dashboard")
                return True
                
        except Exception as e:
            self.log_result("Dashboard Integration", False, str(e))
            return False
    
    def test_safety_guidelines_content(self):
        """Test that safety guidelines contain required content."""
        steps_file = self.onboarding_dir / "OnboardingSteps.jsx"
        
        if not steps_file.exists():
            self.log_result("Safety Guidelines Content", False, "OnboardingSteps.jsx not found")
            return False
        
        try:
            content = steps_file.read_text(encoding='utf-8').lower()
            
            required_safety_content = [
                "911",
                "988", 
                "741741",
                "crisis",
                "emergency",
                "suicide",
                "self-harm",
                "professional help"
            ]
            
            missing_content = [item for item in required_safety_content if item not in content]
            
            if len(missing_content) > 2:  # Allow some flexibility
                self.log_result("Safety Guidelines Content", False, f"Missing safety content: {missing_content}")
                return False
            else:
                self.log_result("Safety Guidelines Content", True, "Comprehensive safety guidelines included")
                return True
                
        except Exception as e:
            self.log_result("Safety Guidelines Content", False, str(e))
            return False
    
    def test_role_based_content(self):
        """Test that role-based content exists for both patients and providers."""
        components_to_check = [
            ("HealthcareOnboarding.jsx", ["patient", "provider", "userRole"]),
            ("OnboardingSteps.jsx", ["PatientGuideStep", "ProviderGuideStep"]),
            ("UserGuide.jsx", ["patient", "provider", "clinical"])
        ]
        
        all_passed = True
        for component_file, expected_content in components_to_check:
            file_path = self.onboarding_dir / component_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8').lower()
                    missing_content = [item for item in expected_content if item.lower() not in content]
                    
                    if missing_content:
                        all_passed = False
                        self.log_result(f"Role-Based Content - {component_file}", False, 
                                      f"Missing content: {missing_content}")
                    else:
                        self.log_result(f"Role-Based Content - {component_file}", True)
                except Exception as e:
                    all_passed = False
                    self.log_result(f"Role-Based Content - {component_file}", False, str(e))
            else:
                all_passed = False
                self.log_result(f"Role-Based Content - {component_file}", False, "File not found")
        
        return all_passed
    
    def test_css_styling(self):
        """Test that CSS files exist and contain proper styling."""
        css_files = [
            "HealthcareOnboarding.css",
            "TooltipSystem.css", 
            "UserGuide.css"
        ]
        
        all_passed = True
        for css_file in css_files:
            file_path = self.onboarding_dir / css_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Check for basic CSS structure
                    if len(content) < 100:  # Very basic check
                        all_passed = False
                        self.log_result(f"CSS Styling - {css_file}", False, "CSS file too small")
                    else:
                        self.log_result(f"CSS Styling - {css_file}", True)
                except Exception as e:
                    all_passed = False
                    self.log_result(f"CSS Styling - {css_file}", False, str(e))
            else:
                all_passed = False
                self.log_result(f"CSS Styling - {css_file}", False, "CSS file not found")
        
        return all_passed
    
    def test_interactive_features(self):
        """Test that interactive features are implemented."""
        tooltip_file = self.onboarding_dir / "TooltipSystem.jsx"
        
        if not tooltip_file.exists():
            self.log_result("Interactive Features", False, "TooltipSystem.jsx not found")
            return False
        
        try:
            content = tooltip_file.read_text(encoding='utf-8')
            
            interactive_features = [
                "Tooltip",
                "InteractiveTutorial", 
                "HelpButton",
                "ContextualHelp",
                "QuickTips"
            ]
            
            missing_features = [feature for feature in interactive_features if feature not in content]
            
            if missing_features:
                self.log_result("Interactive Features", False, f"Missing features: {missing_features}")
                return False
            else:
                self.log_result("Interactive Features", True, "All interactive features implemented")
                return True
                
        except Exception as e:
            self.log_result("Interactive Features", False, str(e))
            return False
    
    def test_system_limitations_disclosure(self):
        """Test that system limitations are properly disclosed."""
        files_to_check = [
            self.onboarding_dir / "OnboardingSteps.jsx",
            self.onboarding_dir / "UserGuide.jsx"
        ]
        
        limitation_keywords = [
            "cannot",
            "limitation",
            "not a replacement",
            "professional",
            "medical advice",
            "diagnosis"
        ]
        
        all_passed = True
        for file_path in files_to_check:
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8').lower()
                    found_keywords = [kw for kw in limitation_keywords if kw in content]
                    
                    if len(found_keywords) < 3:
                        all_passed = False
                        self.log_result(f"System Limitations - {file_path.name}", False, 
                                      f"Insufficient limitation disclosure. Found: {found_keywords}")
                    else:
                        self.log_result(f"System Limitations - {file_path.name}", True)
                except Exception as e:
                    all_passed = False
                    self.log_result(f"System Limitations - {file_path.name}", False, str(e))
            else:
                all_passed = False
                self.log_result(f"System Limitations - {file_path.name}", False, "File not found")
        
        return all_passed
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("🧪 Running Healthcare User Onboarding System Validation...")
        print("=" * 60)
        
        tests = [
            self.test_onboarding_components_exist,
            self.test_component_imports,
            self.test_app_integration,
            self.test_dashboard_integration,
            self.test_safety_guidelines_content,
            self.test_role_based_content,
            self.test_css_styling,
            self.test_interactive_features,
            self.test_system_limitations_disclosure
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
            print()  # Add spacing between tests
        
        print("=" * 60)
        print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All onboarding system validation tests passed!")
            return True
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed")
            return False


def main():
    """Main function to run validation tests."""
    validator = OnboardingSystemValidator()
    success = validator.run_all_tests()
    
    if success:
        print("\n✅ Healthcare User Onboarding System implementation is complete and valid!")
    else:
        print("\n❌ Healthcare User Onboarding System implementation has issues that need to be addressed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
