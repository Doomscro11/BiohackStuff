"""
Admin Feature Flags API
Endpoints for managing feature flags and user feature levels
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from middleware.auth import require_role
from services import feature_flags_service
from schemas.feature_flags import FeatureFlagUpdate, UserFeatureLevel, FeatureFlagResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/features", tags=["admin_features"])


@router.get("/flags")
async def get_feature_flags(user=Depends(require_role("admin"))):
    """
    Get all feature flags
    Admin only
    """
    try:
        flags = await feature_flags_service.get_feature_flags()
        return {"flags": flags}
    except Exception as e:
        logger.error(f"Failed to get feature flags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feature flags"
        )


@router.post("/flags")
async def update_feature_flag(
    body: FeatureFlagUpdate,
    user=Depends(require_role("admin"))
):
    """
    Update a feature flag
    Admin only
    """
    try:
        result = await feature_flags_service.update_feature_flag(
            flag_key=body.flag_key,
            enabled=body.enabled,
            config=body.config,
            updated_by=user.get('email')
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to update feature flag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feature flag: {str(e)}"
        )


@router.post("/user-level")
async def set_user_feature_level(
    body: UserFeatureLevel,
    user=Depends(require_role("admin"))
):
    """
    Set user's feature access level
    Admin only
    """
    try:
        result = await feature_flags_service.set_user_feature_level(
            user_id=body.user_id,
            level=body.feature_level,
            updated_by=user.get('email')
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to set user feature level: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set user feature level: {str(e)}"
        )


@router.get("/user-level/{user_id}")
async def get_user_feature_level(
    user_id: str,
    user=Depends(require_role("admin"))
):
    """
    Get user's feature access level
    Admin only
    """
    try:
        level = await feature_flags_service.get_user_feature_level(user_id)
        return {"user_id": user_id, "feature_level": level}
    except Exception as e:
        logger.error(f"Failed to get user feature level: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user feature level"
        )


@router.get("/audit-log")
async def get_feature_audit_log(
    limit: int = 100,
    user=Depends(require_role("admin"))
):
    """
    Get feature flag audit log
    Admin only
    """
    try:
        logs = await feature_flags_service.get_feature_audit_log(limit=limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Failed to get audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit log"
        )


@router.get("/presets")
async def get_feature_presets(user=Depends(require_role("admin"))):
    """
    Get available feature flag presets
    Admin only
    """
    presets = {
        "baseline": {
            "name": "Baseline",
            "description": "All advanced features disabled",
            "flags": {
                "advanced_mode_enabled": False,
                "experimental_ui_enabled": False,
                "preview_mode_enabled": False,
                "extended_analytics_enabled": False
            }
        },
        "preview": {
            "name": "Preview Mode",
            "description": "Basic UI scaffolding enabled",
            "flags": {
                "advanced_mode_enabled": True,
                "experimental_ui_enabled": False,
                "preview_mode_enabled": True,
                "extended_analytics_enabled": False
            }
        },
        "extended": {
            "name": "Extended UI",
            "description": "Additional panels accessible",
            "flags": {
                "advanced_mode_enabled": True,
                "experimental_ui_enabled": True,
                "preview_mode_enabled": True,
                "extended_analytics_enabled": True
            }
        },
        "full_scaffold": {
            "name": "Full Scaffold",
            "description": "Complete UI framework visible",
            "flags": {
                "advanced_mode_enabled": True,
                "experimental_ui_enabled": True,
                "preview_mode_enabled": True,
                "extended_analytics_enabled": True
            }
        }
    }
    
    return {"presets": presets}


@router.post("/apply-preset")
async def apply_feature_preset(
    preset_name: str,
    user=Depends(require_role("admin"))
):
    """
    Apply a feature flag preset
    Admin only
    """
    try:
        # Get preset
        response = await get_feature_presets(user)
        presets = response["presets"]
        
        if preset_name not in presets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preset '{preset_name}' not found"
            )
        
        preset = presets[preset_name]
        
        # Apply all flags in preset
        for flag_key, enabled in preset["flags"].items():
            await feature_flags_service.update_feature_flag(
                flag_key=flag_key,
                enabled=enabled,
                updated_by=user.get('email')
            )
        
        logger.info(f"Applied preset '{preset_name}' by {user.get('email')}")
        
        return {
            "success": True,
            "preset": preset_name,
            "applied_flags": preset["flags"],
            "applied_by": user.get('email')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply preset: {str(e)}"
        )
