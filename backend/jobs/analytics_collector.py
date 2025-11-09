# Analytics Collector - Nightly Rollup Job
# Run via cron: 0 2 * * * python -m app.jobs.analytics_collector

import os
import logging
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

logging.basicConfig(level=logging.INFO)
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

async def collect_analytics():
    """
    Collect and aggregate analytics data for the previous day
    Writes one document to analytics_snapshots
    """
    # Calculate yesterday's date range (00:00 to 23:59)
    now = datetime.utcnow()
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_end = yesterday_start + timedelta(hours=23, minutes=59, seconds=59)
    
    logger.info(f"Collecting analytics for: {yesterday_start.date()}")
    
    try:
        # Total users
        users_total = await users.count_documents({})
        
        # Active users in last 24h
        users_active_24h = await users.count_documents({
            "lastLogin": {"$gte": yesterday_start, "$lte": yesterday_end}
        })
        
        # Analogues generated yesterday
        gen_pipeline_24h = [
            {"$match": {"ts": {"$gte": yesterday_start, "$lte": yesterday_end}}},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$numAnalogues"}
            }}
        ]
        gen_result_24h = await generation_logs.aggregate(gen_pipeline_24h).to_list(1)
        analogues_24h = gen_result_24h[0]["total"] if gen_result_24h else 0
        
        # Analogues generated in last 7 days
        week_ago = yesterday_start - timedelta(days=6)
        gen_pipeline_7d = [
            {"$match": {"ts": {"$gte": week_ago, "$lte": yesterday_end}}},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$numAnalogues"}
            }}
        ]
        gen_result_7d = await generation_logs.aggregate(gen_pipeline_7d).to_list(1)
        analogues_7d = gen_result_7d[0]["total"] if gen_result_7d else 0
        
        # Total analogues ever
        gen_pipeline_total = [
            {"$group": {
                "_id": None,
                "total": {"$sum": "$numAnalogues"}
            }}
        ]
        gen_result_total = await generation_logs.aggregate(gen_pipeline_total).to_list(1)
        analogues_total = gen_result_total[0]["total"] if gen_result_total else 0
        
        # Credits purchased yesterday
        purchased_pipeline = [
            {"$match": {
                "timestamp": {"$gte": yesterday_start, "$lte": yesterday_end},
                "delta": {"$gt": 0}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$delta"}}}
        ]
        purchased_result = await credits_ledger.aggregate(purchased_pipeline).to_list(1)
        credits_purchased_24h = purchased_result[0]["total"] if purchased_result else 0
        
        # Credits consumed yesterday
        consumed_pipeline = [
            {"$match": {
                "timestamp": {"$gte": yesterday_start, "$lte": yesterday_end},
                "delta": {"$lt": 0}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$delta"}}}
        ]
        consumed_result = await credits_ledger.aggregate(consumed_pipeline).to_list(1)
        credits_consumed_24h = abs(consumed_result[0]["total"]) if consumed_result else 0
        
        # Net flow
        net_flow_24h = credits_purchased_24h - credits_consumed_24h
        
        # Modification group mix yesterday
        mod_mix_pipeline = [
            {"$match": {
                "ts": {"$gte": yesterday_start, "$lte": yesterday_end},
                "status": "success"
            }},
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
        
        # Errors yesterday
        errors_24h = await errors.count_documents({
            "ts": {"$gte": yesterday_start, "$lte": yesterday_end}
        })
        
        # Latency p95 (if available)
        latency_pipeline = [
            {"$match": {
                "ts": {"$gte": yesterday_start, "$lte": yesterday_end},
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
        
        # Create snapshot document
        snapshot = {
            "snapshot_date": yesterday_start,
            "users_total": users_total,
            "users_active_24h": users_active_24h,
            "analogues_24h": analogues_24h,
            "analogues_7d": analogues_7d,
            "analogues_total": analogues_total,
            "credits_purchased_24h": credits_purchased_24h,
            "credits_consumed_24h": credits_consumed_24h,
            "net_flow_24h": net_flow_24h,
            "mod_group_mix_24h": mod_group_mix_24h,
            "errors_24h": errors_24h,
            "latency_p95_ms": latency_p95_ms,
            "created_at": now
        }
        
        # Insert snapshot
        result = await analytics_snapshots.insert_one(snapshot)
        logger.info(f"Analytics snapshot created: {result.inserted_id}")
        logger.info(f"  - Users active: {users_active_24h}")
        logger.info(f"  - Analogues: {analogues_24h}")
        logger.info(f"  - Credits flow: {net_flow_24h}")
        logger.info(f"  - Errors: {errors_24h}")
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Analytics collection failed: {e}")
        raise

async def main():
    """Main entry point"""
    logger.info("Starting analytics collector...")
    await collect_analytics()
    logger.info("Analytics collector finished")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
