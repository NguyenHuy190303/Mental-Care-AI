"""
Advanced Encryption System for Mental Health Agent
HIPAA/GDPR compliant encryption for sensitive health data.
"""

import os
import base64
import hashlib
from typing import Optional, Union, Dict, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import secrets

from ..monitoring.logging_config import get_logger

logger = get_logger("security.encryption")


class HealthDataEncryption:
    """HIPAA-compliant encryption for mental health data."""
    
    def __init__(self):
        """Initialize encryption system."""
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)
        
        # Initialize field-specific encryption keys
        self.field_keys = {
            'conversation_content': self._derive_field_key('conversation'),
            'user_profile': self._derive_field_key('profile'),
            'crisis_logs': self._derive_field_key('crisis'),
            'medical_data': self._derive_field_key('medical')
        }
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key."""
        # In production, this should come from a secure key management service
        master_key_b64 = os.getenv('ENCRYPTION_MASTER_KEY')
        
        if master_key_b64:
            try:
                return base64.urlsafe_b64decode(master_key_b64)
            except Exception as e:
                logger.error(f"Invalid master key format: {e}")
                raise ValueError("Invalid encryption master key")
        
        # Generate new key if not provided (development only)
        if os.getenv('ENVIRONMENT') == 'development':
            logger.warning("Generating new master key for development")
            return Fernet.generate_key()
        
        raise ValueError("Master encryption key not configured")
    
    def _derive_field_key(self, field_name: str) -> Fernet:
        """Derive field-specific encryption key."""
        # Use PBKDF2 to derive field-specific keys
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=field_name.encode('utf-8').ljust(16, b'\0')[:16],
            iterations=100000,
        )
        
        field_key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(field_key)
    
    def encrypt_conversation_content(self, content: str) -> str:
        """Encrypt conversation content."""
        try:
            encrypted_data = self.field_keys['conversation_content'].encrypt(
                content.encode('utf-8')
            )
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt conversation content: {e}")
            raise
    
    def decrypt_conversation_content(self, encrypted_content: str) -> str:
        """Decrypt conversation content."""
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_content.encode('utf-8'))
            decrypted_data = self.field_keys['conversation_content'].decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt conversation content: {e}")
            raise
    
    def encrypt_user_profile(self, profile_data: Dict[str, Any]) -> str:
        """Encrypt user profile data."""
        try:
            import json
            profile_json = json.dumps(profile_data, sort_keys=True)
            encrypted_data = self.field_keys['user_profile'].encrypt(
                profile_json.encode('utf-8')
            )
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt user profile: {e}")
            raise
    
    def decrypt_user_profile(self, encrypted_profile: str) -> Dict[str, Any]:
        """Decrypt user profile data."""
        try:
            import json
            encrypted_data = base64.urlsafe_b64decode(encrypted_profile.encode('utf-8'))
            decrypted_data = self.field_keys['user_profile'].decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to decrypt user profile: {e}")
            raise
    
    def encrypt_crisis_log(self, log_data: Dict[str, Any]) -> str:
        """Encrypt crisis intervention logs with highest security."""
        try:
            import json
            
            # Add timestamp and integrity hash
            log_data['encrypted_at'] = str(int(time.time()))
            log_json = json.dumps(log_data, sort_keys=True)
            
            # Double encryption for crisis data
            first_encryption = self.field_keys['crisis_logs'].encrypt(
                log_json.encode('utf-8')
            )
            second_encryption = self.fernet.encrypt(first_encryption)
            
            return base64.urlsafe_b64encode(second_encryption).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt crisis log: {e}")
            raise
    
    def decrypt_crisis_log(self, encrypted_log: str) -> Dict[str, Any]:
        """Decrypt crisis intervention logs."""
        try:
            import json
            
            # Double decryption for crisis data
            encrypted_data = base64.urlsafe_b64decode(encrypted_log.encode('utf-8'))
            first_decryption = self.fernet.decrypt(encrypted_data)
            second_decryption = self.field_keys['crisis_logs'].decrypt(first_decryption)
            
            return json.loads(second_decryption.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to decrypt crisis log: {e}")
            raise
    
    def encrypt_medical_data(self, medical_data: Dict[str, Any]) -> str:
        """Encrypt medical/EHR data."""
        try:
            import json
            medical_json = json.dumps(medical_data, sort_keys=True)
            encrypted_data = self.field_keys['medical_data'].encrypt(
                medical_json.encode('utf-8')
            )
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt medical data: {e}")
            raise
    
    def decrypt_medical_data(self, encrypted_medical: str) -> Dict[str, Any]:
        """Decrypt medical/EHR data."""
        try:
            import json
            encrypted_data = base64.urlsafe_b64decode(encrypted_medical.encode('utf-8'))
            decrypted_data = self.field_keys['medical_data'].decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to decrypt medical data: {e}")
            raise
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token."""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """Hash password with salt using PBKDF2."""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        password_hash = kdf.derive(password.encode('utf-8'))
        
        return (
            base64.urlsafe_b64encode(password_hash).decode('utf-8'),
            base64.urlsafe_b64encode(salt).decode('utf-8')
        )
    
    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash."""
        try:
            salt_bytes = base64.urlsafe_b64decode(salt.encode('utf-8'))
            stored_hash_bytes = base64.urlsafe_b64decode(stored_hash.encode('utf-8'))
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=100000,
            )
            
            kdf.verify(password.encode('utf-8'), stored_hash_bytes)
            return True
        except Exception:
            return False


class RedisEncryption:
    """Encryption for Redis cache data."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize Redis encryption."""
        if encryption_key:
            self.fernet = Fernet(encryption_key.encode('utf-8'))
        else:
            # Generate key from environment
            redis_key = os.getenv('REDIS_ENCRYPTION_KEY')
            if redis_key:
                self.fernet = Fernet(redis_key.encode('utf-8'))
            else:
                # Generate new key for development
                self.fernet = Fernet(Fernet.generate_key())
                logger.warning("Using generated Redis encryption key for development")
    
    def encrypt_cache_data(self, data: Union[str, Dict[str, Any]]) -> str:
        """Encrypt data for Redis cache."""
        try:
            if isinstance(data, dict):
                import json
                data = json.dumps(data, sort_keys=True)
            
            encrypted_data = self.fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt cache data: {e}")
            raise
    
    def decrypt_cache_data(self, encrypted_data: str) -> str:
        """Decrypt data from Redis cache."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt cache data: {e}")
            raise


class JWTEncryption:
    """Enhanced JWT encryption for sensitive claims."""
    
    def __init__(self):
        """Initialize JWT encryption."""
        self.jwt_secret = os.getenv('JWT_SECRET_KEY')
        if not self.jwt_secret:
            raise ValueError("JWT secret key not configured")
        
        # Derive encryption key from JWT secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'jwt_encryption_salt',
            iterations=100000,
        )
        
        jwt_encryption_key = base64.urlsafe_b64encode(
            kdf.derive(self.jwt_secret.encode('utf-8'))
        )
        self.fernet = Fernet(jwt_encryption_key)
    
    def encrypt_sensitive_claims(self, claims: Dict[str, Any]) -> str:
        """Encrypt sensitive claims in JWT payload."""
        try:
            import json
            claims_json = json.dumps(claims, sort_keys=True)
            encrypted_claims = self.fernet.encrypt(claims_json.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_claims).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt JWT claims: {e}")
            raise
    
    def decrypt_sensitive_claims(self, encrypted_claims: str) -> Dict[str, Any]:
        """Decrypt sensitive claims from JWT payload."""
        try:
            import json
            encrypted_data = base64.urlsafe_b64decode(encrypted_claims.encode('utf-8'))
            decrypted_claims = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_claims.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to decrypt JWT claims: {e}")
            raise


# Global encryption instances
health_data_encryption = HealthDataEncryption()
redis_encryption = RedisEncryption()
jwt_encryption = JWTEncryption()


# Utility functions for database integration
def encrypt_for_database(field_type: str, data: Union[str, Dict[str, Any]]) -> str:
    """Encrypt data for database storage based on field type."""
    if field_type == 'conversation':
        return health_data_encryption.encrypt_conversation_content(str(data))
    elif field_type == 'profile':
        return health_data_encryption.encrypt_user_profile(data if isinstance(data, dict) else {'data': data})
    elif field_type == 'crisis':
        return health_data_encryption.encrypt_crisis_log(data if isinstance(data, dict) else {'data': data})
    elif field_type == 'medical':
        return health_data_encryption.encrypt_medical_data(data if isinstance(data, dict) else {'data': data})
    else:
        # Default encryption
        return health_data_encryption.fernet.encrypt(str(data).encode('utf-8')).decode('utf-8')


def decrypt_from_database(field_type: str, encrypted_data: str) -> Union[str, Dict[str, Any]]:
    """Decrypt data from database based on field type."""
    if field_type == 'conversation':
        return health_data_encryption.decrypt_conversation_content(encrypted_data)
    elif field_type == 'profile':
        return health_data_encryption.decrypt_user_profile(encrypted_data)
    elif field_type == 'crisis':
        return health_data_encryption.decrypt_crisis_log(encrypted_data)
    elif field_type == 'medical':
        return health_data_encryption.decrypt_medical_data(encrypted_data)
    else:
        # Default decryption
        return health_data_encryption.fernet.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
