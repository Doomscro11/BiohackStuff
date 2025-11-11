"""
Partner Analytics Module (Phase IXf+)
Tracks and reports on partner share access events
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Literal
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# MongoDB connection (shared with main app)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'peptimancer_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


async def track_event(
    share_id: str,
    event: Literal["open", "download", "blocked", "expired", "revoked"],
    ip: str,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None,
    file_size_kb: Optional[int] = None,
    geo_country: Optional[str] = None,
    geo_city: Optional[str] = None
) -> str:
    """
    Track a partner share access event
    
    Args:
        share_id: Partner share ID
        event: Event type
        ip: Client IP address
        user_agent: Client user agent
        reason: Reason for blocked/expired/revoked events
        file_size_kb: File size for downloads
        geo_country: Geo country (optional)
        geo_city: Geo city (optional)
    
    Returns:
        Event ID
    """
    import uuid
    
    event_doc = {
        "event_id": str(uuid.uuid4()),
        "share_id": share_id,
        "event": event,
        "ts": datetime.now(timezone.utc),
        "ip": ip,
        "user_agent": user_agent,
        "geo_country": geo_country,
        "geo_city": geo_city,
        "reason": reason,
        "file_size_kb": file_size_kb
    }
    
    try:
        result = await db.partner_share_events.insert_one(event_doc)
        logger.info(f"Tracked event: share={share_id} event={event} ip={ip}")
        return event_doc["event_id"]
    except Exception as e:
        logger.error(f"Failed to track event: {e}")
        raise


async def get_share_analytics(share_id: str) -> Dict[str, Any]:
    """
    Get analytics for a specific share
    
    Args:
        share_id: Partner share ID
    
    Returns:
        Analytics data: {opens, downloads, blocked, last_access_at, top_ips, geo_breakdown}
    """
    pipeline = [
        {"$match": {"share_id": share_id}},
        {
            "$group": {
                "_id": "$event",
                "count": {"$sum": 1},
                "last_ts": {"$max": "$ts"}
            }
        }
    ]
    
    try:
        results = await db.partner_share_events.aggregate(pipeline).to_list(length=None)
        
        analytics = {
            "opens": 0,
            "downloads": 0,
            "blocked": 0,
            "expired": 0,
            "revoked": 0,
            "last_access_at": None
        }
        
        for result in results:
            event_type = result["_id"]
            count = result["count"]
            analytics[event_type] = count
            
            if analytics["last_access_at"] is None or result["last_ts"] > analytics["last_access_at"]:
                analytics["last_access_at"] = result["last_ts"]
        
        # Get top IPs
        ip_pipeline = [
            {"$match": {"share_id": share_id}},
            {
                "$group": {
                    "_id": "$ip",
                    "count": {"$sum": 1},
                    "events": {"$push": "$event"}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        top_ips = await db.partner_share_events.aggregate(ip_pipeline).to_list(length=None)
        analytics["top_ips"] = [
            {"ip": item["_id"], "count": item["count"], "events": item["events"]}
            for item in top_ips
        ]
        
        # Get geo breakdown
        geo_pipeline = [
            {"$match": {"share_id": share_id, "geo_country": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$geo_country",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        geo_results = await db.partner_share_events.aggregate(geo_pipeline).to_list(length=None)
        analytics["geo_breakdown"] = [
            {"country": item["_id"], "count": item["count"]}
            for item in geo_results
        ]
        
        return analytics
    
    except Exception as e:
        logger.error(f"Failed to get analytics for share {share_id}: {e}")
        raise


async def get_dashboard_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get dashboard metrics for Grafana/admin panel
    
    Args:
        start_date: Start date filter (default: 30 days ago)
        end_date: End date filter (default: now)
    
    Returns:
        Dashboard metrics
    """
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    
    try:
        # Get share state breakdown
        share_states_pipeline = [
            {
                "$group": {
                    "_id": "$state",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        share_states = await db.partner_shares.aggregate(share_states_pipeline).to_list(length=None)
        
        # Get event breakdown by day
        events_pipeline = [
            {"$match": {"ts": {"$gte": start_date, "$lte": end_date}}},
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$ts"}},
                        "event": "$event"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.date": 1}}
        ]
        
        events_by_day = await db.partner_share_events.aggregate(events_pipeline).to_list(length=None)
        
        # Get top partners by downloads
        top_partners_pipeline = [
            {"$match": {"ts": {"$gte": start_date, "$lte": end_date}, "event": "download"}},
            {
                "$lookup": {
                    "from": "partner_shares",
                    "localField": "share_id",
                    "foreignField": "share_id",
                    "as": "share"
                }
            },
            {"$unwind": "$share"},
            {
                "$group": {
                    "_id": "$share.recipient_email",
                    "downloads": {"$sum": 1},
                    "company": {"$first": "$share.company_or_project"}
                }
            },
            {"$sort": {"downloads": -1}},
            {"$limit": 10}
        ]
        
        top_partners = await db.partner_share_events.aggregate(top_partners_pipeline).to_list(length=None)
        
        # Get blocked events breakdown
        blocked_pipeline = [
            {"$match": {"ts": {"$gte": start_date, "$lte": end_date}, "event": "blocked"}},
            {
                "$group": {
                    "_id": "$reason",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        blocked_breakdown = await db.partner_share_events.aggregate(blocked_pipeline).to_list(length=None)
        
        # Get geo distribution
        geo_pipeline = [
            {"$match": {"ts": {"$gte": start_date, "$lte": end_date}, "geo_country": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$geo_country",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        
        geo_distribution = await db.partner_share_events.aggregate(geo_pipeline).to_list(length=None)
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "share_states": {item["_id"]: item["count"] for item in share_states},
            "events_by_day": [
                {
                    "date": item["_id"]["date"],
                    "event": item["_id"]["event"],
                    "count": item["count"]
                }
                for item in events_by_day
            ],
            "top_partners": [
                {
                    "email": item["_id"],
                    "company": item.get("company", "Unknown"),
                    "downloads": item["downloads"]
                }
                for item in top_partners
            ],
            "blocked_breakdown": [
                {"reason": item["_id"], "count": item["count"]}
                for item in blocked_breakdown
            ],
            "geo_distribution": [
                {"country": item["_id"], "count": item["count"]}
                for item in geo_distribution
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise


async def cleanup_old_events(days: int = 180) -> int:
    """
    Clean up events older than specified days
    
    Args:
        days: Age threshold in days
    
    Returns:
        Number of deleted events
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    try:
        result = await db.partner_share_events.delete_many({"ts": {"$lt": cutoff}})
        deleted_count = result.deleted_count
        logger.info(f"Cleaned up {deleted_count} old events (older than {days} days)")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to cleanup old events: {e}")
        raise
