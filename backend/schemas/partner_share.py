"""
Partner Share API Schemas
Request/response models for partner share operations
"""

from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field, EmailStr


class ShareCreationRequest(BaseModel):
    """Request to create a new partner share"""
    file_id: str
    recipient_email: EmailStr
    recipient_first_name: str
    company_or_project: str
    expires_in_days: int = 14
    max_downloads: int = 10
    ip_allowlist: List[str] = Field(default_factory=list)
    watermark_enabled: bool = True
    internal_notes: str = ""
    
    class Config:
        arbitrary_types_allowed = True


class ShareRotationResult(BaseModel):
    """Result of share token rotation"""
    share_id: str
    old_token: str
    new_token: str
    new_expires_at: datetime
    rotated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        arbitrary_types_allowed = True
