"""
Partner Shares API Routes (Phase IXf+)
Admin and public endpoints for partner share management
"""

import os
import hmac
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import FileResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
import uuid
import json
from pathlib import Path

from models.partner_share import (
    PartnerShare,
    SharePolicy,
    ShareCreationRequest,
    ShareRotationResult
)
from analytics.partner_analytics import track_event, get_share_analytics, get_dashboard_metrics
from watermark.pdf_watermark import watermark_pdf, add_json_watermark_headers
from middleware.auth import get_current_user, require_role
from services.settings import is_feature_enabled
from services import partner_share_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/patentpulse/partner", tags=["partner_shares"])

# Configuration from environment
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@peptimancer.com')
RATE_LIMIT_PER_IP = os.environ.get('RATE_LIMIT_PER_IP', '30/min')

# Rate limiting in-memory store (simple implementation)
rate_limit_store: Dict[str, List[datetime]] = {}


async def check_feature_flag():
    """Check if partner portal feature is enabled"""
    if not await is_feature_enabled('FEATURE_PATENTPULSE_PARTNER'):
        raise HTTPException(status_code=503, detail="Partner portal feature not enabled")


# Token generation and verification are now handled by partner_share_service
generate_share_token = partner_share_service.generate_share_token
verify_share_token = partner_share_service.verify_share_token


def check_rate_limit(ip: str) -> bool:
    """
    Check if IP is within rate limit
    
    Returns:
        True if allowed, False if rate limited
    """
    # Parse rate limit (e.g., "30/min")
    try:
        limit_parts = RATE_LIMIT_PER_IP.split('/')
        max_requests = int(limit_parts[0])
        window_unit = limit_parts[1] if len(limit_parts) > 1 else 'min'
        
        # Convert to seconds
        window_seconds = {
            'sec': 1,
            'min': 60,
            'hour': 3600,
            'day': 86400
        }.get(window_unit, 60)
        
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean old entries
        if ip in rate_limit_store:
            rate_limit_store[ip] = [ts for ts in rate_limit_store[ip] if ts > cutoff]
        else:
            rate_limit_store[ip] = []
        
        # Check limit
        if len(rate_limit_store[ip]) >= max_requests:
            return False
        
        # Add current request
        rate_limit_store[ip].append(now)
        return True
    
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return True  # Fail open


def check_ip_allowlist(ip: str, allowlist: List[str]) -> bool:
    """
    Check if IP is in allowlist (supports CIDR notation)
    
    Returns:
        True if allowed or allowlist is empty
    """
    if not allowlist:
        return True
    
    # Simple implementation (exact match)
    # TODO: Add CIDR support with ipaddress module
    return ip in allowlist


# ============================================================
# ADMIN ENDPOINTS (2FA REQUIRED)
# ============================================================

@router.post("/shares", dependencies=[Depends(require_role(['admin']))])
async def create_partner_share(
    request: ShareCreationRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new partner share (Admin only, 2FA required)
    """
    check_feature_flag()
    
    try:
        # Verify file exists
        export_doc = await db.patentpulse_exports.find_one({"file_id": request.file_id})
        if not export_doc:
            raise HTTPException(status_code=404, detail=f"Export file not found: {request.file_id}")
        
        # Create share document
        share_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)
        
        policy = SharePolicy(
            expires_at=expires_at,
            max_downloads=request.max_downloads,
            ip_allowlist=request.ip_allowlist,
            watermark_enabled=request.watermark_enabled
        )
        
        share_token = generate_share_token(share_id, request.file_id, expires_at)
        
        share = PartnerShare(
            share_id=share_id,
            file_id=request.file_id,
            file_name=export_doc.get("file_name", "reclaim_pack.pdf"),
            format=export_doc.get("format", "pdf"),
            recipient_email=request.recipient_email,
            recipient_first_name=request.recipient_first_name,
            company_or_project=request.company_or_project,
            policy=policy,
            share_token=share_token,
            created_by=current_user["email"],
            internal_notes=request.internal_notes
        )
        
        # Insert into database
        share_dict = share.dict()
        share_dict["policy"] = share_dict["policy"]  # Ensure nested model is serialized
        
        await db.partner_shares.insert_one(share_dict)
        
        logger.info(f"Created partner share: {share_id} for {request.recipient_email}")
        
        # Generate share URL
        app_url = os.environ.get('APP_URL', 'http://localhost:3000')
        share_url = f"{app_url}/share/{share_token}"
        
        return {
            "share_id": share_id,
            "share_token": share_token,
            "share_url": share_url,
            "recipient_email": request.recipient_email,
            "expires_at": expires_at.isoformat(),
            "max_downloads": request.max_downloads,
            "created_at": share.created_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create partner share: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create share: {str(e)}")


@router.get("/shares", dependencies=[Depends(require_role(['admin']))])
async def list_partner_shares(
    state: Optional[str] = None,
    recipient: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List partner shares with filters (Admin only)
    """
    check_feature_flag()
    
    try:
        query = {}
        if state:
            query["state"] = state
        if recipient:
            query["recipient_email"] = {"$regex": recipient, "$options": "i"}
        
        # Get total count
        total = await db.partner_shares.count_documents(query)
        
        # Get paginated results
        shares = await db.partner_shares.find(query) \
            .sort("created_at", -1) \
            .skip(offset) \
            .limit(limit) \
            .to_list(length=None)
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "shares": shares
        }
    
    except Exception as e:
        logger.error(f"Failed to list shares: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list shares: {str(e)}")


