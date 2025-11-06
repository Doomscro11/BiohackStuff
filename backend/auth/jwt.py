# JWT Token Management for Peptimancer Enterprise
import os
import time
import hmac
import base64
import json
import hashlib
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me_in_production")
JWT_ISSUER = os.getenv("JWT_ISSUER", "peptimancer")
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "72"))

def _base64url_encode(data: bytes) -> str:
    """Base64URL encode without padding"""
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def _base64url_decode(data: str) -> bytes:
    """Base64URL decode with padding"""
    # Add padding if necessary
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return base64.urlsafe_b64decode(data)

def sign_jwt(claims: Dict[str, Any]) -> str:
    """Create and sign a JWT token"""
    try:
        # Header
        header = {"alg": "HS256", "typ": "JWT"}
        
        # Payload with standard claims
        now = int(time.time())
        payload = {
            **claims,
            "iss": JWT_ISSUER,
            "iat": now,
            "exp": now + (JWT_EXPIRES_HOURS * 3600),
            "nbf": now  # Not before
        }
        
        # Encode header and payload
        header_encoded = _base64url_encode(json.dumps(header, separators=(',', ':')).encode())
        payload_encoded = _base64url_encode(json.dumps(payload, separators=(',', ':')).encode())
        
        # Create signature
        message = f"{header_encoded}.{payload_encoded}"
        signature = hmac.new(
            JWT_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_encoded = _base64url_encode(signature)
        
        token = f"{header_encoded}.{payload_encoded}.{signature_encoded}"
        logger.info(f"JWT signed for user: {claims.get('sub', 'unknown')}")
        return token
        
    except Exception as e:
        logger.error(f"Failed to sign JWT: {e}")
        raise ValueError("Failed to create JWT token")

def verify_jwt(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        # Split token
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        header_encoded, payload_encoded, signature_encoded = parts
        
        # Verify signature
        message = f"{header_encoded}.{payload_encoded}"
        expected_signature = hmac.new(
            JWT_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        expected_signature_encoded = _base64url_encode(expected_signature)
        
        if not hmac.compare_digest(signature_encoded, expected_signature_encoded):
            raise ValueError("Invalid signature")
        
        # Decode header and payload
        header = json.loads(_base64url_decode(header_encoded))
        payload = json.loads(_base64url_decode(payload_encoded))
        
        # Verify standard claims
        if payload.get("iss") != JWT_ISSUER:
            raise ValueError("Invalid issuer")
        
        now = int(time.time())
        if payload.get("exp", 0) < now:
            raise ValueError("Token expired")
        
        if payload.get("nbf", 0) > now:
            raise ValueError("Token not yet valid")
        
        logger.debug(f"JWT verified for user: {payload.get('sub', 'unknown')}")
        return payload
        
    except json.JSONDecodeError:
        logger.warning("Failed to decode JWT payload")
        raise ValueError("Invalid token format")
    except Exception as e:
        logger.warning(f"JWT verification failed: {e}")
        raise ValueError("Invalid or expired token")

def extract_user_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user information from JWT payload"""
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "researcher"),
        "org_id": payload.get("orgId", "default"),
        "issued_at": payload.get("iat"),
        "expires_at": payload.get("exp")
    }

def create_admin_token(user_id: str, email: str, role: str = "admin", org_id: str = "default") -> str:
    """Create a JWT token for an admin user"""
    claims = {
        "sub": user_id,
        "email": email,
        "role": role,
        "orgId": org_id,
        "scope": "admin" if role == "admin" else "user"
    }
    return sign_jwt(claims)

def is_token_expired(token: str) -> bool:
    """Check if a token is expired without raising exceptions"""
    try:
        verify_jwt(token)
        return False
    except ValueError as e:
        return "expired" in str(e).lower()

def get_token_expiry(token: str) -> Optional[int]:
    """Get token expiry timestamp"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        payload = json.loads(_base64url_decode(parts[1]))
        return payload.get("exp")
    except:
        return None

# Security utilities
def generate_secure_random(length: int = 32) -> str:
    """Generate a secure random string for secrets"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_password(password: str) -> str:
    """Hash a password using bcrypt (for future password-based auth)"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))