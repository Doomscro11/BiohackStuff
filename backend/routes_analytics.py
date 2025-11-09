# Admin Analytics Routes for Peptimancer
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
users = db['users']
generation_logs = db['generation_logs']
credits_ledger = db['credits_ledger']
errors = db['errors']
analytics_snapshots = db['analytics_snapshots']

router = APIRouter(prefix="/api/admin/analytics", tags=["admin_analytics"])

def require_admin_2fa(request: Request):
    """Require admin with 2FA"""
    from middleware.auth import require_admin
    
    user = require_admin(request)
    
    # Check admin2fa
    if not getattr(request.state, 'admin2fa', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin 2FA required"
        )
    
    return user

@router.get("/live")
async def get_live_analytics(user=Depends(require_admin_2fa)):
    """
    Get live 24h analytics aggregates
    No PII - only counts and aggregates
    """
    try:
        # Calculate 24h ago timestamp
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)
        
        # Active users in last 24h (based on lastLogin)
        users_active_24h = await users.count_documents({
            "lastLogin": {"$gte": yesterday}
        })
        
        # Analogues generated in last 24h
        gen_pipeline = [
            {"$match": {"ts": {"$gte": yesterday}}},
            {"$group": {
                "_id": None,
                "total_analogues": {"$sum": "$numAnalogues"},
                "total_requests": {"$sum": 1}
            }}
        ]
        gen_result = await generation_logs.aggregate(gen_pipeline).to_list(1)
        analogues_24h = gen_result[0]["total_analogues"] if gen_result else 0
        
        # Credits purchased in last 24h
        purchased_pipeline = [
            {"$match": {
                "timestamp": {"$gte": yesterday},
                "delta": {"$gt": 0}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$delta"}}}
        ]
        purchased_result = await credits_ledger.aggregate(purchased_pipeline).to_list(1)
        credits_purchased_24h = purchased_result[0]["total"] if purchased_result else 0
        
        # Credits consumed in last 24h
        consumed_pipeline = [
            {"$match": {
                "timestamp": {"$gte": yesterday},
                "delta": {"$lt": 0}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$delta"}}}
        ]
        consumed_result = await credits_ledger.aggregate(consumed_pipeline).to_list(1)
        credits_consumed_24h = abs(consumed_result[0]["total"]) if consumed_result else 0
        
        # Net flow
        net_flow_24h = credits_purchased_24h - credits_consumed_24h
        
        # Errors in last 24h
        errors_24h = await errors.count_documents({
            "ts": {"$gte": yesterday}
        })
        
        # Modification group mix in last 24h
        mod_mix_pipeline = [
            {"$match": {"ts": {"$gte": yesterday}, "status": "success"}},
            {"$project": {
                "mods_array": {"$objectToArray": "$mods"}
            }},
            {"$unwind": "$mods_array"},
            {"$match": {"mods_array.v": {"$gt": 0}}},
            {"$group": {
                "_id": "$mods_array.k",
                "count": {"$sum": "$mods_array.v"}
            }}
        ]
        mod_mix_result = await generation_logs.aggregate(mod_mix_pipeline).to_list(None)
        mod_group_mix_24h = {item["_id"]: item["count"] for item in mod_mix_result}
        
        # Latency p95 (if available)
        latency_pipeline = [
            {"$match": {
                "ts": {"$gte": yesterday},
                "status": "success",
                "latencyMs": {"$exists": True}
            }},
            {"$group": {
                "_id": None,
                "latencies": {"$push": "$latencyMs"}
            }},
            {"$project": {
                "p95": {
                    "$let": {
                        "vars": {
                            "sorted": {"$sortArray": {"input": "$latencies", "sortBy": 1}},
                            "count": {"$size": "$latencies"}
                        },
                        "in": {
                            "$arrayElemAt": [
                                "$$sorted",
                                {"$floor": {"$multiply": [0.95, "$$count"]}}
                            ]
                        }
                    }
                }
            }}
        ]
        latency_result = await generation_logs.aggregate(latency_pipeline).to_list(1)
        latency_p95_ms = latency_result[0]["p95"] if latency_result else None
        
        return {
            "users_active_24h": users_active_24h,
            "analogues_24h": analogues_24h,
            "credits_purchased_24h": credits_purchased_24h,
            "credits_consumed_24h": credits_consumed_24h,
            "net_flow_24h": net_flow_24h,
            "errors_24h": errors_24h,
            "latency_p95_ms": latency_p95_ms,
            "mod_group_mix_24h": mod_group_mix_24h
        }
        
    except Exception as e:
        logger.error(f"Live analytics fetch failed: {e}")
        # Return zeroed payload so dashboard still renders
        return {
            "users_active_24h": 0,
            "analogues_24h": 0,
            "credits_purchased_24h": 0,
            "credits_consumed_24h": 0,
            "net_flow_24h": 0,
            "errors_24h": 0,
            "latency_p95_ms": None,
            "mod_group_mix_24h": {}
        }

@router.get("/snapshots")
async def get_snapshots(days: int = 30, user=Depends(require_admin_2fa)):
    """
    Get historical analytics snapshots
    Returns last N days of rollup data for trend charts
    """
    try:
        # Fetch last N snapshots ordered by date descending
        cursor = analytics_snapshots.find().sort("snapshot_date", -1).limit(days)
        snapshots = await cursor.to_list(days)
        
        # Convert ObjectIds and dates to strings
        for snap in snapshots:
            snap["_id"] = str(snap["_id"])
            if isinstance(snap.get("snapshot_date"), datetime):
                snap["snapshot_date"] = snap["snapshot_date"].isoformat()
        
        return {
            "snapshots": snapshots,
            "count": len(snapshots)
        }
        
    except Exception as e:
        logger.error(f"Snapshots fetch failed: {e}")
        return {
            "snapshots": [],
            "count": 0
        }
