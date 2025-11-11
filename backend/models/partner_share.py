"""
Partner Share Models (Phase IXf+)
Models for secure external sharing of PatentPulse Reclaim Packs
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr
import uuid


class SharePolicy(BaseModel):
    """Access policy for a partner share"""
    expires_at: datetime
    max_downloads: int = 10
    ip_allowlist: List[str] = Field(default_factory=list)  # CIDR notation supported
    rate_limit_per_ip: str = "30/min"
    watermark_enabled: bool = True
    
    class Config:
        arbitrary_types_allowed = True


class PartnerShare(BaseModel):
    """Partner share document"""
    share_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str  # Reference to patentpulse_exports
    file_name: str
    format: Literal["pdf", "json"]
    
    # Recipient info
    recipient_email: EmailStr
    recipient_first_name: str
    company_or_project: str
    
    # Access control
    policy: SharePolicy
    share_token: str  # HMAC signed token
    
    # State
    state: Literal["active", "expired", "revoked"] = "active"
    download_count: int = 0
    last_accessed_at: Optional[datetime] = None
    
    # Metadata
    created_by: str  # Admin email
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revoked_reason: Optional[str] = None
    
    # Notes
    internal_notes: str = ""
    
    class Config:
        arbitrary_types_allowed = True


class PartnerShareEvent(BaseModel):
    """Analytics event for partner share access"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    share_id: str
    event: Literal["open", "download", "blocked", "expired", "revoked"]
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Request context
    ip: str
    user_agent: Optional[str] = None
    geo_country: Optional[str] = None
    geo_city: Optional[str] = None
    
    # Event details
    reason: Optional[str] = None  # For blocked/expired/revoked
    file_size_kb: Optional[int] = None  # For downloads
    
    class Config:
        arbitrary_types_allowed = True


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
