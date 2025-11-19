# PatentPulse Backend Routes - Patent Mining & Analysis API
import logging
import os
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from pydantic import BaseModel

from services import patentpulse_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/patentpulse", tags=["patentpulse"])

# Feature flag check
def check_feature_enabled():
    """Check if PatentPulse feature is enabled"""
    enabled = os.getenv("FEATURE_PATENTPULSE", "false").lower() == "true"
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PatentPulse feature is not enabled"
        )

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

class PatentItem(BaseModel):
    """Patent item response model"""
    title: str
    patent_id: str
    assignee: str
    country: str
    expiry_date: str
    status: str
    keywords: List[str]
    sequence_data: Optional[str] = None
    commercial_score: float
    synthesis_score: float
    fto_risk: float
    repurpose_notes: str
    created_at: str
    updated_at: str

@router.get("/items")
async def get_patent_items(
    status_filter: Optional[str] = Query(None, description="Filter by status: Expired, Lapsed, Expiring"),
    country: Optional[str] = Query(None, description="Filter by country"),
    min_commercial_score: Optional[float] = Query(None, description="Minimum commercial score (0-1)"),
    limit: int = Query(50, le=100, description="Max results"),
    skip: int = Query(0, description="Skip N results"),
    user=Depends(require_admin_2fa)
):
    """
    Get patent items with optional filters
    Returns patents ready for commercialization or revival
    """
    check_feature_enabled()
    
    try:
        result = await patentpulse_service.get_patent_items(
            status_filter=status_filter,
            country=country,
            min_commercial_score=min_commercial_score,
            limit=limit,
            skip=skip
        )
        return result
    except Exception as e:
        logger.error(f"PatentPulse items fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch patent items: {str(e)}"
        )

@router.get("/stats")
async def get_patent_stats(user=Depends(require_admin_2fa)):
    """
    Get PatentPulse statistics
    Returns counts by status, top assignees, average scores
    """
    check_feature_enabled()
    
    try:
        # Total patents
        total = await patentpulse_items.count_documents({})
        
        # By status
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        status_result = await patentpulse_items.aggregate(status_pipeline).to_list(None)
        by_status = {item["_id"]: item["count"] for item in status_result}
        
        # Top assignees
        assignee_pipeline = [
            {"$group": {"_id": "$assignee", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        assignee_result = await patentpulse_items.aggregate(assignee_pipeline).to_list(10)
        top_assignees = [{"assignee": item["_id"], "count": item["count"]} for item in assignee_result]
        
        # Average scores
        avg_pipeline = [
            {"$group": {
                "_id": None,
                "avg_commercial": {"$avg": "$commercial_score"},
                "avg_synthesis": {"$avg": "$synthesis_score"},
                "avg_fto_risk": {"$avg": "$fto_risk"}
            }}
        ]
        avg_result = await patentpulse_items.aggregate(avg_pipeline).to_list(1)
        avg_scores = avg_result[0] if avg_result else {
            "avg_commercial": 0,
            "avg_synthesis": 0,
            "avg_fto_risk": 0
        }
        
        # Expiring soon (next 24 months)
        cutoff = datetime.utcnow() + timedelta(days=730)
        expiring_soon = await patentpulse_items.count_documents({
            "status": {"$in": ["Active", "Expiring"]},
            "expiry_date": {"$lte": cutoff}
        })
        
        return {
            "total": total,
            "by_status": by_status,
            "top_assignees": top_assignees,
            "avg_commercial_score": round(avg_scores.get("avg_commercial", 0), 3),
            "avg_synthesis_score": round(avg_scores.get("avg_synthesis", 0), 3),
            "avg_fto_risk": round(avg_scores.get("avg_fto_risk", 0), 3),
            "expiring_soon_24mo": expiring_soon
        }
        
    except Exception as e:
        logger.error(f"PatentPulse stats fetch failed: {e}")
        return {
            "total": 0,
            "by_status": {},
            "top_assignees": [],
            "avg_commercial_score": 0,
            "avg_synthesis_score": 0,
            "avg_fto_risk": 0,
            "expiring_soon_24mo": 0
        }

@router.get("/top-opportunities")
async def get_top_opportunities(
    limit: int = Query(10, le=50, description="Max results"),
    user=Depends(require_admin_2fa)
):
    """
    Get top patent opportunities ranked by composite viability score
    Composite = commercial_score * (1 - synthesis_score) * (1 - fto_risk)
    """
    check_feature_enabled()
    
    try:
        # Calculate composite viability and sort
        pipeline = [
            {"$match": {"status": {"$in": ["Expired", "Lapsed", "Expiring"]}}},
            {"$addFields": {
                "viability_score": {
                    "$multiply": [
                        "$commercial_score",
                        {"$subtract": [1, "$synthesis_score"]},
                        {"$subtract": [1, "$fto_risk"]}
                    ]
                }
            }},
            {"$sort": {"viability_score": -1}},
            {"$limit": limit}
        ]
        
        result = await patentpulse_items.aggregate(pipeline).to_list(limit)
        
        # Convert dates to strings
        for item in result:
            item["_id"] = str(item["_id"])
            if isinstance(item.get("expiry_date"), datetime):
                item["expiry_date"] = item["expiry_date"].isoformat()
            if isinstance(item.get("created_at"), datetime):
                item["created_at"] = item["created_at"].isoformat()
            if isinstance(item.get("updated_at"), datetime):
                item["updated_at"] = item["updated_at"].isoformat()
            item["viability_score"] = round(item["viability_score"], 4)
        
        return {
            "opportunities": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"Top opportunities fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch opportunities: {str(e)}"
        )
