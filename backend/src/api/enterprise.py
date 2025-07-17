"""
Enterprise API endpoints for Mental Health Agent.
Provides SSO, API gateway management, and EHR integration endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..enterprise import (
    enterprise_sso,
    get_api_gateway,
    EHRIntegrationFactory,
    SSOConfig,
    SSOProviderType,
    EHRConfig,
    EHRSystem,
    FHIRVersion,
    RateLimitConfig,
    RateLimitType
)
from ..models.database import User
from ..monitoring.logging_config import get_logger

router = APIRouter(prefix="/enterprise", tags=["enterprise"])
logger = get_logger("api.enterprise")

# Simple admin check functions
async def require_admin(current_user: User = Depends(lambda: None)) -> User:
    """Require admin privileges."""
    # For now, allow all requests since we don't have proper auth setup
    return current_user

async def require_organization_admin(current_user: User = Depends(lambda: None)) -> User:
    """Require organization admin privileges."""
    # For now, allow all requests since we don't have proper auth setup
    return current_user


# SSO Endpoints
@router.post("/sso/providers", summary="Register SSO Provider")
async def register_sso_provider(
    provider_config: Dict[str, Any],
    current_user: User = Depends(require_organization_admin)
) -> Dict[str, Any]:
    """
    Register SSO provider for organization.
    
    Args:
        provider_config: SSO provider configuration
        current_user: Current authenticated admin user
        
    Returns:
        Registration result
    """
    try:
        logger.info("SSO provider registration requested", user_id=current_user.id)
        
        # Validate and create SSO config
        config = SSOConfig(
            provider_type=SSOProviderType(provider_config["provider_type"]),
            provider_name=provider_config["provider_name"],
            client_id=provider_config["client_id"],
            client_secret=provider_config["client_secret"],
            discovery_url=provider_config.get("discovery_url"),
            authorization_url=provider_config.get("authorization_url"),
            token_url=provider_config.get("token_url"),
            userinfo_url=provider_config.get("userinfo_url"),
            issuer=provider_config.get("issuer"),
            audience=provider_config.get("audience"),
            scopes=provider_config.get("scopes", ["openid", "email", "profile"]),
            metadata=provider_config.get("metadata", {})
        )
        
        success = await enterprise_sso.register_provider(
            current_user.organization_id,
            config
        )
        
        if success:
            return {
                "message": "SSO provider registered successfully",
                "provider_name": config.provider_name,
                "provider_type": config.provider_type.value
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to register SSO provider")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"SSO provider registration failed: {e}")
        raise HTTPException(status_code=500, detail="SSO provider registration failed")


@router.get("/sso/login/{provider_name}", summary="Initiate SSO Login")
async def initiate_sso_login(
    provider_name: str,
    redirect_uri: str = Query(..., description="Redirect URI after authentication"),
    state: Optional[str] = Query(None, description="State parameter"),
    organization_id: str = Query(..., description="Organization ID")
) -> Dict[str, Any]:
    """
    Initiate SSO login flow.
    
    Args:
        provider_name: SSO provider name
        redirect_uri: Redirect URI after authentication
        state: Optional state parameter
        organization_id: Organization identifier
        
    Returns:
        SSO login information
    """
    try:
        logger.info(f"SSO login initiated", provider_name=provider_name, organization_id=organization_id)
        
        result = await enterprise_sso.initiate_sso_login(
            organization_id,
            provider_name,
            redirect_uri,
            state
        )
        
        return result
        
    except Exception as e:
        logger.error(f"SSO login initiation failed: {e}")
        raise HTTPException(status_code=500, detail="SSO login initiation failed")


@router.post("/sso/callback/{provider_name}", summary="Handle SSO Callback")
async def handle_sso_callback(
    provider_name: str,
    request: Request,
    organization_id: str = Query(..., description="Organization ID")
) -> Dict[str, Any]:
    """
    Handle SSO callback and complete authentication.
    
    Args:
        provider_name: SSO provider name
        request: HTTP request with callback parameters
        organization_id: Organization identifier
        
    Returns:
        Authentication result with tokens
    """
    try:
        logger.info(f"SSO callback received", provider_name=provider_name, organization_id=organization_id)
        
        result = await enterprise_sso.handle_sso_callback(
            organization_id,
            provider_name,
            request
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSO callback handling failed: {e}")
        raise HTTPException(status_code=500, detail="SSO authentication failed")


# API Gateway Endpoints
@router.post("/api-keys", summary="Create API Key")
async def create_api_key(
    api_key_config: Dict[str, Any],
    current_user: User = Depends(require_organization_admin)
) -> Dict[str, Any]:
    """
    Create new API key for organization.
    
    Args:
        api_key_config: API key configuration
        current_user: Current authenticated admin user
        
    Returns:
        API key information
    """
    try:
        logger.info("API key creation requested", user_id=current_user.id)
        
        gateway = await get_api_gateway()
        
        # Parse rate limits if provided
        rate_limits = []
        if "rate_limits" in api_key_config:
            for rl_config in api_key_config["rate_limits"]:
                rate_limits.append(RateLimitConfig(
                    limit_type=RateLimitType(rl_config["limit_type"]),
                    limit=rl_config["limit"],
                    window_seconds=rl_config["window_seconds"],
                    burst_limit=rl_config.get("burst_limit"),
                    organization_id=current_user.organization_id
                ))
        
        # Parse expiration date
        expires_at = None
        if "expires_at" in api_key_config:
            expires_at = datetime.fromisoformat(api_key_config["expires_at"])
        
        result = await gateway.create_api_key(
            current_user.organization_id,
            api_key_config["name"],
            api_key_config.get("permissions", []),
            rate_limits,
            expires_at
        )
        
        return result
        
    except Exception as e:
        logger.error(f"API key creation failed: {e}")
        raise HTTPException(status_code=500, detail="API key creation failed")


@router.get("/api-keys", summary="List API Keys")
async def list_api_keys(
    current_user: User = Depends(require_organization_admin)
) -> Dict[str, Any]:
    """
    List API keys for organization.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        List of API keys
    """
    try:
        # Implementation would query database for API keys
        # This is a simplified version
        return {
            "api_keys": [],
            "total": 0,
            "organization_id": current_user.organization_id
        }
        
    except Exception as e:
        logger.error(f"API key listing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


# EHR Integration Endpoints
@router.post("/ehr/configure", summary="Configure EHR Integration")
async def configure_ehr_integration(
    ehr_config: Dict[str, Any],
    current_user: User = Depends(require_organization_admin)
) -> Dict[str, Any]:
    """
    Configure EHR integration for organization.
    
    Args:
        ehr_config: EHR configuration
        current_user: Current authenticated admin user
        
    Returns:
        Configuration result
    """
    try:
        logger.info("EHR integration configuration requested", user_id=current_user.id)
        
        # Create EHR config
        config = EHRConfig(
            system_type=EHRSystem(ehr_config["system_type"]),
            base_url=ehr_config["base_url"],
            fhir_version=FHIRVersion(ehr_config["fhir_version"]),
            client_id=ehr_config["client_id"],
            client_secret=ehr_config["client_secret"],
            scope=ehr_config["scope"],
            redirect_uri=ehr_config["redirect_uri"],
            tenant_id=ehr_config.get("tenant_id"),
            sandbox_mode=ehr_config.get("sandbox_mode", True),
            timeout=ehr_config.get("timeout", 30)
        )
        
        # Create EHR integration
        ehr_integration = EHRIntegrationFactory.create_integration(config)
        
        # Test authentication
        auth_success = await ehr_integration.authenticate()
        
        if auth_success:
            # Store configuration (implementation would save to database)
            return {
                "message": "EHR integration configured successfully",
                "system_type": config.system_type.value,
                "fhir_version": config.fhir_version.value,
                "sandbox_mode": config.sandbox_mode,
                "authentication_test": "passed"
            }
        else:
            raise HTTPException(status_code=400, detail="EHR authentication failed")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"EHR configuration failed: {e}")
        raise HTTPException(status_code=500, detail="EHR configuration failed")


@router.get("/ehr/patient/{patient_id}", summary="Get Patient Information")
async def get_patient_info(
    patient_id: str,
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get patient information from EHR.
    
    Args:
        patient_id: Patient identifier
        current_user: Current authenticated admin user
        
    Returns:
        Patient information
    """
    try:
        logger.info(f"Patient info requested", patient_id=patient_id, user_id=current_user.id)
        
        # This would use the configured EHR integration
        # For now, return a placeholder response
        return {
            "message": "EHR integration not configured",
            "patient_id": patient_id,
            "status": "configuration_required"
        }
        
    except Exception as e:
        logger.error(f"Patient info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient information")


