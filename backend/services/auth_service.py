"""
Authentication Service
Handles OTP generation, verification, and user management logic
"""

import os
import random
import string
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient

from auth.jwt import sign_jwt, create_admin_token

logger = logging.getLogger(__name__)

# Configuration
ADMIN_EMAILS = [
    email.strip().lower() 
    for email in os.getenv("ADMIN_EMAILS", "").split(",") 
    if email.strip()
]
OTP_LENGTH = int(os.getenv("OTP_LENGTH", "6"))
OTP_EXPIRES_MINUTES = int(os.getenv("OTP_EXPIRES_MINUTES", "10"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))
ENABLE_DEMO_OTP = os.getenv("ENABLE_DEMO_OTP", "true").lower() == "true"

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
magic_codes_collection = db['_magic_codes']
users_collection = db['users']
login_attempts_collection = db['_login_attempts']


def normalize_email(email: str) -> str:
    """Normalize email address"""
    return email.strip().lower()


def generate_otp() -> str:
    """Generate a random OTP code"""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def determine_role(email: str) -> str:
    """Determine user role based on email"""
    normalized = normalize_email(email)
    return "admin" if normalized in ADMIN_EMAILS else "researcher"


async def check_rate_limit(email: str) -> Dict[str, Any]:
    """
    Check if user is rate-limited
    
    Returns:
        Dict with 'allowed' (bool) and optional 'retry_after' (datetime)
    """
    normalized = normalize_email(email)
    
    # Check recent failed attempts
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    
    failed_attempts = await login_attempts_collection.count_documents({
        'email': normalized,
        'success': False,
        'timestamp': {'$gte': cutoff_time}
    })
    
    if failed_attempts >= MAX_LOGIN_ATTEMPTS:
        # Find the earliest attempt to calculate retry_after
        earliest = await login_attempts_collection.find_one(
            {
                'email': normalized,
                'success': False,
                'timestamp': {'$gte': cutoff_time}
            },
            sort=[('timestamp', 1)]
        )
        
        if earliest:
            retry_after = earliest['timestamp'] + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            return {
                'allowed': False,
                'retry_after': retry_after
            }
    
    return {'allowed': True}


async def record_login_attempt(email: str, success: bool, metadata: Optional[Dict] = None):
    """Record a login attempt for rate limiting"""
    await login_attempts_collection.insert_one({
        'email': normalize_email(email),
        'success': success,
        'timestamp': datetime.now(timezone.utc),
        'metadata': metadata or {}
    })


async def create_magic_code(email: str) -> Dict[str, Any]:
    """
    Create and store a magic code for the given email
    
    Returns:
        Dict with 'code' and 'expires_at'
    """
    normalized = normalize_email(email)
    
    # Generate OTP
    code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRES_MINUTES)
    
    # Store in database
    await magic_codes_collection.update_one(
        {'email': normalized},
        {
            '$set': {
                'code': code,
                'expires_at': expires_at,
                'created_at': datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    logger.info(f"Magic code created for {normalized}, expires at {expires_at}")
    
    return {
        'code': code if ENABLE_DEMO_OTP else None,
        'expires_at': expires_at
    }


async def verify_magic_code(email: str, code: str) -> Optional[Dict[str, Any]]:
    """
    Verify a magic code
    
    Returns:
        User data dict if valid, None if invalid
    """
    normalized = normalize_email(email)
    
    # Find the magic code
    magic_code_doc = await magic_codes_collection.find_one({'email': normalized})
    
    if not magic_code_doc:
        logger.warning(f"No magic code found for {normalized}")
        return None
    
    # Check expiry
    expires_at = magic_code_doc['expires_at']
    # Ensure expires_at is timezone-aware
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if datetime.now(timezone.utc) > expires_at:
        logger.warning(f"Expired magic code for {normalized}")
        await magic_codes_collection.delete_one({'email': normalized})
        return None
    
    # Verify code
    if magic_code_doc['code'] != code:
        logger.warning(f"Invalid code attempt for {normalized}")
        return None
    
    # Code is valid - delete it (one-time use)
    await magic_codes_collection.delete_one({'email': normalized})
    
    # Get or create user
    role = determine_role(normalized)
    user = await users_collection.find_one({'email': normalized})
    
    if not user:
        # Create new user
        user = {
            'id': f"user_{normalized.split('@')[0]}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            'email': normalized,
            'role': role,
            'org_id': 'default',
            'created_at': datetime.now(timezone.utc),
            'last_login': datetime.now(timezone.utc)
        }
        await users_collection.insert_one(user)
        logger.info(f"Created new user: {normalized} with role {role}")
    else:
        # Check if user has an id field, if not add it (for legacy users)
        if not user.get('id'):
            user_id = f"user_{normalized.split('@')[0]}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            await users_collection.update_one(
                {'email': normalized},
                {'$set': {
                    'id': user_id,
                    'last_login': datetime.now(timezone.utc)
                }}
            )
            user['id'] = user_id
            logger.info(f"Added missing id field to existing user: {normalized}")
        else:
            # Update last login
            await users_collection.update_one(
                {'email': normalized},
                {'$set': {'last_login': datetime.now(timezone.utc)}}
            )
    
    return {
        'id': user['id'],
        'email': user['email'],
        'role': user.get('role', role),
        'org_id': user.get('org_id', 'default')
    }


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    return await users_collection.find_one({'id': user_id}, {'_id': 0})


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    normalized = normalize_email(email)
    return await users_collection.find_one({'email': normalized}, {'_id': 0})


def create_jwt_token(user: Dict[str, Any]) -> str:
    """Create JWT token for user"""
    if user['role'] == 'admin':
        return create_admin_token(
            user_id=user['id'],
            email=user['email'],
            role=user['role']
        )
    else:
        claims = {
            "sub": user['id'],
            "email": user['email'],
            "role": user['role'],
            "orgId": user.get('org_id', 'default'),
            "scope": "user"
        }
        return sign_jwt(claims)
