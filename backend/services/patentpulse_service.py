"""
PatentPulse Service
Handles patent data queries and operations
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'peptimancer_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


def _serialize_dates(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime objects to ISO strings"""
    if item.get("_id"):
        item["_id"] = str(item["_id"])
    
    date_fields = ["expiry_date", "created_at", "updated_at", "priority_date"]
    for field in date_fields:
        if isinstance(item.get(field), datetime):
            item[field] = item[field].isoformat()
    
    return item


async def get_patent_items(
    status_filter: Optional[str] = None,
    country: Optional[str] = None,
    min_commercial_score: Optional[float] = None,
    limit: int = 50,
    skip: int = 0
) -> Dict[str, Any]:
    """
    Get patent items with optional filters and pagination
    
    Returns:
        Dict with 'items', 'count', 'total', 'skip', 'limit'
    """
    query = {}
    
    if status_filter:
        query['status'] = status_filter
    
    if country:
        query['country'] = country
    
    if min_commercial_score is not None:
        query['commercial_score'] = {'$gte': min_commercial_score}
    
    # Execute query with pagination
    cursor = db.patentpulse_items.find(query).sort('commercial_score', -1).skip(skip).limit(limit)
    items = await cursor.to_list(limit)
    
    # Serialize dates
    items = [_serialize_dates(item) for item in items]
    
    # Get total count
    total = await db.patentpulse_items.count_documents(query)
    
    logger.info(f"Retrieved {len(items)} patent items (total: {total})")
    
    return {
        'items': items,
        'count': len(items),
        'total': total,
        'skip': skip,
        'limit': limit
    }


async def get_patent_by_id(patent_id: str) -> Optional[Dict[str, Any]]:
    """Get patent by ID"""
    patent = await db.patentpulse_items.find_one({'patent_id': patent_id}, {'_id': 0})
    return patent


async def get_patent_stats() -> Dict[str, Any]:
    """
    Get patent statistics
    
    Returns:
        Dict with total, by_status, top_assignees, average scores, expiring_soon count
    """
    try:
        # Total patents
        total = await db.patentpulse_items.count_documents({})
        
        # By status
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        status_result = await db.patentpulse_items.aggregate(status_pipeline).to_list(None)
        by_status = {item["_id"]: item["count"] for item in status_result}
        
        # Top assignees
        assignee_pipeline = [
            {"$group": {"_id": "$assignee", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        assignee_result = await db.patentpulse_items.aggregate(assignee_pipeline).to_list(10)
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
        avg_result = await db.patentpulse_items.aggregate(avg_pipeline).to_list(1)
        avg_scores = avg_result[0] if avg_result else {
            "avg_commercial": 0,
            "avg_synthesis": 0,
            "avg_fto_risk": 0
        }
        
        # Expiring soon (next 24 months)
        cutoff = datetime.now(timezone.utc) + timedelta(days=730)
        expiring_soon = await db.patentpulse_items.count_documents({
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


async def get_top_opportunities(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get top patent opportunities sorted by viability score
    """
    cursor = db.patentpulse_items.find(
        {'viability_score': {'$exists': True}},
        {'_id': 0}
    ).sort('viability_score', -1).limit(limit)
    
    opportunities = await cursor.to_list(length=limit)
    
    logger.info(f"Retrieved {len(opportunities)} top opportunities")
    
    return opportunities


async def update_patent_status(patent_id: str, status: str) -> bool:
    """
    Update patent status
    
    Returns:
        True if updated, False if not found
    """
    result = await db.patentpulse_items.update_one(
        {'patent_id': patent_id},
        {
            '$set': {
                'status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.modified_count > 0:
        logger.info(f"Updated patent {patent_id} status to {status}")
        return True
    
    return False


async def search_patents(
    query_text: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search patents by text
    
    Note: Requires text index on title and abstract fields
    """
    cursor = db.patentpulse_items.find(
        {'$text': {'$search': query_text}},
        {'_id': 0, 'score': {'$meta': 'textScore'}}
    ).sort([('score', {'$meta': 'textScore'})]).limit(limit)
    
    results = await cursor.to_list(length=limit)
    
    logger.info(f"Found {len(results)} patents matching '{query_text}'")
    
    return results
