#!/usr/bin/env python3
"""
Sage - Environment Validation Script
Validates environment configuration for production readiness
"""

import os
import sys
import re
import base64
from pathlib import Path
from typing import List, Tuple, Dict

class EnvironmentValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        
    def validate_required_vars(self) -> None:
        """Validate required environment variables."""
        required_vars = [
            'OPENAI_API_KEY',
            'JWT_SECRET_KEY',
            'JWT_REFRESH_SECRET_KEY',
            'POSTGRES_PASSWORD',
            'REDIS_PASSWORD',
            'ENCRYPTION_KEY',
            'FIELD_ENCRYPTION_KEY',
            'CRISIS_ENCRYPTION_KEY',
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.errors.append(f"Missing required environment variables: {', '.join(missing_vars)}")
        else:
            self.info.append("✅ All required environment variables are present")
    
    def validate_openai_key(self) -> None:
        """Validate OpenAI API key format."""
        api_key = os.getenv('OPENAI_API_KEY', '')
        
        if not api_key.startswith('sk-'):
            self.errors.append("OPENAI_API_KEY must start with 'sk-'")
        elif len(api_key) < 50:
            self.errors.append("OPENAI_API_KEY appears to be too short")
        else:
            self.info.append("✅ OpenAI API key format is valid")
    
    def validate_jwt_secrets(self) -> None:
        """Validate JWT secret keys."""
        jwt_secret = os.getenv('JWT_SECRET_KEY', '')
        jwt_refresh_secret = os.getenv('JWT_REFRESH_SECRET_KEY', '')
        
        if len(jwt_secret) < 32:
            self.errors.append("JWT_SECRET_KEY must be at least 32 characters long")
        
        if len(jwt_refresh_secret) < 32:
            self.errors.append("JWT_REFRESH_SECRET_KEY must be at least 32 characters long")
        
        if jwt_secret == jwt_refresh_secret:
            self.errors.append("JWT_SECRET_KEY and JWT_REFRESH_SECRET_KEY must be different")
        
        if len(jwt_secret) >= 32 and len(jwt_refresh_secret) >= 32 and jwt_secret != jwt_refresh_secret:
            self.info.append("✅ JWT secrets are properly configured")
    
    def validate_encryption_keys(self) -> None:
        """Validate encryption keys."""
        encryption_keys = [
            'ENCRYPTION_KEY',
            'FIELD_ENCRYPTION_KEY', 
            'CRISIS_ENCRYPTION_KEY'
        ]
        
        for key_name in encryption_keys:
            key_value = os.getenv(key_name, '')
            
            if not key_value:
                self.errors.append(f"{key_name} is required")
                continue
            
            try:
                # Try to decode as base64
                decoded = base64.b64decode(key_value)
                if len(decoded) != 32:
                    self.errors.append(f"{key_name} must be a 32-byte key encoded in base64")
                else:
                    self.info.append(f"✅ {key_name} is properly formatted")
            except Exception:
                self.errors.append(f"{key_name} must be a valid base64-encoded 32-byte key")
    
    def validate_passwords(self) -> None:
        """Validate password strength."""
        passwords = {
            'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD', '')
        }
        
        for name, password in passwords.items():
            if len(password) < 12:
                self.errors.append(f"{name} must be at least 12 characters long")
            elif len(password) < 16:
                self.warnings.append(f"{name} should be at least 16 characters long for better security")
            else:
                self.info.append(f"✅ {name} meets security requirements")
    
    def validate_security_settings(self) -> None:
        """Validate security settings."""
        security_settings = {
            'ENABLE_CRISIS_DETECTION': 'true',
            'ENABLE_CONTENT_FILTERING': 'true',
            'ENABLE_SAFETY_LOGGING': 'true',
            'ENABLE_AUDIT_LOGGING': 'true',
            'GDPR_COMPLIANCE': 'true',
            'HIPAA_COMPLIANCE': 'true',
            'ENABLE_PROMPT_INJECTION_PROTECTION': 'true',
            'ENABLE_SECURITY_MONITORING': 'true'
        }
        
        for setting, expected_value in security_settings.items():
            actual_value = os.getenv(setting, '').lower()
            if actual_value != expected_value:
                self.warnings.append(f"{setting} should be set to '{expected_value}' for maximum security")
        
        self.info.append("✅ Security settings validation completed")
    
    def validate_production_settings(self) -> None:
        """Validate production-specific settings."""
        environment = os.getenv('ENVIRONMENT', '').lower()
        debug = os.getenv('DEBUG', '').lower()
        
        if environment == 'production':
            if debug == 'true':
                self.errors.append("DEBUG must be 'false' in production environment")
            
            # Check for development-only settings
            dev_settings = [
                'ENABLE_DEBUG_ENDPOINTS',
                'ENABLE_TEST_ENDPOINTS',
                'ENABLE_SWAGGER_UI'
            ]
            
            for setting in dev_settings:
                if os.getenv(setting, '').lower() == 'true':
                    self.warnings.append(f"{setting} should be 'false' in production")
        
        self.info.append("✅ Production settings validation completed")
    
    def validate_cors_origins(self) -> None:
        """Validate CORS origins."""
        cors_origins = os.getenv('CORS_ORIGINS', '')
        
        if 'localhost' in cors_origins and os.getenv('ENVIRONMENT') == 'production':
            self.warnings.append("CORS_ORIGINS contains localhost in production environment")
        
        if not cors_origins or cors_origins == '["*"]':
            self.errors.append("CORS_ORIGINS must be properly configured (not wildcard)")
        
        self.info.append("✅ CORS origins validation completed")
    
    def validate_database_urls(self) -> None:
        """Validate database connection URLs."""
        database_url = os.getenv('DATABASE_URL', '')
        redis_url = os.getenv('REDIS_URL', '')
        
        if not database_url.startswith('postgresql://'):
            self.errors.append("DATABASE_URL must be a valid PostgreSQL connection string")
        
        if not redis_url.startswith('redis://'):
            self.errors.append("REDIS_URL must be a valid Redis connection string")
        
        # Check for passwords in URLs
        if 'localhost' not in database_url and 'password' in database_url.lower():
            postgres_password = os.getenv('POSTGRES_PASSWORD', '')
            if postgres_password not in database_url:
                self.warnings.append("DATABASE_URL password doesn't match POSTGRES_PASSWORD")
        
        self.info.append("✅ Database URLs validation completed")
    
    def validate_file_permissions(self) -> None:
        """Validate file permissions."""
        env_file = Path('.env')
        
        if env_file.exists():
            # Check if .env file is readable by others (Unix-like systems)
            try:
                stat_info = env_file.stat()
                if stat_info.st_mode & 0o044:  # Check if readable by group or others
                    self.warnings.append(".env file should not be readable by group/others (chmod 600)")
                else:
                    self.info.append("✅ .env file permissions are secure")
            except:
                self.info.append("ℹ️  Could not check .env file permissions (Windows system?)")
        
    def run_validation(self) -> Dict[str, List[str]]:
        """Run all validations."""
        print("🔍 Sage - Environment Validation")
        print("=" * 50)
        
        # Load .env file if it exists
        env_file = Path('.env')
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv()
            print("📁 Loaded .env file")
        else:
            print("⚠️  No .env file found, checking system environment variables")
        
        print("\n🔍 Running validation checks...")
        
        # Run all validation methods
        self.validate_required_vars()
        self.validate_openai_key()
        self.validate_jwt_secrets()
        self.validate_encryption_keys()
        self.validate_passwords()
        self.validate_security_settings()
        self.validate_production_settings()
        self.validate_cors_origins()
        self.validate_database_urls()
        self.validate_file_permissions()
        
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }
    
    def print_results(self, results: Dict[str, List[str]]) -> bool:
        """Print validation results."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION RESULTS")
        print("=" * 50)
        
        # Print errors
        if results['errors']:
            print("\n❌ ERRORS (Must be fixed):")
            for error in results['errors']:
                print(f"   • {error}")
        
        # Print warnings
        if results['warnings']:
            print("\n⚠️  WARNINGS (Should be addressed):")
            for warning in results['warnings']:
                print(f"   • {warning}")
        
        # Print info
        if results['info']:
            print("\n✅ PASSED CHECKS:")
            for info in results['info']:
                print(f"   • {info}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📈 SUMMARY")
        print("=" * 50)
        
        error_count = len(results['errors'])
        warning_count = len(results['warnings'])
        passed_count = len(results['info'])
        
        print(f"❌ Errors: {error_count}")
        print(f"⚠️  Warnings: {warning_count}")
        print(f"✅ Passed: {passed_count}")
        
        if error_count == 0:
            if warning_count == 0:
                print("\n🎉 ENVIRONMENT IS PRODUCTION READY!")
                print("All validation checks passed successfully.")
            else:
                print("\n✅ ENVIRONMENT IS READY WITH WARNINGS")
                print("Consider addressing the warnings for optimal security.")
            return True
        else:
            print("\n❌ ENVIRONMENT IS NOT READY")
            print("Please fix the errors before deploying to production.")
            return False

def main():
    """Main function."""
    try:
        # Try to import dotenv
        try:
            from dotenv import load_dotenv
        except ImportError:
            print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
            print("Checking system environment variables only...\n")
        
        validator = EnvironmentValidator()
        results = validator.run_validation()
        is_ready = validator.print_results(results)
        
        if is_ready:
            print("\n🚀 Next steps:")
            print("1. docker-compose up -d")
            print("2. Test health endpoint: curl http://localhost:8000/api/health")
            print("3. Monitor logs: docker-compose logs -f")
            sys.exit(0)
        else:
            print("\n🔧 Fix the errors and run validation again:")
            print("python scripts/validate-environment.py")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Validation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()