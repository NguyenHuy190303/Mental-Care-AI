#!/usr/bin/env python3
"""
Test script to verify configuration and logging setup.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_environment_variables():
    """Test environment variable loading."""
    print("Testing environment variable configuration...")
    
    try:
        from config.settings import settings
        
        print(f"✓ App Name: {settings.APP_NAME}")
        print(f"✓ Environment: {settings.ENVIRONMENT}")
        print(f"✓ Debug Mode: {settings.DEBUG}")
        print(f"✓ API Host: {settings.API_HOST}")
        print(f"✓ API Port: {settings.API_PORT}")
        print(f"✓ Database URL: {settings.DATABASE_URL[:50]}...")
        print(f"✓ ChromaDB Host: {settings.CHROMADB_HOST}")
        print(f"✓ Redis URL: {settings.REDIS_URL}")
        print(f"✓ Log Level: {settings.LOG_LEVEL}")
        
        # Test directory creation
        settings.create_directories()
        print("✓ Data directories created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading settings: {e}")
        return False

def test_logging_configuration():
    """Test logging configuration."""
    print("\nTesting logging configuration...")
    
    try:
        from config.logging import get_logger
        
        # Create test logger
        logger = get_logger("test_config")
        
        # Test different log levels
        logger.debug("Debug message test")
        logger.info("Info message test")
        logger.warning("Warning message test")
        logger.error("Error message test")
        
        print("✓ Logging configuration working correctly")
        print("✓ Check logs/ directory for log files")
        
        return True
        
    except Exception as e:
        print(f"✗ Error with logging configuration: {e}")
        return False

def test_directory_structure():
    """Test that all required directories exist."""
    print("\nTesting directory structure...")
    
    required_dirs = [
        "data",
        "data/cache",
        "data/user_storage", 
        "data/index_storage",
        "data/ingestion_storage",
        "logs",
        "config",
        "src",
        "backend/src",
        "frontend/src",
        "tests"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - Missing")
            all_exist = False
    
    return all_exist

def test_requirements():
    """Test that key requirements are available."""
    print("\nTesting key requirements availability...")
    
    key_modules = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "sqlalchemy",
        "redis",
        "openai",
        "structlog"
    ]
    
    available_modules = []
    missing_modules = []
    
    for module in key_modules:
        try:
            __import__(module)
            available_modules.append(module)
            print(f"✓ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"✗ {module} - Not installed")
    
    if missing_modules:
        print(f"\nMissing modules: {', '.join(missing_modules)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Run all configuration tests."""
    print("Mental Health Agent - Configuration Test")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Logging Configuration", test_logging_configuration), 
        ("Directory Structure", test_directory_structure),
        ("Requirements", test_requirements)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✓ All configuration tests passed!")
        print("The project foundation is properly set up.")
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()