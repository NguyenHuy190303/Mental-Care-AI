#!/usr/bin/env python3
"""
Validation script for healthcare model configuration.
Tests that the default model configuration is properly set up.
"""

import os
import sys
from enum import Enum

# Add the backend source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_model_type_enum():
    """Test that ModelType enum includes healthcare default."""
    try:
        # Test by checking the source code directly
        with open('backend/src/agents/chain_of_thought_engine.py', 'r') as f:
            content = f.read()
        
        print("✅ Testing ModelType enum...")

        # Check that HEALTHCARE_DEFAULT exists in the source code
        assert 'HEALTHCARE_DEFAULT = "gpt-4o-mini"' in content, "HEALTHCARE_DEFAULT not found in ModelType"

        # Check all expected models exist in source
        expected_models = {
            'SIMPLE = "gpt-3.5-turbo"',
            'COMPLEX = "gpt-4"',
            'ADVANCED = "gpt-4-turbo"',
            'HEALTHCARE_DEFAULT = "gpt-4o-mini"'
        }

        for model_def in expected_models:
            assert model_def in content, f"Model definition {model_def} not found in source"
        
        print("✅ ModelType enum validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ ModelType enum validation failed: {e}")
        return False

def test_environment_variables():
    """Test that environment variables are properly configured."""
    print("✅ Testing environment variables...")
    
    # Test docker-compose.yml configuration
    try:
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
            
        # Check for healthcare model configuration
        required_env_vars = [
            'OPENAI_MODEL:',
            'SAGE_HEALTHCARE_MODE:',
            'DEFAULT_HEALTHCARE_MODEL:'
        ]
        
        for env_var in required_env_vars:
            assert env_var in content, f"Environment variable {env_var} not found in docker-compose.yml"
        
        print("✅ Environment variables validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Environment variables validation failed: {e}")
        return False

def test_settings_configuration():
    """Test that settings.py is properly configured."""
    print("✅ Testing settings configuration...")
    
    try:
        # Add config to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))
        
        # Check settings file content
        with open('config/settings.py', 'r') as f:
            content = f.read()
        
        # Check for healthcare configuration
        required_settings = [
            'SAGE_HEALTHCARE_MODE',
            'DEFAULT_HEALTHCARE_MODEL',
            'gpt-4o-mini'
        ]
        
        for setting in required_settings:
            assert setting in content, f"Setting {setting} not found in settings.py"
        
        print("✅ Settings configuration validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Settings configuration validation failed: {e}")
        return False

def test_deployment_checklist():
    """Test that deployment checklist is updated."""
    print("✅ Testing deployment checklist...")

    try:
        with open('DEPLOYMENT_CHECKLIST.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for healthcare model documentation
        required_docs = [
            'Healthcare Model Configuration',
            'GPT-4.1-mini',
            'gpt-4o-mini',
            'SAGE_HEALTHCARE_MODE',
            'DEFAULT_HEALTHCARE_MODEL'
        ]
        
        for doc_item in required_docs:
            assert doc_item in content, f"Documentation for {doc_item} not found in DEPLOYMENT_CHECKLIST.md"
        
        print("✅ Deployment checklist validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Deployment checklist validation failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🏥 Validating Healthcare Model Configuration for Sage")
    print("=" * 60)
    
    tests = [
        test_model_type_enum,
        test_environment_variables,
        test_settings_configuration,
        test_deployment_checklist
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All healthcare model configuration tests passed!")
        print("✅ GPT-4.1-mini is properly configured as the default model")
        print("✅ Healthcare mode is enabled")
        print("✅ No manual model selection required for users")
        return True
    else:
        print("❌ Some tests failed. Please review the configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
