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
            encryption_key: Base64-encoded encryption key (if None, reads from environment)
        """
        self._key = encryption_key or os.getenv("ENCRYPTION_KEY")
        if not self._key:
            # Generate a new key if none provided (for development only)
            self._key = self._generate_key()
            logger.warning(
                "No encryption key provided. Generated new key for development. "
                "Set ENCRYPTION_KEY environment variable for production."
            )
        
        try:
            # Handle different key formats
            if isinstance(self._key, str):
                # If it's a string, try to use it as base64
                try:
                    self._fernet = Fernet(self._key.encode())
                except:
                    # If that fails, generate a proper key
                    logger.warning("Invalid key format, generating new key")
                    self._key = self._generate_key()
                    self._fernet = Fernet(self._key.encode())
            else:
                self._fernet = Fernet(self._key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            # Generate a fallback key for development
            logger.warning("Generating fallback encryption key for development")
            self._key = self._generate_key()
            self._fernet = Fernet(self._key.encode())
    
    @staticmethod
    def _generate_key() -> str:
        """Generate a new encryption key."""
        key = Fernet.generate_key()
        return key.decode()
    
    @staticmethod
    def generate_key_from_password(password: str, salt: Optional[bytes] = None) -> str:
        """
        Generate encryption key from password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generates random if None)
            
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
        
        try:
            encrypted_data = self._fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Failed to encrypt data")
    
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
            decrypted_data = self._fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data")
    
    def encrypt_dict(self, data: dict) -> str:
        """
        Encrypt a dictionary as JSON.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted JSON string
        """
        import json
        json_data = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_data)
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """
        Decrypt data to dictionary.
        
        Args:
            encrypted_data: Base64-encoded encrypted JSON string
            
        Returns:
            Decrypted dictionary
        """
        import json
        json_data = self.decrypt(encrypted_data)
        return json.loads(json_data)
    
    def is_encrypted(self, data: str) -> bool:
        """
        Check if data appears to be encrypted.
        
        Args:
            data: Data to check
            
        Returns:
            True if data appears encrypted, False otherwise
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


def encrypt_user_data(data: Union[str, dict]) -> str:
    """
    Encrypt user data for storage.
    
    Args:
        data: Data to encrypt (string or dictionary)
        
    Returns:
        Encrypted data string
    """
    if isinstance(data, dict):
        return encryption_manager.encrypt_dict(data)
    else:
        return encryption_manager.encrypt(data)


def decrypt_user_data(encrypted_data: str, as_dict: bool = False) -> Union[str, dict]:
    """
    Decrypt user data from storage.
    
    Args:
        encrypted_data: Encrypted data string
        as_dict: Whether to return as dictionary
        
    Returns:
        Decrypted data
    """
    if as_dict:
        return encryption_manager.decrypt_dict(encrypted_data)
    else:
        return encryption_manager.decrypt(encrypted_data)


def hash_password(password: str) -> str:
    """
    Hash password for storage.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    import bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        password: Plain text password
        hashed_password: Stored password hash
        
    Returns:
        True if password matches, False otherwise
    """
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length: Token length in bytes
        
    Returns:
        Base64-encoded secure token
    """
    token = os.urandom(length)
    return base64.urlsafe_b64encode(token).decode()


def sanitize_for_logging(data: str, max_length: int = 50) -> str:
    """
    Sanitize sensitive data for logging.
    
    Args:
        data: Data to sanitize
        max_length: Maximum length to show
        
    Returns:
        Sanitized data string
    """
    if not data:
        return "[empty]"
    
    if len(data) <= max_length:
        return f"[{len(data)} chars]"
    else:
        return f"[{len(data)} chars: {data[:10]}...]"
