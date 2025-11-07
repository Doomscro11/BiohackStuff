# Authentication Routes for Peptimancer Enterprise
import os
import re
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, status, Response, Depends
from pydantic import BaseModel, EmailStr, validator
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

# Create router
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Request models
class EmailRequest(BaseModel):
    email: EmailStr
    
    @validator("email")
    def normalize_email(cls, v):
        return v.lower().strip()

class VerifyRequest(BaseModel):
    email: EmailStr
    code: str
    
    @validator("email")
    def normalize_email(cls, v):
        return v.lower().strip()
    
    @validator("code")
    def validate_code(cls, v):
        if not v or not v.isdigit() or len(v) != OTP_LENGTH:
            raise ValueError(f"Code must be {OTP_LENGTH} digits")
        return v

class User(BaseModel):
    id: str
    email: EmailStr
    role: str = "researcher"
    org_id: str = "default"
    created_at: datetime
    last_login: datetime

# Utility functions
def normalize_email(email: str) -> str:
    """Normalize email address"""
    return email.strip().lower()

def generate_otp() -> str:
    """Generate a random OTP code"""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))

async def is_user_locked_out(email: str) -> bool:
    """Check if user is currently locked out due to failed attempts"""
    cutoff_time = datetime.utcnow() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    
    recent_attempts = await login_attempts_collection.count_documents({
        "email": email,
        "success": False,
        "timestamp": {"$gte": cutoff_time}
    })
    
    return recent_attempts >= MAX_LOGIN_ATTEMPTS

async def log_login_attempt(email: str, success: bool, ip_address: str = None):
    """Log a login attempt for rate limiting"""
    await login_attempts_collection.insert_one({
        "email": email,
        "success": success,
        "timestamp": datetime.utcnow(),
        "ip_address": ip_address
    })

async def send_otp_email(email: str, code: str) -> bool:
    """Send OTP via email (implement SMTP in production)"""
    # TODO: Implement SMTP email sending
    # For now, just log the code
    logger.info(f"OTP for {email}: {code} (expires in {OTP_EXPIRES_MINUTES} minutes)")
    return True

# Auth endpoints
@auth_router.post("/magic/request")
async def request_magic_code(request: Request, body: EmailRequest):
    """Request a magic code via email"""
    email = normalize_email(body.email)
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Check if user is locked out
        if await is_user_locked_out(email):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
            )
        
        # Generate OTP
        code = generate_otp()
        expires = datetime.utcnow() + timedelta(minutes=OTP_EXPIRES_MINUTES)
        
        # Store code in database
        await magic_codes_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "email": email,
                    "code": code,
                    "expires": expires,
                    "created_at": datetime.utcnow(),
                    "used": False
                }
            },
            upsert=True
        )
        
        # Send email (or return code in demo mode)
        if ENABLE_DEMO_OTP:
            logger.info(f"Demo OTP generated for {email}: {code}")
            return {
                "success": True,
                "message": f"Magic code sent to {email}",
                "demo_code": code,  # Remove in production!
                "expires_in_minutes": OTP_EXPIRES_MINUTES
            }
        else:
            # Send actual email
            email_sent = await send_otp_email(email, code)
            if not email_sent:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send magic code"
                )
            
            return {
                "success": True,
                "message": f"Magic code sent to {email}",
                "expires_in_minutes": OTP_EXPIRES_MINUTES
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send magic code to {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send magic code"
        )

@auth_router.post("/magic/verify")
async def verify_magic_code(request: Request, response: Response, body: VerifyRequest):
    """Verify magic code and create session"""
    email = normalize_email(body.email)
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Check if user is locked out
        if await is_user_locked_out(email):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
            )
        
        # Find and verify code
        code_record = await magic_codes_collection.find_one({"email": email})
        
        if (not code_record or 
            code_record.get("code") != body.code or 
            code_record.get("expires") < datetime.utcnow() or
            code_record.get("used", False)):
            
            await log_login_attempt(email, False, client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired magic code"
            )
        
        # Mark code as used
        await magic_codes_collection.update_one(
            {"email": email},
            {"$set": {"used": True, "used_at": datetime.utcnow()}}
        )
        
        # Determine user role
        role = "admin" if email in ADMIN_EMAILS else "researcher"
        logger.info(f"Role determination: email={email}, ADMIN_EMAILS={ADMIN_EMAILS}, role={role}")
        
        # Create or update user
        now = datetime.utcnow()
        user_doc = await users_collection.find_one_and_update(
            {"email": email},
            {
                "$setOnInsert": {
                    "email": email,
                    "created_at": now,
                    "org_id": "default"
                },
                "$set": {
                    "last_login": now,
                    "role": role  # Update role in case admin list changed
                }
            },
            upsert=True,
            return_document=True
        )
        
        user_id = str(user_doc["_id"])
        
        # Create JWT token
        token = create_admin_token(user_id, email, role)
        
        # Set HTTP-only cookie
        cookie_secure = os.getenv("REQUIRE_HTTPS_COOKIES", "false").lower() == "true"
        response.set_cookie(
            "pmnc_jwt",
            token,
            httponly=True,
            secure=cookie_secure,  # Set to True in production with HTTPS
            samesite="Lax",
            max_age=60 * 60 * int(os.getenv("JWT_EXPIRES_HOURS", "72")),
            path="/"
        )
        
        # Log successful attempt
        await log_login_attempt(email, True, client_ip)
        
        logger.info(f"User authenticated: {email} (role: {role})")
        
        return {
            "success": True,
            "role": role,
            "email": email,
            "message": "Authentication successful"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify magic code for {email}: {e}")
        await log_login_attempt(email, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@auth_router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing session cookie"""
    response.delete_cookie("pmnc_jwt", path="/")
    return {"success": True, "message": "Logged out successfully"}

@auth_router.get("/me")
async def get_current_user_info(request: Request):
    """Get current user information"""
    from middleware.auth import get_current_user
    
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "org_id": user["org_id"],
        "is_admin": user["role"] == "admin"
    }

@auth_router.get("/admin/status")
async def get_admin_status():
    """Get admin configuration status (public endpoint for troubleshooting)"""
    return {
        "admin_emails_configured": len(ADMIN_EMAILS) > 0,
        "demo_mode": ENABLE_DEMO_OTP,
        "otp_length": OTP_LENGTH,
        "otp_expires_minutes": OTP_EXPIRES_MINUTES,
        "max_login_attempts": MAX_LOGIN_ATTEMPTS,
        "lockout_duration_minutes": LOCKOUT_DURATION_MINUTES
    }