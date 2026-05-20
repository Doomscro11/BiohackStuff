"""
Security utilities for JWT, password hashing, and authentication.
"""

import os
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any


JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24 * 7  # 7 days


def create_jwt(payload: Dict[str, Any], expires_hours: Optional[int] = None) -> str:
    """
    Create a JWT token with the given payload.
    
    Args:
        payload: Dictionary to encode in the token
        expires_hours: Token expiry in hours (default: 7 days)
    
    Returns:
        Encoded JWT string
    """
    if expires_hours is None:
        expires_hours = JWT_EXPIRY_HOURS
    
    exp = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    payload_copy = payload.copy()
    payload_copy['exp'] = exp
    
    return jwt.encode(payload_copy, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT string to verify
    
    Returns:
        Decoded payload if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
