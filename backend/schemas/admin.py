"""
Admin API Schemas
Request/response models for admin operations
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class AdjustCreditsBody(BaseModel):
    """Request body for adjusting user credits"""
    userId: str
    delta: int
    reason: str = Field(min_length=2, max_length=80)


class SetTierBody(BaseModel):
    """Request body for setting user tier"""
    userId: str
    tier: str  # basic | pro | enterprise | admin


class UserSummary(BaseModel):
    """User summary response for admin dashboard"""
    id: str
    email: EmailStr
    role: str
    tier: str
    credits: int
    lastLogin: Optional[datetime] = None
