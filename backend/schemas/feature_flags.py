"""
Feature Flags Schemas
Request/response models for feature flag management
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class FeatureFlagUpdate(BaseModel):
    """Request to update a feature flag"""
    flag_key: str = Field(..., description="Feature flag identifier")
    enabled: bool = Field(..., description="Enable or disable the feature")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Optional configuration")


class UserFeatureLevel(BaseModel):
    """Request to update user's feature access level"""
    user_id: str
    feature_level: int = Field(ge=0, le=4, description="Feature access level (0-4)")


class FeatureFlagResponse(BaseModel):
    """Response with feature flag state"""
    flag_key: str
    enabled: bool
    config: Optional[Dict[str, Any]] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
