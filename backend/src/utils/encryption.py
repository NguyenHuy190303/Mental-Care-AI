"""
HIPAA-compliant encryption utilities for patient data.

This module provides encryption and decryption functions for sensitive
healthcare data, ensuring compliance with HIPAA security requirements.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

# Get encryption key from environment or generate one
ENCRYPTION_KEY = os.getenv('SAGE_ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # Generate a key for development (in production, this should be set in environment)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.warning("Using generated encryption key. Set SAGE_ENCRYPTION_KEY environment variable for production.")

# Initialize Fernet cipher
try:
    cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
except Exception as e:
    logger.error(f"Failed to initialize encryption: {e}")
    # Fallback to a generated key
    cipher_suite = Fernet(Fernet.generate_key())


def encrypt_data(data: str) -> str:
    """
    Encrypt sensitive data using Fernet symmetric encryption.
    
    Args:
        data: Plain text data to encrypt
        
    Returns:
        Base64 encoded encrypted data
        
    Raises:
        Exception: If encryption fails
    """
    try:
        if not data:
            return ""
        
        # Convert string to bytes
        data_bytes = data.encode('utf-8')
        
        # Encrypt the data
        encrypted_data = cipher_suite.encrypt(data_bytes)
        
        # Return base64 encoded string
        return base64.b64encode(encrypted_data).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise Exception("Failed to encrypt data")


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt data that was encrypted with encrypt_data.
    
    Args:
        encrypted_data: Base64 encoded encrypted data
        
    Returns:
        Decrypted plain text data
        
    Raises:
        Exception: If decryption fails
    """
    try:
        if not encrypted_data:
            return ""
        
        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        
        # Decrypt the data
        decrypted_bytes = cipher_suite.decrypt(encrypted_bytes)
        
        # Convert bytes back to string
        return decrypted_bytes.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise Exception("Failed to decrypt data")


def generate_key() -> str:
    """
    Generate a new encryption key.
    
    Returns:
        Base64 encoded encryption key
    """
    return Fernet.generate_key().decode()


def derive_key_from_password(password: str, salt: bytes = None) -> str:
    """
    Derive an encryption key from a password using PBKDF2.
    
    Args:
        password: Password to derive key from
        salt: Salt for key derivation (generated if not provided)
        
    Returns:
        Base64 encoded derived key
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


def hash_data(data: str) -> str:
    """
    Create a one-way hash of data for verification purposes.
    
    Args:
        data: Data to hash
        
    Returns:
        Hexadecimal hash string
    """
    import hashlib
    
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def secure_compare(a: str, b: str) -> bool:
    """
    Securely compare two strings to prevent timing attacks.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings are equal, False otherwise
    """
    import hmac
    
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


# HIPAA Compliance Functions

def audit_log_access(user_id: str, data_type: str, action: str, patient_id: str = None):
    """
    Log data access for HIPAA audit trail.
    
    Args:
        user_id: ID of user accessing data
        data_type: Type of data being accessed
        action: Action being performed (read, write, delete)
        patient_id: ID of patient whose data is being accessed
    """
    audit_entry = {
        'timestamp': logger.handlers[0].formatter.formatTime(logger.makeRecord(
            logger.name, logging.INFO, __file__, 0, "", (), None
        )) if logger.handlers else None,
        'user_id': user_id,
        'data_type': data_type,
        'action': action,
        'patient_id': patient_id
    }
    
    # In production, this should write to a secure audit log
    logger.info(f"AUDIT: {audit_entry}")


def validate_data_access(user_id: str, patient_id: str, user_role: str = None) -> bool:
    """
    Validate that a user has permission to access patient data.
    
    Args:
        user_id: ID of user requesting access
        patient_id: ID of patient whose data is being accessed
        user_role: Role of the user (patient, provider, admin)
        
    Returns:
        True if access is allowed, False otherwise
    """
    # Basic validation - in production, this should check against
    # a proper authorization system
    
    if user_role == 'admin':
        return True
    
    if user_role == 'provider':
        # Providers should have access to their assigned patients
        # This would need to be checked against a patient-provider relationship table
        return True
    
    if user_role == 'patient':
        # Patients can only access their own data
        return user_id == patient_id
    
    return False


def anonymize_data(data: dict, fields_to_anonymize: list = None) -> dict:
    """
    Anonymize sensitive fields in data for research or analytics.
    
    Args:
        data: Dictionary containing data to anonymize
        fields_to_anonymize: List of field names to anonymize
        
    Returns:
        Dictionary with anonymized data
    """
    if fields_to_anonymize is None:
        fields_to_anonymize = [
            'name', 'email', 'phone', 'address', 'ssn', 
            'date_of_birth', 'medical_record_number'
        ]
    
    anonymized = data.copy()
    
    for field in fields_to_anonymize:
        if field in anonymized:
            # Replace with anonymized version
            anonymized[field] = hash_data(str(anonymized[field]))[:8] + "***"
    
    return anonymized
