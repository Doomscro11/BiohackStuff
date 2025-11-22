"""
Placeholder API Endpoints
Mock endpoints that return example data for UI scaffolding
No actual functionality - purely architectural placeholders
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from middleware.auth import get_current_user
from services import feature_flags_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/placeholder", tags=["placeholder"])


@router.get("/advanced-preview")
async def advanced_preview(user=Depends(get_current_user)):
    """
    Placeholder endpoint for advanced mode preview
    Returns mock data only - no actual computation
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check user's feature level
    feature_level = await feature_flags_service.get_user_feature_level(user['id'])
    
    # Log access
    await feature_flags_service.log_feature_access(
        user_id=user['id'],
        feature_key='advanced_preview',
        level=feature_level
    )
    
    # Return richer mock placeholder data
    return {
        "status": "preview_mode",
        "feature_level": feature_level,
        "available_features": [
            "feature_alpha" if feature_level >= 1 else None,
            "feature_beta" if feature_level >= 2 else None,
            "feature_gamma" if feature_level >= 3 else None,
            "feature_delta" if feature_level >= 4 else None
        ],
        "mock_data": {
            "example_field_1": "placeholder_value_1",
            "example_field_2": 42,
            "example_field_3": [1, 2, 3, 4, 5],
            "mock_parameters": {
                "param_a": 0.75,
                "param_b": "preset_1",
                "param_c": ["option_1", "option_2", "option_3"]
            },
            "mock_results": [
                {"id": "r1", "type": "placeholder", "value": 42.5, "status": "mock"},
                {"id": "r2", "type": "placeholder", "value": 38.2, "status": "mock"},
                {"id": "r3", "type": "placeholder", "value": 51.8, "status": "mock"}
            ],
            "mock_visualization": {
                "chart_type": "bar",
                "data_points": [60, 80, 40, 90, 50],
                "labels": ["A", "B", "C", "D", "E"]
            }
        },
        "message": "This is placeholder data only. No actual computation performed."
    }


@router.post("/advanced-action")
async def advanced_action(user=Depends(get_current_user)):
    """
    Placeholder endpoint for advanced actions
    Returns mock response only - no actual processing
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    feature_level = await feature_flags_service.get_user_feature_level(user['id'])
    
    # Log access
    await feature_flags_service.log_feature_access(
        user_id=user['id'],
        feature_key='advanced_action',
        level=feature_level
    )
    
    # Return mock response
    return {
        "status": "completed",
        "action_type": "placeholder",
        "result": {
            "mock_result_1": "example_output",
            "mock_result_2": {"nested": "data"},
            "mock_result_3": [{"id": 1, "value": "A"}, {"id": 2, "value": "B"}]
        },
        "metadata": {
            "feature_level_used": feature_level,
            "computation_type": "none_performed",
            "disclaimer": "This is non-functional placeholder data"
        }
    }


@router.get("/feature-status")
async def feature_status(user=Depends(get_current_user)):
    """
    Get user's feature access status
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    feature_level = await feature_flags_service.get_user_feature_level(user['id'])
    flags = await feature_flags_service.get_feature_flags()
    
    return {
        "user_id": user['id'],
        "feature_level": feature_level,
        "global_flags": flags,
        "capabilities": {
            "level_0": "baseline",
            "level_1": "enabled" if feature_level >= 1 else "locked",
            "level_2": "enabled" if feature_level >= 2 else "locked",
            "level_3": "enabled" if feature_level >= 3 else "locked",
            "level_4": "enabled" if feature_level >= 4 else "locked"
        }
    }
