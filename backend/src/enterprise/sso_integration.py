"""
Enterprise Single Sign-On (SSO) Integration for Mental Health Agent
Supports SAML 2.0, OAuth 2.0, OpenID Connect, and LDAP authentication.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import jwt
import httpx
from urllib.parse import urlencode, parse_qs

from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..models.database import User, Organization, SSOProvider
from ..auth.secure_jwt_handler import SecureJWTHandler
from ..monitoring.logging_config import get_logger

logger = get_logger("enterprise.sso")


class SSOProviderType(str, Enum):
    """Supported SSO provider types."""
    SAML2 = "saml2"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "openid_connect"
    LDAP = "ldap"
    AZURE_AD = "azure_ad"
    GOOGLE_WORKSPACE = "google_workspace"
    OKTA = "okta"
    AUTH0 = "auth0"


@dataclass
class SSOConfig:
    """SSO provider configuration."""
    
    provider_type: SSOProviderType
    provider_name: str
    client_id: str
    client_secret: str
    discovery_url: Optional[str] = None
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    userinfo_url: Optional[str] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None
    scopes: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class SSOUserInfo:
    """User information from SSO provider."""
    
    external_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    groups: List[str] = None
    roles: List[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    metadata: Dict[str, Any] = None


class EnterpriseSSO:
    """Enterprise SSO integration manager."""
    
    def __init__(self):
        """Initialize SSO manager."""
        self.providers = {}
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    async def register_provider(
        self,
        organization_id: str,
        config: SSOConfig
    ) -> bool:
        """
        Register SSO provider for organization.
        
        Args:
            organization_id: Organization identifier
            config: SSO provider configuration
            
        Returns:
            Success status
        """
        try:
            # Validate configuration
            await self._validate_sso_config(config)
            
            # Store provider configuration
            async with get_db_session() as session:
                provider = SSOProvider(
                    organization_id=organization_id,
                    provider_type=config.provider_type.value,
                    provider_name=config.provider_name,
                    configuration=config.__dict__,
                    is_active=True
                )
                
                session.add(provider)
                await session.commit()
                
                # Cache provider configuration
                self.providers[f"{organization_id}:{config.provider_name}"] = config
                
                logger.info(
                    f"SSO provider registered",
                    organization_id=organization_id,
                    provider_type=config.provider_type.value,
                    provider_name=config.provider_name
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to register SSO provider: {e}")
            return False
    
    async def initiate_sso_login(
        self,
        organization_id: str,
        provider_name: str,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate SSO login flow.
        
        Args:
            organization_id: Organization identifier
            provider_name: SSO provider name
            redirect_uri: Redirect URI after authentication
            state: Optional state parameter
            
        Returns:
            SSO login information
        """
        try:
            config = await self._get_provider_config(organization_id, provider_name)
            
            if config.provider_type == SSOProviderType.OAUTH2:
                return await self._initiate_oauth2_login(config, redirect_uri, state)
            elif config.provider_type == SSOProviderType.OPENID_CONNECT:
                return await self._initiate_oidc_login(config, redirect_uri, state)
            elif config.provider_type == SSOProviderType.SAML2:
                return await self._initiate_saml2_login(config, redirect_uri, state)
            elif config.provider_type == SSOProviderType.AZURE_AD:
                return await self._initiate_azure_ad_login(config, redirect_uri, state)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported SSO provider type: {config.provider_type}"
                )
                
        except Exception as e:
            logger.error(f"Failed to initiate SSO login: {e}")
            raise HTTPException(status_code=500, detail="SSO login initiation failed")
    
    async def handle_sso_callback(
        self,
        organization_id: str,
        provider_name: str,
        request: Request
    ) -> Dict[str, Any]:
        """
        Handle SSO callback and complete authentication.
        
        Args:
            organization_id: Organization identifier
            provider_name: SSO provider name
            request: HTTP request with callback parameters
            
        Returns:
            Authentication result with tokens
        """
        try:
            config = await self._get_provider_config(organization_id, provider_name)
            
            # Extract callback parameters
            if config.provider_type in [SSOProviderType.OAUTH2, SSOProviderType.OPENID_CONNECT, SSOProviderType.AZURE_AD]:
                code = request.query_params.get('code')
                state = request.query_params.get('state')
                error = request.query_params.get('error')
                
                if error:
                    raise HTTPException(status_code=400, detail=f"SSO error: {error}")
                
                if not code:
                    raise HTTPException(status_code=400, detail="Authorization code not provided")
                
                # Exchange code for tokens
                tokens = await self._exchange_code_for_tokens(config, code)
                
                # Get user information
                user_info = await self._get_user_info_from_tokens(config, tokens)
                
            elif config.provider_type == SSOProviderType.SAML2:
                # Handle SAML response
                saml_response = request.form.get('SAMLResponse')
                if not saml_response:
                    raise HTTPException(status_code=400, detail="SAML response not provided")
                
                user_info = await self._process_saml_response(config, saml_response)
                
            else:
                raise HTTPException(status_code=400, detail="Unsupported SSO provider type")
            
            # Create or update user
            user = await self._create_or_update_sso_user(organization_id, provider_name, user_info)
            
            # Generate JWT tokens
            access_token = create_access_token({"sub": user.id, "email": user.email})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "organization_id": user.organization_id
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"SSO callback handling failed: {e}")
            raise HTTPException(status_code=500, detail="SSO authentication failed")
    
    async def _validate_sso_config(self, config: SSOConfig) -> bool:
        """Validate SSO configuration."""
        if not config.client_id:
            raise ValueError("Client ID is required")
        
        if config.provider_type in [SSOProviderType.OAUTH2, SSOProviderType.OPENID_CONNECT]:
            if not config.client_secret:
                raise ValueError("Client secret is required for OAuth2/OIDC")
            if not config.authorization_url:
                raise ValueError("Authorization URL is required")
            if not config.token_url:
                raise ValueError("Token URL is required")
        
        return True
    
    async def _get_provider_config(self, organization_id: str, provider_name: str) -> SSOConfig:
        """Get SSO provider configuration."""
        cache_key = f"{organization_id}:{provider_name}"
        
        if cache_key in self.providers:
            return self.providers[cache_key]
        
        async with get_db_session() as session:
            provider = await session.get(SSOProvider, {
                "organization_id": organization_id,
                "provider_name": provider_name
            })
            
            if not provider or not provider.is_active:
                raise HTTPException(status_code=404, detail="SSO provider not found")
            
            config = SSOConfig(**provider.configuration)
            self.providers[cache_key] = config
            
            return config
    
    async def _initiate_oauth2_login(
        self,
        config: SSOConfig,
        redirect_uri: str,
        state: Optional[str]
    ) -> Dict[str, Any]:
        """Initiate OAuth2 login flow."""
        params = {
            "response_type": "code",
            "client_id": config.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(config.scopes or ["openid", "email", "profile"]),
        }
        
        if state:
            params["state"] = state
        
        auth_url = f"{config.authorization_url}?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "provider_type": config.provider_type.value,
            "provider_name": config.provider_name
        }
    
    async def _initiate_oidc_login(
        self,
        config: SSOConfig,
        redirect_uri: str,
        state: Optional[str]
    ) -> Dict[str, Any]:
        """Initiate OpenID Connect login flow."""
        # OIDC is essentially OAuth2 with standardized scopes
        return await self._initiate_oauth2_login(config, redirect_uri, state)
    
    async def _initiate_azure_ad_login(
        self,
        config: SSOConfig,
        redirect_uri: str,
        state: Optional[str]
    ) -> Dict[str, Any]:
        """Initiate Azure AD login flow."""
        tenant_id = config.metadata.get("tenant_id", "common")
        
        params = {
            "response_type": "code",
            "client_id": config.client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "response_mode": "query"
        }
        
        if state:
            params["state"] = state
        
        auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "provider_type": config.provider_type.value,
            "provider_name": config.provider_name
        }
    
    async def _initiate_saml2_login(
        self,
        config: SSOConfig,
        redirect_uri: str,
        state: Optional[str]
    ) -> Dict[str, Any]:
        """Initiate SAML 2.0 login flow."""
        # SAML implementation would require additional libraries like python3-saml
        # This is a simplified version
        
        saml_request = self._create_saml_request(config, redirect_uri)
        
        return {
            "auth_url": config.authorization_url,
            "saml_request": saml_request,
            "provider_type": config.provider_type.value,
            "provider_name": config.provider_name
        }
    
    async def _exchange_code_for_tokens(
        self,
        config: SSOConfig,
        code: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access tokens."""
        token_data = {
            "grant_type": "authorization_code",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = await self.http_client.post(
            config.token_url,
            data=token_data,
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Token exchange failed")
        
        return response.json()
    
    async def _get_user_info_from_tokens(
        self,
        config: SSOConfig,
        tokens: Dict[str, Any]
    ) -> SSOUserInfo:
        """Get user information from access tokens."""
        access_token = tokens.get("access_token")
        id_token = tokens.get("id_token")
        
        if id_token and config.provider_type == SSOProviderType.OPENID_CONNECT:
            # Decode ID token for user info
            user_claims = jwt.decode(
                id_token,
                options={"verify_signature": False}  # In production, verify signature
            )
            
            return SSOUserInfo(
                external_id=user_claims.get("sub"),
                email=user_claims.get("email"),
                first_name=user_claims.get("given_name"),
                last_name=user_claims.get("family_name"),
                display_name=user_claims.get("name"),
                groups=user_claims.get("groups", []),
                metadata=user_claims
            )
        
        elif access_token and config.userinfo_url:
            # Use access token to get user info
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = await self.http_client.get(
                config.userinfo_url,
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            
            user_data = response.json()
            
            return SSOUserInfo(
                external_id=user_data.get("sub") or user_data.get("id"),
                email=user_data.get("email"),
                first_name=user_data.get("given_name") or user_data.get("first_name"),
                last_name=user_data.get("family_name") or user_data.get("last_name"),
                display_name=user_data.get("name") or user_data.get("display_name"),
                groups=user_data.get("groups", []),
                metadata=user_data
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unable to get user information")
    
    async def _create_or_update_sso_user(
        self,
        organization_id: str,
        provider_name: str,
        user_info: SSOUserInfo
    ) -> User:
        """Create or update user from SSO information."""
        async with get_db_session() as session:
            # Check if user exists
            user = await session.query(User).filter(
                User.email == user_info.email,
                User.organization_id == organization_id
            ).first()
            
            if user:
                # Update existing user
                user.first_name = user_info.first_name or user.first_name
                user.last_name = user_info.last_name or user.last_name
                user.sso_provider = provider_name
                user.sso_external_id = user_info.external_id
                user.last_login = datetime.utcnow()
                user.metadata = {
                    **(user.metadata or {}),
                    "sso_groups": user_info.groups,
                    "sso_metadata": user_info.metadata
                }
            else:
                # Create new user
                user = User(
                    email=user_info.email,
                    first_name=user_info.first_name,
                    last_name=user_info.last_name,
                    organization_id=organization_id,
                    sso_provider=provider_name,
                    sso_external_id=user_info.external_id,
                    is_active=True,
                    email_verified=True,  # SSO users are pre-verified
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow(),
                    metadata={
                        "sso_groups": user_info.groups,
                        "sso_metadata": user_info.metadata
                    }
                )
                session.add(user)
            
            await session.commit()
            await session.refresh(user)
            
            return user
    
    def _create_saml_request(self, config: SSOConfig, redirect_uri: str) -> str:
        """Create SAML authentication request."""
        # Simplified SAML request creation
        # In production, use proper SAML library
        import base64
        import uuid
        
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        saml_request = f"""
        <samlp:AuthnRequest
            xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
            ID="{request_id}"
            Version="2.0"
            IssueInstant="{timestamp}"
            Destination="{config.authorization_url}"
            AssertionConsumerServiceURL="{redirect_uri}">
            <saml:Issuer>{config.issuer}</saml:Issuer>
        </samlp:AuthnRequest>
        """
        
        return base64.b64encode(saml_request.encode()).decode()
    
    async def _process_saml_response(
        self,
        config: SSOConfig,
        saml_response: str
    ) -> SSOUserInfo:
        """Process SAML response and extract user information."""
        # Simplified SAML response processing
        # In production, use proper SAML library with signature verification
        import base64
        import xml.etree.ElementTree as ET
        
        try:
            decoded_response = base64.b64decode(saml_response).decode()
            root = ET.fromstring(decoded_response)
            
            # Extract user attributes (simplified)
            email = None
            first_name = None
            last_name = None
            external_id = None
            
            # This would need proper SAML parsing in production
            for attr in root.iter():
                if 'email' in attr.tag.lower():
                    email = attr.text
                elif 'firstname' in attr.tag.lower():
                    first_name = attr.text
                elif 'lastname' in attr.tag.lower():
                    last_name = attr.text
                elif 'nameid' in attr.tag.lower():
                    external_id = attr.text
            
            return SSOUserInfo(
                external_id=external_id or email,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            
        except Exception as e:
            logger.error(f"SAML response processing failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid SAML response")


# Global SSO manager instance
enterprise_sso = EnterpriseSSO()
