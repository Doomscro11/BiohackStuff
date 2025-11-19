"""
Configuration management for Peptimancer monorepo.
Centralizes environment variable loading and settings.
"""

import os
from typing import List
from functools import lru_cache


class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'peptimancer_db')
    
    # JWT & Security
    JWT_SECRET: str = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRY_HOURS: int = 24 * 7  # 7 days
    
    # Admin
    ADMIN_EMAILS: List[str] = os.environ.get('ADMIN_EMAILS', '').split(',')
    
    # Billing & Credits
    TIER_FREE_CREDITS: int = int(os.environ.get('TIER_FREE_CREDITS', '50'))
    TIER_BASIC_CREDITS: int = int(os.environ.get('TIER_BASIC_CREDITS', '200'))
    TIER_PRO_CREDITS: int = int(os.environ.get('TIER_PRO_CREDITS', '1000'))
    TIER_ENT_CREDITS: int = int(os.environ.get('TIER_ENT_CREDITS', '5000'))
    
    # Features
    ENABLE_DEMO_OTP: bool = os.environ.get('ENABLE_DEMO_OTP', 'true').lower() == 'true'
    FEATURE_PATENTPULSE: bool = os.environ.get('FEATURE_PATENTPULSE', 'false').lower() == 'true'
    FEATURE_PATENTPULSE_PARTNER: bool = os.environ.get('FEATURE_PATENTPULSE_PARTNER', 'false').lower() == 'true'
    
    # PatentPulse Partner Portal
    PARTNER_SIGNING_SECRET: str = os.environ.get('PARTNER_SIGNING_SECRET', 'change_in_production')
    PARTNER_SHARE_TTL_DAYS: int = int(os.environ.get('PARTNER_SHARE_TTL_DAYS', '14'))
    PARTNER_MAX_DOWNLOADS: int = int(os.environ.get('PARTNER_MAX_DOWNLOADS', '10'))
    
    # App URLs
    APP_URL: str = os.environ.get('APP_URL', 'http://localhost:3000')
    BACKEND_URL: str = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
