# Observability and Error Logging for Peptimancer
import os
import time
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("peptimancer")

# Phase 7.1: Initialize Sentry for error tracking (optional)
try:
    import sentry_sdk
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=0.1,
            environment=os.getenv("ENV", "production")
        )
        logger.info("Sentry error tracking initialized")
except ImportError:
    logger.debug("Sentry SDK not installed - skipping error tracking")

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

async def log_error(kind: str, props: dict):
    """
    Log error to MongoDB for tracking and monitoring
    
    Args:
        kind: Error type/category (e.g., "2fa_failed", "rate_limit_exceeded")
        props: Additional error properties and context
    """
    try:
        await db.errors.insert_one({
            "kind": kind,
            "props": props,
            "ts": time.time()
        })
    except Exception as e:
        logger.error(f"log_error failed: {e}")

async def get_error_stats():
    """
    Get error statistics for health monitoring
    """
    try:
        # Get last error
        last_err = await db.errors.find_one(sort=[("ts", -1)])
        
        # Count errors in last 24 hours
        cutoff_time = time.time() - 86400
        errors_24h = await db.errors.count_documents({"ts": {"$gt": cutoff_time}})
        
        return {
            "lastKind": last_err.get("kind") if last_err else None,
            "lastTs": last_err.get("ts") if last_err else None,
            "count24h": errors_24h
        }
    except Exception as e:
        logger.error(f"get_error_stats failed: {e}")
        return {
            "lastKind": None,
            "lastTs": None,
            "count24h": 0
        }
