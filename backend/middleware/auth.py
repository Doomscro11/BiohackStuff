# Authentication Middleware for Peptimancer Enterprise
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from typing import Optional, Dict, Any
import logging
from auth.jwt import verify_jwt, extract_user_from_payload

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware that extracts user from JWT tokens"""
    
    def __init__(self, app):
        super().__init__(app)
        self.exempt_paths = {
            "/api/auth/magic/request",
            "/api/auth/magic/verify", 
            "/api/mode",
            "/api/generate-analogues",
            "/api/validate-sequence",
            "/healthz",
            "/docs",
            "/openapi.json"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and attach user information"""
        user = None
        token = None
        
        try:
            # Extract token from Authorization header or cookie
            auth_header = request.headers.get("authorization", "")
            if auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1].strip()
            
            # Fallback to cookie
            if not token:
                token = request.cookies.get("pmnc_jwt")
            
            # Verify and extract user if token exists
            if token:
                try:
                    payload = verify_jwt(token)
                    user = extract_user_from_payload(payload)
                    logger.debug(f"Authenticated user: {user['email']} (role: {user['role']})")
                except Exception as e:
                    logger.warning(f"Invalid token for request to {request.url.path}: {e}")
                    user = None
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            user = None
        
        # Attach user information to request state
        request.state.user = user
        request.state.user_id = user.get("id", "anonymous") if user else "anonymous"
        request.state.user_role = user.get("role", "anonymous") if user else "anonymous"
        request.state.is_authenticated = user is not None
        request.state.is_admin = user.get("role") == "admin" if user else False
        
        # Phase 7.1: Check admin2fa cookie for elevated access
        request.state.admin2fa = False
        admin2fa_token = request.cookies.get("pmnc_admin2fa")
        if admin2fa_token and user:
            try:
                admin2fa_payload = verify_jwt(admin2fa_token)
                # Verify it's the same user and has admin2fa scope
                if (admin2fa_payload.get("scope") == "admin2fa" and 
                    admin2fa_payload.get("sub") == user.get("id")):
                    request.state.admin2fa = True
                    logger.debug(f"Admin 2FA validated for: {user['email']}")
            except Exception as e:
                logger.warning(f"Invalid admin2fa token: {e}")
                request.state.admin2fa = False
        
        # Log authentication for audit trail
        if request.url.path.startswith("/api/admin") and user:
            logger.info(f"Admin access: {user['email']} accessing {request.url.path}")
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Helper function to get current user from request"""
    return getattr(request.state, 'user', None)

def require_auth(request: Request) -> Dict[str, Any]:
    """Helper function that requires authentication"""
    from fastapi import HTTPException, status
    
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

def require_admin(request: Request) -> Dict[str, Any]:
    """Helper function that requires admin role"""
    from fastapi import HTTPException, status
    
    user = require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return user

def get_user_permissions(user: Optional[Dict[str, Any]]) -> set:
    """Get user permissions based on role"""
    if not user:
        return set()
    
    role = user.get("role", "")
    
    permissions = {"read_public"}
    
    if role == "researcher":
        permissions.update({
            "generate_analogues",
            "export_pdf",
            "view_history"
        })
    elif role == "admin":
        permissions.update({
            "generate_analogues",
            "export_pdf", 
            "view_history",
            "admin_settings",
            "admin_users",
            "admin_audit"
        })
    
    return permissions

def has_permission(user: Optional[Dict[str, Any]], permission: str) -> bool:
    """Check if user has specific permission"""
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def require_role(allowed_roles: list):
    """
    Dependency for requiring specific roles with 2FA check for admin
    
    Usage:
        @router.get("/endpoint", dependencies=[Depends(require_role(['admin']))])
    """
    from fastapi import Depends, HTTPException, Request, status
    
    async def check_role(request: Request):
        # Check authentication
        user = get_current_user(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Check role
        user_role = user.get("role", "")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(allowed_roles)}"
            )
        
        # For admin role, require 2FA
        if "admin" in allowed_roles and user_role == "admin":
            admin2fa = getattr(request.state, 'admin2fa', False)
            if not admin2fa:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin 2FA required"
                )
        
        return user
    
    return check_role