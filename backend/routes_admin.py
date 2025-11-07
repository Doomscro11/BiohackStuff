# Admin API Routes for Peptimancer Enterprise Runtime Control
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import logging
import os
from datetime import datetime

# Import settings service
from services.settings import (
    get_settings, set_settings, get_audit_history, get_settings_info,
    reset_settings_to_defaults, export_settings_backup, initialize_settings
)
from config_dynamic import ALLOWED_MODES

logger = logging.getLogger(__name__)

# Create admin router
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


# Phase 7.1: Helper function to require 2FA
def require_2fa(request: Request):
    """Require 2FA verification for admin endpoints"""
    if not getattr(request.state, "admin2fa", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA verification required for admin operations"
        )


# Admin request models
class SettingsUpdate(BaseModel):
    integrationsMode: Optional[str] = None
    demoMode: Optional[bool] = None
    watermarkExports: Optional[bool] = None
    croEnabled: Optional[bool] = None
    billingEnabled: Optional[bool] = None
    rateLimitDemo: Optional[int] = None
    rateLimitLive: Optional[int] = None
    maxAnalogues: Optional[int] = None
    enterpriseFeatures: Optional[bool] = None
    auditLogging: Optional[bool] = None
    confirm: str = Field(..., description="Must be 'SWITCH' to confirm changes")

    @validator("integrationsMode")
    def validate_mode(cls, v):
        if v and v not in ALLOWED_MODES:
            raise ValueError(f"Invalid mode. Must be one of: {ALLOWED_MODES}")
        return v

    @validator("confirm")
    def validate_confirmation(cls, v):
        if v != "SWITCH":
            raise ValueError("Confirmation must be 'SWITCH'")
        return v

    @validator("rateLimitDemo", "rateLimitLive")
    def validate_rate_limits(cls, v):
        if v is not None and (v < 1 or v > 10000):
            raise ValueError("Rate limit must be between 1 and 10000")
        return v

    @validator("maxAnalogues")
    def validate_max_analogues(cls, v):
        if v is not None and (v < 1 or v > 20):
            raise ValueError("Max analogues must be between 1 and 20")
        return v

# Simple admin authentication (using new auth middleware)
from middleware.auth import require_admin

def get_current_user(request: Request):
    """Get current authenticated user"""
    return require_admin(request)

def require_admin_role(user: Dict[str, Any]):
    """Ensure user has admin role - now handled by require_admin middleware"""
    # This function is now redundant as require_admin already checks role
    pass

# Admin endpoints
@admin_router.get("/settings")
async def get_admin_settings(request: Request):
    """Get current runtime settings (requires 2FA)"""
    user = get_current_user(request)
    require_2fa(request)  # Phase 7.1: Require 2FA
    
    try:
        settings_info = await get_settings_info()
        return settings_info
    except Exception as e:
        logger.error(f"Failed to get admin settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve settings"
        )

@admin_router.put("/settings")
async def update_admin_settings(
    request: Request,
    body: SettingsUpdate
):
    """Update runtime settings (requires 2FA)"""
    user = get_current_user(request)
    require_2fa(request)  # Phase 7.1: Require 2FA
    
    # Phase 7.1: Emergency freeze mode - block all settings changes
    if os.getenv("ADMIN_FREEZE", "false").lower() == "true":
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Admin operations are frozen due to emergency lockdown. Contact system administrator."
        )
    
    try:
        # Extract updates (exclude None values and confirmation)
        updates = {
            k: v for k, v in body.dict().items() 
            if v is not None and k != "confirm"
        }
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid updates provided"
            )
        
        # Add request metadata for audit trail
        actor_info = f"{user.get('email', 'admin')} ({user.get('id', 'unknown')})"
        
        # Update settings
        new_settings = await set_settings(updates, actor_info)
        
        logger.info(f"Settings updated by {actor_info}: {updates}")
        
        return {
            "success": True,
            "message": "Settings updated successfully",
            "settings": new_settings,
            "updated_fields": list(updates.keys())
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )

@admin_router.get("/settings/history")
async def get_settings_history(
    request: Request,
    limit: int = 50
):
    """Get settings change audit history"""
    user = get_current_user(request)
    
    try:
        if limit > 200:
            limit = 200  # Cap at 200 for performance
            
        history = await get_audit_history(limit)
        return {
            "history": history,
            "total_returned": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get settings history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history"
        )

@admin_router.post("/settings/reset")
async def reset_settings(request: Request):
    """Reset all settings to defaults"""
    user = get_current_user(request)
    
    try:
        actor_info = f"{user.get('email', 'admin')} ({user.get('id', 'unknown')})"
        default_settings = await reset_settings_to_defaults(actor_info)
        
        logger.warning(f"Settings reset to defaults by {actor_info}")
        
        return {
            "success": True,
            "message": "Settings reset to defaults",
            "settings": default_settings
        }
    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset settings"
        )

@admin_router.get("/settings/export")
async def export_settings(request: Request):
    """Export settings backup"""
    user = get_current_user(request)
    
    try:
        backup = await export_settings_backup()
        return backup
    except Exception as e:
        logger.error(f"Failed to export settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export settings"
        )

@admin_router.get("/health")
async def admin_health_check(request: Request):
    """Admin health check endpoint"""
    user = get_current_user(request)
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "admin_user": user.get("email", "Unknown"),
        "features": {
            "settings_management": True,
            "audit_trail": True,
            "runtime_switching": True
        }
    }

# Public endpoint for mode information (no auth required)
@admin_router.get("/mode", include_in_schema=True)
async def get_public_mode_info():
    """Get public mode information (no authentication required)"""
    try:
        settings = await get_settings()
        from ..config_dynamic import get_mode_display
        
        mode_info = get_mode_display(settings["integrationsMode"])
        
        return {
            "mode": settings["integrationsMode"],
            "demo_mode": settings["demoMode"],
            "watermark_enabled": settings["watermarkExports"],
            "mode_info": {
                "name": mode_info["name"],
                "description": mode_info["description"],
                "color": mode_info["color"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get mode info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get mode information"
        )

# Initialize settings on startup
@admin_router.on_event("startup")
async def startup_initialize_settings():
    """Initialize settings on application startup"""
    await initialize_settings()
    logger.info("Admin module initialized with runtime settings")