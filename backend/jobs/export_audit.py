#!/usr/bin/env python3
"""
Nightly Audit Export Job
Exports audit trails to local file and optionally to S3/GCS
"""
import os
import json
import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

def json_serializer(obj):
    """Custom JSON serializer for MongoDB types"""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

async def export_day(day: str = None) -> dict:
    """
    Export audit trails for a specific day
    
    Args:
        day: Date in YYYY-MM-DD format, defaults to yesterday
    
    Returns:
        dict with ok status and file path
    """
    # Parse date
    if day:
        dt = datetime.date.fromisoformat(day)
    else:
        dt = datetime.date.today() - datetime.timedelta(days=1)
    
    start = datetime.datetime.combine(dt, datetime.time.min)
    end = datetime.datetime.combine(dt, datetime.time.max)
    
    logger.info(f"Exporting audit data for {dt.isoformat()}")
    
    # Query audit collections
    settings_history = await db._settings_history.find({
        "ts": {"$gte": start, "$lte": end}
    }).to_list(length=None)
    
    credits_ledger = await db.credits_ledger.find({
        "timestamp": {"$gte": start, "$lte": end}
    }).to_list(length=None)
    
    # Prepare export data
    export_data = {
        "date": dt.isoformat(),
        "exported_at": datetime.datetime.utcnow().isoformat(),
        "settings_history": settings_history,
        "credits_ledger": credits_ledger,
        "counts": {
            "settings_changes": len(settings_history),
            "credit_transactions": len(credits_ledger)
        }
    }
    
    # Write to local file
    export_dir = "/tmp/audits"
    os.makedirs(export_dir, exist_ok=True)
    
    file_path = f"{export_dir}/{dt.isoformat()}.json"
    with open(file_path, "w") as f:
        json.dump(export_data, f, default=json_serializer, indent=2)
    
    logger.info(f"Audit export complete: {file_path}")
    
    # TODO: Upload to S3/GCS when credentials are configured
    # Example:
    # if os.getenv("AWS_ACCESS_KEY_ID"):
    #     upload_to_s3(file_path, f"audits/{dt.isoformat()}.json")
    
    return {
        "ok": True,
        "file": file_path,
        "date": dt.isoformat(),
        "counts": export_data["counts"]
    }

# CLI entry point
if __name__ == "__main__":
    import asyncio
    import sys
    
    day = sys.argv[1] if len(sys.argv) > 1 else None
    result = asyncio.run(export_day(day))
    print(json.dumps(result, indent=2))
