"""
Encryption utilities for GDPR/HIPAA compliance.
"""

import os
import base64
import logging
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            encryption_key: Base64-encoded encryption key (if None, will be read from environment)
        """
        self._key = encryption_key or os.getenv("ENCRYPTION_KEY")
        if not self._key:
            self._key = self._generate_key()
            logger.warning("No encryption key provided, generated new key. Store this securely!")
            logger.warning(f"Generated key: {self._key}")
        
        self._fernet = Fernet(self._key.encode() if isinstance(self._key, str) else self._key)
    
    @staticmethod
    def _generate_key() -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()
    
    @staticmethod
    def generate_key_from_password(password: str, salt: Optional[bytes] = None) -> str:
        """
        Generate encryption key from password.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (if None, will be generated)
            
        Returns:
            Base64-encoded encryption key
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt (string or bytes)
            
        Returns:
            Base64-encoded encrypted data
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted_data = self._fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted string
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")
    
    def encrypt_dict(self, data: dict) -> str:
        """
        Encrypt dictionary data as JSON.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted JSON string
        """
        import json
        json_str = json.dumps(data, default=str)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """
        Decrypt JSON data to dictionary.
        
        Args:
            encrypted_data: Base64-encoded encrypted JSON string
            
        Returns:
            Decrypted dictionary
        """
        import json
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)
    
    def is_encrypted(self, data: str) -> bool:
        """
        Check if data appears to be encrypted.
        
        Args:
            data: Data to check
            
        Returns:
            True if data appears to be encrypted
        """
        try:
            # Try to decode as base64
            base64.urlsafe_b64decode(data.encode())
            # If it's valid base64 and longer than typical plaintext, likely encrypted
            return len(data) > 50 and '=' in data[-4:]
        except Exception:
            return False


# Global encryption manager instance
encryption_manager = EncryptionManager()


def encrypt_sensitive_data(data: Union[str, dict]) -> str:
    """
    Encrypt sensitive data using global encryption manager.
    
    Args:
        data: Data to encrypt
        
    Returns:
        Encrypted data string
    """
    if isinstance(data, dict):
        return encryption_manager.encrypt_dict(data)
    return encryption_manager.encrypt(data)


def decrypt_sensitive_data(encrypted_data: str, as_dict: bool = False) -> Union[str, dict]:
    """
    Decrypt sensitive data using global encryption manager.
    
    Args:
        encrypted_data: Encrypted data string
        as_dict: Whether to return as dictionary
        
    Returns:
        Decrypted data
    """
    if as_dict:
        return encryption_manager.decrypt_dict(encrypted_data)
    return encryption_manager.decrypt(encrypted_data)


def ensure_encryption_key_exists():
    """Ensure encryption key exists in environment or generate one."""
    if not os.getenv("ENCRYPTION_KEY"):
        key = EncryptionManager._generate_key()
        logger.warning("No ENCRYPTION_KEY found in environment!")
        logger.warning(f"Generated key: {key}")
        logger.warning("Please set this as ENCRYPTION_KEY environment variable")
        return key
    return os.getenv("ENCRYPTION_KEY")