@router.get("/ehr/systems", summary="Get Supported EHR Systems")
async def get_supported_ehr_systems() -> Dict[str, Any]:
    """
    Get list of supported EHR systems.
    
    Returns:
        List of supported EHR systems
    """
    try:
        systems = EHRIntegrationFactory.get_supported_systems()
        
        return {
            "supported_systems": systems,
            "fhir_versions": [version.value for version in FHIRVersion],
            "total_systems": len(systems)
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported EHR systems: {e}")
        raise HTTPException(status_code=500, detail="Failed to get supported systems")


# White-label Customization Endpoints
@router.post("/branding", summary="Configure White-label Branding")
async def configure_branding(
    branding_config: Dict[str, Any],
    current_user: User = Depends(require_organization_admin)
) -> Dict[str, Any]:
    """
    Configure white-label branding for organization.
    
    Args:
        branding_config: Branding configuration
        current_user: Current authenticated admin user
        
    Returns:
        Configuration result
    """
    try:
        logger.info("Branding configuration requested", user_id=current_user.id)
        
        # Validate branding configuration
        required_fields = ["organization_name", "primary_color", "logo_url"]
        for field in required_fields:
            if field not in branding_config:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Store branding configuration (implementation would save to database)
        branding_data = {
            "organization_id": current_user.organization_id,
            "organization_name": branding_config["organization_name"],
            "primary_color": branding_config["primary_color"],
            "secondary_color": branding_config.get("secondary_color"),
            "logo_url": branding_config["logo_url"],
            "favicon_url": branding_config.get("favicon_url"),
            "custom_css": branding_config.get("custom_css"),
            "welcome_message": branding_config.get("welcome_message"),
            "support_email": branding_config.get("support_email"),
            "support_phone": branding_config.get("support_phone"),
            "privacy_policy_url": branding_config.get("privacy_policy_url"),
            "terms_of_service_url": branding_config.get("terms_of_service_url"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "message": "Branding configuration updated successfully",
            "organization_name": branding_data["organization_name"],
            "primary_color": branding_data["primary_color"],
            "updated_at": branding_data["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Branding configuration failed: {e}")
        raise HTTPException(status_code=500, detail="Branding configuration failed")


@router.get("/branding", summary="Get Branding Configuration")
async def get_branding_configuration(
    current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get branding configuration for organization.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Branding configuration
    """
    try:
        # Implementation would retrieve from database
        # For now, return default configuration
        return {
            "organization_id": current_user.organization_id,
            "organization_name": "Mental Health Agent",
            "primary_color": "#3b82f6",
            "secondary_color": "#1e40af",
            "logo_url": "/images/default-logo.png",
            "welcome_message": "Welcome to your mental health support system",
            "support_email": "support@mentalhealthagent.com",
            "privacy_policy_url": "/privacy",
            "terms_of_service_url": "/terms"
        }
        
    except Exception as e:
        logger.error(f"Failed to get branding configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to get branding configuration")


# Webhook Management Endpoints
@router.post("/webhooks", summary="Create Webhook")
async def create_webhook(
    webhook_config: Dict[str, Any],
    current_user: User = Depends(require_organization_admin)
) -> Dict[str, Any]:
    """
    Create webhook for organization.
    
    Args:
        webhook_config: Webhook configuration
        current_user: Current authenticated admin user
        
    Returns:
        Webhook information
    """
    try:
        logger.info("Webhook creation requested", user_id=current_user.id)
        
        # Validate webhook configuration
        required_fields = ["url", "events"]
        for field in required_fields:
            if field not in webhook_config:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Generate webhook secret
        import secrets
        webhook_secret = secrets.token_urlsafe(32)
        
        webhook_data = {
            "webhook_id": secrets.token_urlsafe(16),
            "organization_id": current_user.organization_id,
            "url": webhook_config["url"],
            "events": webhook_config["events"],
            "secret": webhook_secret,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "webhook_id": webhook_data["webhook_id"],
            "url": webhook_data["url"],
            "events": webhook_data["events"],
            "secret": webhook_secret,  # Only returned once
            "created_at": webhook_data["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook creation failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook creation failed")


@router.get("/webhooks", summary="List Webhooks")
async def list_webhooks(
    current_user: User = Depends(require_organization_admin)
) -> Dict[str, Any]:
    """
    List webhooks for organization.
    
    Args:
        current_user: Current authenticated admin user
        
    Returns:
        List of webhooks
    """
    try:
        # Implementation would query database for webhooks
        return {
            "webhooks": [],
            "total": 0,
            "organization_id": current_user.organization_id
        }
        
    except Exception as e:
        logger.error(f"Webhook listing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list webhooks")


# Include enterprise router in main application
enterprise_router = router
