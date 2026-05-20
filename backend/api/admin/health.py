# Admin Health Monitoring Routes for Peptimancer
import os
import time
import logging
from fastapi import APIRouter, Request, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from middleware.auth import require_admin
from services.settings import get_settings

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Router
router = APIRouter(prefix="/api/admin/health", tags=["admin-health"])

@router.get("")
async def get_system_health(request: Request):
    """
    Get system health metrics and status
    Requires: admin role + 2FA
    """
    # RBAC check
    user = require_admin(request)
    
    # Phase 7.1: Require 2FA for admin endpoints
    if not getattr(request.state, "admin2fa", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA verification required"
        )
    
    try:
        # Get current settings
        settings = await get_settings()
        
        # Database ping
        t0 = time.time()
        await db.command("ping")
        db_latency_ms = round((time.time() - t0) * 1000, 2)
        
        # Collection statistics (defensive)
        collection_names = await db.list_collection_names()
        
        # Runs count
        runs_count = 0
        if "vault_ledger" in collection_names:
            runs_count = await db.vault_ledger.estimated_document_count()
        
        # Quotes backlog (synthesis requests)
        quotes_backlog = 0
        if "synthesis_requests" in collection_names:
            quotes_backlog = await db.synthesis_requests.count_documents({
                "status": {"$in": ["processing", "queued"]}
            })
        
        # Recent errors
        errors_recent = 0
        if "errors" in collection_names:
            cutoff_time = time.time() - 86400  # 24 hours ago
            errors_recent = await db.errors.count_documents({
                "timestamp": {"$gt": cutoff_time}
            })
        
        # System uptime (Linux-specific, fallback gracefully)
        uptime = "N/A"
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
                uptime = f"{int(uptime_seconds)}s"
        except:
            uptime = "unknown"
        
        # Get error statistics
        from observability import get_error_stats
        error_stats = await get_error_stats()
        
        return {
            "mode": settings.get("integrationsMode", "sandbox"),
            "demo": settings.get("demoMode", False),
            "db": {
                "latencyMs": db_latency_ms,
                "ok": db_latency_ms < 150
            },
            "services": {
                "generateApi": True,  # API is running if we can respond
                "exportApi": True,
                "croWebhook": settings.get("croEnabled", False),
                "billing": settings.get("billingEnabled", False)
            },
            "metrics": {
                "runs": runs_count,
                "quotesBacklog": quotes_backlog,
                "errors24h": errors_recent
            },
            "errors": {
                "lastKind": error_stats.get("lastKind"),
                "lastTs": error_stats.get("lastTs"),
                "count24h": error_stats.get("count24h", 0)
            },
            "uptime": uptime
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )
