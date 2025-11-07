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
    
    # Upload to cloud storage
    remote_meta = _upload_to_cloud(file_path)
    
    return {
        "ok": True,
        "file": file_path,
        "date": dt.isoformat(),
        "counts": export_data["counts"],
        "remote": remote_meta
    }

def _upload_to_cloud(path: str) -> dict:
    """
    Upload audit file to S3 or GCS based on configuration
    Returns metadata about the upload
    """
    provider = os.getenv("AUDIT_PROVIDER", "").lower()
    bucket = os.getenv("AUDIT_BUCKET")
    prefix = os.getenv("AUDIT_PREFIX", "peptimancer/audits")
    
    if provider == "s3" and bucket:
        try:
            import boto3
            s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
            key = f"{prefix}/{os.path.basename(path)}"
            
            s3.upload_file(
                path, 
                bucket, 
                key,
                ExtraArgs={"ServerSideEncryption": "AES256"}
            )
            
            logger.info(f"Uploaded audit to S3: s3://{bucket}/{key}")
            return {
                "provider": "s3",
                "uri": f"s3://{bucket}/{key}",
                "bucket": bucket,
                "key": key
            }
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            return {"provider": "local", "uri": path, "error": str(e)}
    
    elif provider == "gcs" and bucket:
        try:
            from google.cloud import storage
            client = storage.Client()
            b = client.bucket(bucket)
            key = f"{prefix}/{os.path.basename(path)}"
            blob = b.blob(key)
            blob.upload_from_filename(path)
            
            logger.info(f"Uploaded audit to GCS: gs://{bucket}/{key}")
            return {
                "provider": "gcs",
                "uri": f"gs://{bucket}/{key}",
                "bucket": bucket,
                "key": key
            }
        except Exception as e:
            logger.error(f"Failed to upload to GCS: {e}")
            return {"provider": "local", "uri": path, "error": str(e)}
    
    # No cloud provider configured - local only
    return {
        "provider": "local",
        "uri": path
    }

# CLI entry point
if __name__ == "__main__":
    import asyncio
    import sys
    
    day = sys.argv[1] if len(sys.argv) > 1 else None
    result = asyncio.run(export_day(day))
    print(json.dumps(result, indent=2))
