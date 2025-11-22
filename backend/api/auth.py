# Authentication Routes for Peptimancer Enterprise
import os
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, HTTPException, status, Response, Depends
from pydantic import BaseModel, EmailStr, validator

from services import auth_service

logger = logging.getLogger(__name__)

# Configuration from service
ENABLE_DEMO_OTP = os.getenv("ENABLE_DEMO_OTP", "true").lower() == "true"
OTP_EXPIRES_MINUTES = int(os.getenv("OTP_EXPIRES_MINUTES", "10"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))

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
        OTP_LENGTH = int(os.getenv("OTP_LENGTH", "6"))
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

# Auth endpoints
@auth_router.post("/magic/request")
async def request_magic_code(request: Request, body: EmailRequest):
    """Request a magic code via email"""
    email = auth_service.normalize_email(body.email)
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Check rate limit
        rate_limit_result = await auth_service.check_rate_limit(email)
        if not rate_limit_result['allowed']:
            retry_after = rate_limit_result.get('retry_after')
            if retry_after:
                retry_minutes = int((retry_after - datetime.now()).total_seconds() / 60)
                detail = f"Too many failed attempts. Try again in {retry_minutes} minutes."
            else:
                detail = f"Too many failed attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail
            )
        
        # Create magic code
        result = await auth_service.create_magic_code(email)
        
        # Return response
        if ENABLE_DEMO_OTP and result['code']:
            logger.info(f"Demo OTP generated for {email}: {result['code']}")
            return {
                "success": True,
                "message": f"Magic code sent to {email}",
                "demo_code": result['code'],  # Remove in production!
                "expires_in_minutes": OTP_EXPIRES_MINUTES
            }
        else:
            # TODO: Send actual email
            logger.info(f"OTP for {email} (expires in {OTP_EXPIRES_MINUTES} minutes)")
            return {
                "success": True,
                "message": f"Magic code sent to {email}",
                "expires_in_minutes": OTP_EXPIRES_MINUTES
            }
            
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
    email = auth_service.normalize_email(body.email)
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Check rate limit
        rate_limit_result = await auth_service.check_rate_limit(email)
        if not rate_limit_result['allowed']:
            retry_after = rate_limit_result.get('retry_after')
            if retry_after:
                retry_minutes = int((retry_after - datetime.now()).total_seconds() / 60)
                detail = f"Too many failed attempts. Try again in {retry_minutes} minutes."
            else:
                detail = f"Too many failed attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail
            )
        
        # Verify code
        user_data = await auth_service.verify_magic_code(email, body.code)
        
        if not user_data:
            await auth_service.record_login_attempt(email, False, {'ip': client_ip})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired magic code"
            )
        
        # Create JWT token
        token = auth_service.create_jwt_token(user_data)
        
        # Set HTTP-only cookie
        cookie_secure = os.getenv("REQUIRE_HTTPS_COOKIES", "false").lower() == "true"
        response.set_cookie(
            "pmnc_jwt",
            token,
            httponly=True,
            secure=cookie_secure,
            samesite="Lax",
            max_age=60 * 60 * int(os.getenv("JWT_EXPIRES_HOURS", "72")),
            path="/"
        )
        
        # Log successful attempt
        await auth_service.record_login_attempt(email, True, {'ip': client_ip})
        
        logger.info(f"User authenticated: {email} (role: {user_data['role']})")
        
        return {
            "success": True,
            "role": user_data['role'],
            "email": user_data['email'],
            "message": "Authentication successful"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify magic code for {email}: {e}")
        await auth_service.record_login_attempt(email, False, {'ip': client_ip, 'error': str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@auth_router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing session cookie and 2FA cookie"""
    response.delete_cookie("pmnc_jwt", path="/")
    response.delete_cookie("pmnc_admin2fa", path="/")
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


# ==================== Phase 7.1: Admin 2FA (TOTP) ====================

class TwoFAVerifyBody(BaseModel):
    code: str

@auth_router.post("/2fa/start")
async def twofa_start(request: Request):
    """
    Start 2FA setup for admin users
    Returns TOTP secret and OTP Auth URI for QR code
    """
    from middleware.auth import get_current_user
    from auth.totp import ensure_totp_secret, get_otpauth_uri
    
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Generate or retrieve TOTP secret
    secret = await ensure_totp_secret(user["id"])
    uri = get_otpauth_uri(user["email"], secret)
    
    return {
        "ok": True,
        "otpauth": uri,
        "email": user["email"]
    }

@auth_router.post("/2fa/verify")
async def twofa_verify(body: TwoFAVerifyBody, response: Response, request: Request):
    """
    Verify 2FA code and issue admin2fa cookie
    This cookie grants elevated admin access for 30 minutes
    """
    from middleware.auth import get_current_user
    from auth.totp import verify_totp
    from observability import log_error
    
    user = get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Verify TOTP code
    is_valid = await verify_totp(user["id"], body.code)
    
    if not is_valid:
        await log_error("2fa_failed", {
            "userId": user["id"],
            "email": user["email"],
            "timestamp": datetime.utcnow().isoformat()
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code"
        )
    
    # Issue elevated admin2fa cookie (30 minutes)
    token = sign_jwt({
        "sub": user["id"],
        "email": user["email"],
        "role": "admin",
        "org_id": user.get("org_id", "default"),
        "scope": "admin2fa"
    })
    
    # Phase 7.1: Secure cookie settings (20 min session, Secure flag in prod)
    is_production = os.getenv("ENV", "development") == "production"
    
    response.set_cookie(
        "pmnc_admin2fa",
        token,
        httponly=True,
        secure=is_production,  # HTTPS only in production
        samesite="Strict",
        max_age=60 * 20,  # 20 minutes for tighter security
        path="/"
    )
    
    logger.info(f"2FA verified successfully for admin: {user['email']}")
    
    return {
        "ok": True,
        "message": "2FA verified successfully",
        "expires_in": 1800  # 30 minutes in seconds
    }

# ==================== Phase 8: Session Endpoint for FE State ====================

@auth_router.get("/session")
async def auth_session(request: Request):
    """
    Lightweight session endpoint for frontend state
    Returns user info, tier, credits, and feature level
    """
    from middleware.auth import get_current_user
    from billing.service import get_billing_state
    from services import feature_flags_service
    
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get billing state
    billing = await get_billing_state(user["id"])
    
    # Get feature level
    feature_level = await feature_flags_service.get_user_feature_level(user["id"])
    
    return {
        "email": user["email"],
        "role": user.get("role", "researcher"),
        "tier": billing.get("tier", "basic"),
        "credits": billing.get("credits", 0),
        "feature_level": feature_level
    }
