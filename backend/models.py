# Pydantic models for Peptimancer
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Phase VII - Admin Enhancements Models

class AdjustCreditsBody(BaseModel):
    userId: str
    delta: int
    reason: str = Field(min_length=2, max_length=80)

class SetTierBody(BaseModel):
    userId: str
    tier: str  # basic | pro | enterprise | admin

class UserSummary(BaseModel):
    id: str
    email: EmailStr
    role: str
    tier: str
    credits: int
    lastLogin: Optional[datetime] = None
