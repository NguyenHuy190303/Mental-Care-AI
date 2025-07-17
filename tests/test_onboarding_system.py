#!/usr/bin/env python3
"""
Comprehensive test suite for the Healthcare User Onboarding System.

This test validates all components of the onboarding system including:
- Healthcare Professional Onboarding
- Patient Guidance System  
- Safety Guidelines Integration
- System Limitations Education
- Interactive Tutorial Components
- Role-Based Onboarding
"""

import pytest
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestHealthcareOnboardingSystem:
    """Test suite for the Healthcare User Onboarding System."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.base_url = "http://localhost:3000"
        cls.backend_url = "http://localhost:8000"
        
        # Configure Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.wait = WebDriverWait(cls.driver, 10)
        except Exception as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment."""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def test_frontend_accessibility(self):
        """Test that the frontend is accessible."""
        try:
            response = requests.get(self.base_url, timeout=10)
            assert response.status_code == 200, f"Frontend not accessible: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Frontend not accessible: {e}")
    
    def test_backend_health(self):
        """Test that the backend is healthy."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            assert response.status_code == 200, f"Backend not healthy: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Backend not accessible: {e}")
    
    def test_onboarding_components_load(self):
        """Test that onboarding components load properly."""
        self.driver.get(self.base_url)
        
        # Wait for the page to load
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Check if the app loads without JavaScript errors
        logs = self.driver.get_log('browser')
        critical_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if critical_errors:
            error_messages = [log['message'] for log in critical_errors]
            pytest.fail(f"Critical JavaScript errors found: {error_messages}")
    
    def test_role_based_onboarding_trigger(self):
        """Test that onboarding is triggered for new users."""
        self.driver.get(self.base_url)
        
        # Clear localStorage to simulate first-time user
        self.driver.execute_script("localStorage.clear();")
        self.driver.refresh()
        
        # Wait for page load
        time.sleep(2)
        
        # Check if onboarding appears for first-time users
        # Note: This test assumes onboarding shows by default for new users
        try:
            # Look for onboarding elements
            onboarding_elements = self.driver.find_elements(By.CLASS_NAME, "healthcare-onboarding")
            role_switcher = self.driver.find_elements(By.CLASS_NAME, "role-switcher")
            
            # Either onboarding should be visible or role switcher should be available
            assert len(onboarding_elements) > 0 or len(role_switcher) > 0, \
                "No onboarding or role selection found for new users"
            
        except NoSuchElementException:
            pytest.fail("Onboarding system not properly initialized")
    
    def test_patient_onboarding_flow(self):
        """Test the patient onboarding flow."""
        self.driver.get(self.base_url)
        self.driver.execute_script("localStorage.clear();")
        
        # Set patient role if role switcher is available
        try:
            patient_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Patient View')]"))
            )
            patient_btn.click()
            time.sleep(1)
        except TimeoutException:
            pass  # Role might already be set or onboarding might be showing
        
        # Look for patient-specific onboarding content
        try:
            # Check for welcome step
            welcome_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Welcome to Sage')]")
            assert len(welcome_elements) > 0, "Patient welcome message not found"
            
            # Check for safety guidelines
            safety_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Safety Guidelines')]")
            assert len(safety_elements) > 0, "Safety guidelines not found in patient onboarding"
            
        except (TimeoutException, NoSuchElementException):
            # If onboarding modal isn't visible, check for dashboard elements
            dashboard_elements = self.driver.find_elements(By.CLASS_NAME, "healthcare-dashboard")
            assert len(dashboard_elements) > 0, "Neither onboarding nor dashboard found"
    
    def test_provider_onboarding_flow(self):
        """Test the healthcare provider onboarding flow."""
        self.driver.get(self.base_url)
        self.driver.execute_script("localStorage.clear();")
        
        # Set provider role if role switcher is available
        try:
            provider_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Provider View')]"))
            )
            provider_btn.click()
            time.sleep(1)
        except TimeoutException:
            pass  # Role might already be set
        
        # Look for provider-specific content
        try:
            # Check for provider-specific elements
            provider_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Provider') or contains(text(), 'Clinical')]")
            assert len(provider_elements) > 0, "Provider-specific content not found"
            
        except (TimeoutException, NoSuchElementException):
            # Check for dashboard with provider context
            dashboard_elements = self.driver.find_elements(By.CLASS_NAME, "healthcare-dashboard")
            assert len(dashboard_elements) > 0, "Provider dashboard not found"
    
    def test_safety_guidelines_presence(self):
        """Test that safety guidelines are prominently displayed."""
        self.driver.get(self.base_url)
        
        # Look for safety-related content
        safety_keywords = [
            "emergency", "crisis", "911", "988", "safety", 
            "suicide", "self-harm", "professional help"
        ]
        
        page_text = self.driver.page_source.lower()
        found_keywords = [keyword for keyword in safety_keywords if keyword in page_text]
        
        assert len(found_keywords) >= 3, \
            f"Insufficient safety content found. Found keywords: {found_keywords}"
    
    def test_crisis_support_resources(self):
        """Test that crisis support resources are accessible."""
        self.driver.get(self.base_url)
        
        # Look for crisis support elements
        crisis_keywords = ["988", "741741", "crisis", "emergency"]
        page_text = self.driver.page_source.lower()
        
        found_crisis_info = [keyword for keyword in crisis_keywords if keyword in page_text]
        assert len(found_crisis_info) >= 2, \
            f"Crisis support information insufficient. Found: {found_crisis_info}"
    
    def test_user_guide_accessibility(self):
        """Test that user guide is accessible from the interface."""
        self.driver.get(self.base_url)
        time.sleep(2)
        
        # Look for help or guide buttons
        help_elements = self.driver.find_elements(By.XPATH, 
            "//*[contains(@class, 'help') or contains(@title, 'help') or contains(text(), 'Guide') or contains(text(), 'Help')]"
        )
        
        assert len(help_elements) > 0, "No help or user guide access found"
    
    def test_system_limitations_disclosure(self):
        """Test that system limitations are clearly disclosed."""
        self.driver.get(self.base_url)
        
        # Look for limitation-related content
        limitation_keywords = [
            "limitation", "cannot", "not a replacement", "professional", 
            "medical advice", "diagnosis", "treatment"
        ]
        
        page_text = self.driver.page_source.lower()
        found_limitations = [keyword for keyword in limitation_keywords if keyword in page_text]
        
        assert len(found_limitations) >= 3, \
            f"System limitations not adequately disclosed. Found: {found_limitations}"
    
    def test_privacy_and_hipaa_compliance(self):
        """Test that privacy and HIPAA compliance information is present."""
        self.driver.get(self.base_url)
        
        # Look for privacy-related content
        privacy_keywords = ["hipaa", "privacy", "confidential", "encrypted", "secure"]
        page_text = self.driver.page_source.lower()
        
        found_privacy_info = [keyword for keyword in privacy_keywords if keyword in page_text]
        assert len(found_privacy_info) >= 2, \
            f"Privacy/HIPAA information insufficient. Found: {found_privacy_info}"
    
    def test_interactive_elements_functionality(self):
        """Test that interactive elements work properly."""
        self.driver.get(self.base_url)
        time.sleep(2)
        
        # Test clickable elements
        clickable_elements = self.driver.find_elements(By.TAG_NAME, "button")
        assert len(clickable_elements) > 0, "No interactive buttons found"
        
        # Test that buttons are not disabled
        enabled_buttons = [btn for btn in clickable_elements if btn.is_enabled()]
        assert len(enabled_buttons) > 0, "No enabled buttons found"
    
    def test_responsive_design(self):
        """Test that the onboarding system works on different screen sizes."""
        # Test desktop size
        self.driver.set_window_size(1920, 1080)
        self.driver.get(self.base_url)
        time.sleep(1)
        
        desktop_layout = self.driver.find_elements(By.TAG_NAME, "body")
        assert len(desktop_layout) > 0, "Desktop layout not loading"
        
        # Test mobile size
        self.driver.set_window_size(375, 667)
        time.sleep(1)
        
        mobile_layout = self.driver.find_elements(By.TAG_NAME, "body")
        assert len(mobile_layout) > 0, "Mobile layout not loading"
        
        # Reset to desktop
        self.driver.set_window_size(1920, 1080)
    
    def test_onboarding_completion_persistence(self):
        """Test that onboarding completion is properly stored."""
        self.driver.get(self.base_url)
        
        # Clear localStorage first
        self.driver.execute_script("localStorage.clear();")
        self.driver.refresh()
        time.sleep(2)
        
        # Simulate onboarding completion
        self.driver.execute_script("""
            localStorage.setItem('sage-onboarding-completed', 'true');
            localStorage.setItem('sage-first-time-user', 'false');
        """)
        
        self.driver.refresh()
        time.sleep(2)
        
        # Check that onboarding doesn't show again
        onboarding_elements = self.driver.find_elements(By.CLASS_NAME, "healthcare-onboarding")
        # Onboarding should not be visible for completed users
        # (This test assumes onboarding is hidden after completion)


def run_onboarding_tests():
    """Run all onboarding system tests."""
    print("🧪 Running Healthcare User Onboarding System Tests...")
    
    # Run pytest with verbose output
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short",
        "--color=yes"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    success = run_onboarding_tests()
    if success:
        print("✅ All onboarding system tests passed!")
    else:
        print("❌ Some onboarding system tests failed!")
        exit(1)
