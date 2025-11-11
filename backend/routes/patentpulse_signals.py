"""
PatentPulse Signals API Routes (Phase IXd)
API endpoints for market signal data and score adjustments
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, status, Depends, Query, Body
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
patentpulse_items = db['patentpulse_items']
patentpulse_signals = db['patentpulse_signals']

router = APIRouter(prefix="/api/patentpulse", tags=["patentpulse_signals"])


def require_admin_2fa(request: Request):
    """Require admin with 2FA for PatentPulse access"""
    from middleware.auth import require_admin
    
    user = require_admin(request)
    
    # Check admin2fa
    if not getattr(request.state, 'admin2fa', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin 2FA required for PatentPulse"
        )
    
    return user


class RecomputeRequest(BaseModel):
    """Request body for recompute endpoint"""
    patent_ids: Optional[List[str]] = None
    since: Optional[str] = None
    limit: Optional[int] = 50
    weights: Optional[dict] = None


@router.get("/signals/{patent_id}")
async def get_patent_signals(
    patent_id: str,
    user=Depends(require_admin_2fa)
):
    """
    Get market signals for a specific patent
    Returns features, market_factor, breakdown, and provenance
    """
    try:
        # Fetch signal document
        signal = await patentpulse_signals.find_one({"patent_id": patent_id})
        
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No signals found for patent {patent_id}"
            )
        
        # Fetch patent for breakdown
        patent = await patentpulse_items.find_one({"patent_id": patent_id})
        
        if not patent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patent {patent_id} not found"
            )
        
        # Convert ObjectId to string
        signal["_id"] = str(signal["_id"])
        if patent:
            patent["_id"] = str(patent["_id"])
        
        # Convert datetime fields
        for key in ["computed_at", "ttl_expires_at"]:
            if key in signal and isinstance(signal[key], datetime):
                signal[key] = signal[key].isoformat()
        
        # Convert provenance timestamps
        if "provenance" in signal:
            for prov in signal["provenance"]:
                if "ts" in prov and isinstance(prov["ts"], datetime):
                    prov["ts"] = prov["ts"].isoformat()
        
        return {
            "patent_id": patent_id,
            "features": signal.get("features", {}),
            "provenance": signal.get("provenance", []),
            "computed_at": signal.get("computed_at"),
            "breakdown": patent.get("commercial_breakdown", {}) if patent else {}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch signals for {patent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch signals: {str(e)}"
        )


@router.post("/signals/recompute")
async def recompute_signals(
    request_body: RecomputeRequest = Body(...),
    user=Depends(require_admin_2fa)
):
    """
    Trigger recomputation of market signals
    Can specify patent_ids, since date, limit, and custom weights
    
    This endpoint queues enrichment jobs (in production, would use task queue)
    For MVP, returns success message
    """
    try:
        patent_ids = request_body.patent_ids
        since = request_body.since
        limit = request_body.limit or 50
        weights = request_body.weights or {"base": 0.6, "market": 0.4}
        
        # In production, this would queue jobs to run market_signals_enricher
        # For MVP, we return a success message with parameters
        
        return {
            "status": "queued",
            "message": "Signal recomputation queued",
            "params": {
                "patent_ids": patent_ids,
                "since": since,
                "limit": limit,
                "weights": weights
            },
            "note": "Run: python jobs/market_signals_enricher.py --mode live --limit " + str(limit)
        }
    
    except Exception as e:
        logger.error(f"Failed to queue recomputation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue recomputation: {str(e)}"
        )


@router.get("/items/{patent_id}/score")
async def get_patent_score_breakdown(
    patent_id: str,
    user=Depends(require_admin_2fa)
):
    """
    Get detailed score breakdown for a patent
    Returns base score, market factor, adjusted score, and breakdown components
    """
    try:
        patent = await patentpulse_items.find_one({"patent_id": patent_id})
        
        if not patent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patent {patent_id} not found"
            )
        
        # Extract scores
        base_score = patent.get("commercial_score", 0.0)
        adjusted_score = patent.get("commercial_score_adj")
        breakdown = patent.get("commercial_breakdown", {})
        
        # Calculate delta
        delta = (adjusted_score - base_score) if adjusted_score is not None else 0.0
        
        return {
            "patent_id": patent_id,
            "base_score": base_score,
            "adjusted_score": adjusted_score,
            "delta": round(delta, 3),
            "market_factor": breakdown.get("market_factor"),
            "breakdown": breakdown,
            "market_last_refreshed_at": patent.get("market_last_refreshed_at").isoformat() if patent.get("market_last_refreshed_at") else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch score for {patent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch score: {str(e)}"
        )