@router.get("/shares/{share_id}", dependencies=[Depends(require_role(['admin']))])
async def get_partner_share(share_id: str) -> Dict[str, Any]:
    """
    Get partner share details (Admin only)
    """
    check_feature_flag()
    
    try:
        share = await db.partner_shares.find_one({"share_id": share_id})
        if not share:
            raise HTTPException(status_code=404, detail=f"Share not found: {share_id}")
        
        return share
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get share: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get share: {str(e)}")


@router.post("/shares/{share_id}/rotate", dependencies=[Depends(require_role(['admin']))])
async def rotate_share_token(
    share_id: str,
    current_user: dict = Depends(get_current_user)
) -> ShareRotationResult:
    """
    Rotate share token (Admin only)
    Generates new token, invalidates old one
    """
    check_feature_flag()
    
    try:
        share = await db.partner_shares.find_one({"share_id": share_id})
        if not share:
            raise HTTPException(status_code=404, detail=f"Share not found: {share_id}")
        
        old_token = share["share_token"]
        
        # Generate new token with extended expiry
        new_expires_at = datetime.now(timezone.utc) + timedelta(days=PARTNER_SHARE_TTL_DAYS)
        new_token = generate_share_token(share_id, share["file_id"], new_expires_at)
        
        # Update share
        await db.partner_shares.update_one(
            {"share_id": share_id},
            {
                "$set": {
                    "share_token": new_token,
                    "policy.expires_at": new_expires_at,
                    "state": "active"
                }
            }
        )
        
        logger.info(f"Rotated token for share: {share_id} by {current_user['email']}")
        
        return ShareRotationResult(
            share_id=share_id,
            old_token=old_token,
            new_token=new_token,
            new_expires_at=new_expires_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rotate token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rotate token: {str(e)}")


@router.post("/shares/{share_id}/revoke", dependencies=[Depends(require_role(['admin']))])
async def revoke_share(
    share_id: str,
    reason: str = "Revoked by admin",
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Revoke a share (Admin only)
    """
    check_feature_flag()
    
    try:
        share = await db.partner_shares.find_one({"share_id": share_id})
        if not share:
            raise HTTPException(status_code=404, detail=f"Share not found: {share_id}")
        
        # Update share
        await db.partner_shares.update_one(
            {"share_id": share_id},
            {
                "$set": {
                    "state": "revoked",
                    "revoked_at": datetime.now(timezone.utc),
                    "revoked_by": current_user["email"],
                    "revoked_reason": reason
                }
            }
        )
        
        # Track event
        await track_event(
            share_id=share_id,
            event="revoked",
            ip="internal",
            reason=reason
        )
        
        logger.info(f"Revoked share: {share_id} by {current_user['email']}")
        
        return {
            "share_id": share_id,
            "state": "revoked",
            "revoked_at": datetime.now(timezone.utc).isoformat(),
            "revoked_by": current_user["email"],
            "reason": reason
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke share: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke share: {str(e)}")


@router.get("/shares/{share_id}/analytics", dependencies=[Depends(require_role(['admin']))])
async def get_share_analytics_endpoint(share_id: str) -> Dict[str, Any]:
    """
    Get analytics for a specific share (Admin only)
    """
    check_feature_flag()
    
    try:
        analytics = await get_share_analytics(share_id)
        return analytics
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/dashboard/metrics", dependencies=[Depends(require_role(['admin']))])
async def get_dashboard_metrics_endpoint(
    days: int = 30
) -> Dict[str, Any]:
    """
    Get dashboard metrics (Admin only)
    """
    check_feature_flag()
    
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        metrics = await get_dashboard_metrics(start_date=start_date)
        return metrics
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


# ============================================================
# PUBLIC ENDPOINTS (NO AUTH)
# ============================================================

@router.get("/share/{token}")
async def get_share_metadata(token: str, request: Request) -> Dict[str, Any]:
    """
    Get share metadata for partner landing page (Public)
    """
    check_feature_flag()
    
    client_ip = request.client.host if request.client else "unknown"
    
    # Verify token
    token_data = verify_share_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired share link")
    
    share_id = token_data["share_id"]
    
    try:
        # Get share document
        share = await db.partner_shares.find_one({"share_id": share_id})
        if not share:
            raise HTTPException(status_code=404, detail="Share not found")
        
        # Check state
        if share["state"] == "revoked":
            await track_event(share_id, "blocked", client_ip, reason="revoked")
            raise HTTPException(status_code=403, detail="This share link has been revoked")
        
        if share["state"] == "expired":
            await track_event(share_id, "blocked", client_ip, reason="expired")
            raise HTTPException(status_code=410, detail="This share link has expired")
        
        # Check IP allowlist
        if not check_ip_allowlist(client_ip, share["policy"].get("ip_allowlist", [])):
            await track_event(share_id, "blocked", client_ip, reason="ip_not_allowed")
            raise HTTPException(status_code=403, detail="Your IP address is not authorized")
        
        # Track open event
        user_agent = request.headers.get("user-agent")
        await track_event(share_id, "open", client_ip, user_agent=user_agent)
        
        # Update last accessed
        await db.partner_shares.update_one(
            {"share_id": share_id},
            {"$set": {"last_accessed_at": datetime.now(timezone.utc)}}
        )
        
        # Return metadata (no sensitive data)
        return {
            "share_id": share_id,
            "file_name": share["file_name"],
            "format": share["format"],
            "recipient_first_name": share["recipient_first_name"],
            "company_or_project": share["company_or_project"],
            "expires_at": share["policy"]["expires_at"],
            "max_downloads": share["policy"]["max_downloads"],
            "download_count": share.get("download_count", 0),
            "downloads_remaining": max(0, share["policy"]["max_downloads"] - share.get("download_count", 0)),
            "support_email": SUPPORT_EMAIL
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get share metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to load share")


@router.get("/share/{token}/download")
async def download_shared_file(token: str, request: Request):
    """
    Download shared file with policy enforcement (Public)
    """
    check_feature_flag()
    
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    
    # Rate limit check
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    # Verify token
    token_data = verify_share_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired share link")
    
    share_id = token_data["share_id"]
    file_id = token_data["file_id"]
    
    try:
        # Get share document
        share = await db.partner_shares.find_one({"share_id": share_id})
        if not share:
            raise HTTPException(status_code=404, detail="Share not found")
        
        # Check state
        if share["state"] == "revoked":
            await track_event(share_id, "blocked", client_ip, reason="revoked")
            raise HTTPException(status_code=403, detail="This share link has been revoked")
        
        if share["state"] == "expired":
            await track_event(share_id, "blocked", client_ip, reason="expired")
            raise HTTPException(status_code=410, detail="This share link has expired")
        
        # Check max downloads
        if share.get("download_count", 0) >= share["policy"]["max_downloads"]:
            await track_event(share_id, "blocked", client_ip, reason="max_downloads_reached")
            raise HTTPException(status_code=403, detail="Maximum download limit reached")
        
        # Check IP allowlist
        if not check_ip_allowlist(client_ip, share["policy"].get("ip_allowlist", [])):
            await track_event(share_id, "blocked", client_ip, reason="ip_not_allowed")
            raise HTTPException(status_code=403, detail="Your IP address is not authorized")
        
        # Get export file
        export_doc = await db.patentpulse_exports.find_one({"file_id": file_id})
        if not export_doc:
            raise HTTPException(status_code=404, detail="Export file not found")
        
        file_path = Path(export_doc.get("file_path", ""))
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Apply watermark if enabled
        watermark_enabled = share["policy"].get("watermark_enabled", True)
        
        if watermark_enabled and share["format"] == "pdf":
            # Watermark PDF
            watermarked_path = file_path.parent / f"{file_path.stem}_watermarked.pdf"
            watermark_pdf(
                input_pdf=str(file_path),
                output_pdf=str(watermarked_path),
                recipient_email=share["recipient_email"],
                expires_at=share["policy"]["expires_at"],
                company=share["company_or_project"]
            )
            response_file = watermarked_path
        else:
            response_file = file_path
        
        # Increment download count
        await db.partner_shares.update_one(
            {"share_id": share_id},
            {
                "$inc": {"download_count": 1},
                "$set": {"last_accessed_at": datetime.now(timezone.utc)}
            }
        )
        
        # Track download event
        file_size_kb = int(response_file.stat().st_size / 1024)
        await track_event(
            share_id,
            "download",
            client_ip,
            user_agent=user_agent,
            file_size_kb=file_size_kb
        )
        
        logger.info(f"Partner download: share={share_id} file={file_id} ip={client_ip}")
        
        # Return file
        headers = {}
        if watermark_enabled and share["format"] == "json":
            # Add watermark headers for JSON
            headers["X-PatentPulse-Recipient"] = share["recipient_email"]
            headers["X-PatentPulse-Expiry"] = share["policy"]["expires_at"].isoformat()
            headers["X-PatentPulse-Confidential"] = "true"
        
        return FileResponse(
            path=str(response_file),
            filename=share["file_name"],
            media_type="application/pdf" if share["format"] == "pdf" else "application/json",
            headers=headers
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")
