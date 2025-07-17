"""
Secure JWT Handler with proper signature verification and refresh tokens.
Addresses critical authentication vulnerabilities.
"""

import jwt
import time
import secrets
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..security.encryption import jwt_encryption
from ..monitoring.logging_config import get_logger

logger = get_logger("auth.secure_jwt")


@dataclass
class TokenPair:
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    refresh_expires_at: datetime


class SecureJWTHandler:
    """Secure JWT handler with proper verification and refresh tokens."""
    
    def __init__(self):
        """Initialize secure JWT handler."""
        import os
        self.secret_key = os.getenv('JWT_SECRET_KEY')
        if not self.secret_key or len(self.secret_key) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        
        self.algorithm = 'HS256'
        self.access_token_expire_minutes = 15  # Short-lived access tokens
        self.refresh_token_expire_days = 7     # Longer-lived refresh tokens
        
        # In-memory refresh token store (use Redis in production)
        self.refresh_tokens = {}
    
    def create_token_pair(
        self,
        user_id: str,
        email: str,
        organization_id: Optional[str] = None,
        permissions: Optional[list] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> TokenPair:
        """
        Create access and refresh token pair.
        
        Args:
            user_id: User identifier
            email: User email
            organization_id: Organization identifier
            permissions: User permissions
            additional_claims: Additional JWT claims
            
        Returns:
            Token pair with access and refresh tokens
        """
        try:
            now = datetime.utcnow()
            access_expires = now + timedelta(minutes=self.access_token_expire_minutes)
            refresh_expires = now + timedelta(days=self.refresh_token_expire_days)
            
            # Create access token with minimal claims
            access_payload = {
                'sub': user_id,
                'email': email,
                'iat': int(now.timestamp()),
                'exp': int(access_expires.timestamp()),
                'type': 'access',
                'jti': secrets.token_urlsafe(16)  # JWT ID for revocation
            }
            
            # Add optional claims
            if organization_id:
                access_payload['org_id'] = organization_id
            if permissions:
                access_payload['permissions'] = permissions
            if additional_claims:
                access_payload.update(additional_claims)
            
            # Encrypt sensitive claims
            if 'sensitive_data' in access_payload:
                access_payload['sensitive_data'] = jwt_encryption.encrypt_sensitive_claims(
                    access_payload['sensitive_data']
                )
            
            # Create refresh token
            refresh_token_id = secrets.token_urlsafe(32)
            refresh_payload = {
                'sub': user_id,
                'iat': int(now.timestamp()),
                'exp': int(refresh_expires.timestamp()),
                'type': 'refresh',
                'jti': refresh_token_id
            }
            
            # Sign tokens
            access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
            
            # Store refresh token for validation
            self.refresh_tokens[refresh_token_id] = {
                'user_id': user_id,
                'created_at': now,
                'expires_at': refresh_expires,
                'is_active': True
            }
            
            logger.info(f"Token pair created for user {user_id}")
            
            return TokenPair(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=access_expires,
                refresh_expires_at=refresh_expires
            )
            
        except Exception as e:
            logger.error(f"Failed to create token pair: {e}")
            raise
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify access token with proper signature validation.
        
        Args:
            token: JWT access token
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            # Decode with signature verification
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'require_exp': True,
                    'require_iat': True
                }
            )
            
            # Verify token type
            if payload.get('type') != 'access':
                logger.warning("Invalid token type for access token")
                return None
            
            # Decrypt sensitive claims if present
            if 'sensitive_data' in payload:
                try:
                    payload['sensitive_data'] = jwt_encryption.decrypt_sensitive_claims(
                        payload['sensitive_data']
                    )
                except Exception as e:
                    logger.error(f"Failed to decrypt sensitive claims: {e}")
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.info("Access token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify refresh token.
        
        Args:
            token: JWT refresh token
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            # Decode with signature verification
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'verify_iat': True,
                    'require_exp': True,
                    'require_iat': True
                }
            )
            
            # Verify token type
            if payload.get('type') != 'refresh':
                logger.warning("Invalid token type for refresh token")
                return None
            
            # Check if refresh token is still active
            token_id = payload.get('jti')
            if not token_id or token_id not in self.refresh_tokens:
                logger.warning("Refresh token not found or revoked")
                return None
            
            token_info = self.refresh_tokens[token_id]
            if not token_info['is_active']:
                logger.warning("Refresh token is inactive")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.info("Refresh token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return None
        except Exception as e:
            logger.error(f"Refresh token verification failed: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[TokenPair]:
        """
        Create new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New token pair if successful, None otherwise
        """
        try:
            # Verify refresh token
            refresh_payload = self.verify_refresh_token(refresh_token)
            if not refresh_payload:
                return None
            
            user_id = refresh_payload['sub']
            
            # Get user information for new access token
            # In production, this would query the database
            # For now, create minimal token
            return self.create_token_pair(
                user_id=user_id,
                email=f"user_{user_id}@example.com"  # This should come from database
            )
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None
    
    def revoke_refresh_token(self, token: str) -> bool:
        """
        Revoke refresh token.
        
        Args:
            token: Refresh token to revoke
            
        Returns:
            True if successfully revoked, False otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={'verify_signature': True}
            )
            
            token_id = payload.get('jti')
            if token_id and token_id in self.refresh_tokens:
                self.refresh_tokens[token_id]['is_active'] = False
                logger.info(f"Refresh token revoked: {token_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {e}")
            return False
    
    def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of tokens revoked
        """
        try:
            revoked_count = 0
            
            for token_id, token_info in self.refresh_tokens.items():
                if token_info['user_id'] == user_id and token_info['is_active']:
                    token_info['is_active'] = False
                    revoked_count += 1
            
            logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            return revoked_count
            
        except Exception as e:
            logger.error(f"Failed to revoke user tokens: {e}")
            return 0
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired refresh tokens.
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            now = datetime.utcnow()
            expired_tokens = []
            
            for token_id, token_info in self.refresh_tokens.items():
                if token_info['expires_at'] < now:
                    expired_tokens.append(token_id)
            
            for token_id in expired_tokens:
                del self.refresh_tokens[token_id]
            
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
            return len(expired_tokens)
            
        except Exception as e:
            logger.error(f"Token cleanup failed: {e}")
            return 0
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a token without full verification.
        
        Args:
            token: JWT token
            
        Returns:
            Token information if decodable, None otherwise
        """
        try:
            # Decode without verification for inspection
            payload = jwt.decode(
                token,
                options={'verify_signature': False, 'verify_exp': False}
            )
            
            return {
                'user_id': payload.get('sub'),
                'email': payload.get('email'),
                'token_type': payload.get('type'),
                'issued_at': datetime.fromtimestamp(payload.get('iat', 0)),
                'expires_at': datetime.fromtimestamp(payload.get('exp', 0)),
                'jwt_id': payload.get('jti')
            }
            
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return None


# Global secure JWT handler
secure_jwt_handler = SecureJWTHandler()
