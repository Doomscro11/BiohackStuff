"""
Share Link Cleaner Job (Phase IXf+)
Nightly job to expire old shares and send reminders
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.partner_analytics import cleanup_old_events

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'peptimancer_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


async def expire_old_shares():
    """
    Mark shares as expired if past expiry date
    """
    now = datetime.now(timezone.utc)
    
    try:
        # Find active shares past expiry
        result = await db.partner_shares.update_many(
            {
                "state": "active",
                "policy.expires_at": {"$lt": now}
            },
            {
                "$set": {"state": "expired"}
            }
        )
        
        expired_count = result.modified_count
        logger.info(f"Expired {expired_count} shares")
        
        return expired_count
    
    except Exception as e:
        logger.error(f"Failed to expire shares: {e}")
        raise


async def send_expiry_reminders():
    """
    Send 3-day reminder emails for shares expiring soon
    
    Note: This requires an email sender implementation.
    For now, we'll just log the reminders.
    """
    now = datetime.now(timezone.utc)
    reminder_threshold = now + timedelta(days=3)
    
    try:
        # Find active shares expiring in 3 days
        shares = await db.partner_shares.find({
            "state": "active",
            "policy.expires_at": {
                "$gte": now,
                "$lte": reminder_threshold
            },
            "reminder_sent": {"$ne": True}
        }).to_list(length=None)
        
        reminder_count = 0
        
        for share in shares:
            # TODO: Send email using notifier abstraction
            # For now, just log and mark as reminded
            logger.info(
                f"REMINDER: Share {share['share_id']} for {share['recipient_email']} "
                f"expires on {share['policy']['expires_at']}"
            )
            
            # Mark reminder sent
            await db.partner_shares.update_one(
                {"share_id": share["share_id"]},
                {"$set": {"reminder_sent": True}}
            )
            
            reminder_count += 1
        
        logger.info(f"Sent {reminder_count} expiry reminders")
        return reminder_count
    
    except Exception as e:
        logger.error(f"Failed to send reminders: {e}")
        raise


async def cleanup_old_watermarked_files():
    """
    Clean up temporary watermarked PDF files older than 7 days
    """
    try:
        # Find exports directory
        exports_dir = Path("/app/backend/exports")
        if not exports_dir.exists():
            logger.info("Exports directory not found, skipping cleanup")
            return 0
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        deleted_count = 0
        
        # Find watermarked files
        for watermarked_file in exports_dir.glob("*_watermarked.pdf"):
            try:
                file_mtime = datetime.fromtimestamp(
                    watermarked_file.stat().st_mtime,
                    tz=timezone.utc
                )
                
                if file_mtime < cutoff:
                    watermarked_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old watermarked file: {watermarked_file.name}")
            
            except Exception as e:
                logger.error(f"Failed to delete {watermarked_file}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} old watermarked files")
        return deleted_count
    
    except Exception as e:
        logger.error(f"Failed to cleanup watermarked files: {e}")
        raise


async def run_cleanup():
    """
    Run all cleanup tasks
    """
    logger.info("=== Share Link Cleaner Job Started ===")
    
    start_time = datetime.now(timezone.utc)
    
    try:
        # Expire old shares
        expired_count = await expire_old_shares()
        
        # Send reminders
        reminder_count = await send_expiry_reminders()
        
        # Cleanup old events (180 days)
        deleted_events = await cleanup_old_events(days=180)
        
        # Cleanup old watermarked files
        deleted_files = await cleanup_old_watermarked_files()
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Log summary
        summary = {
            "expired_shares": expired_count,
            "reminders_sent": reminder_count,
            "deleted_events": deleted_events,
            "deleted_files": deleted_files,
            "duration_seconds": duration,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Store run metadata
        await db.partner_cleaner_runs.insert_one({
            "run_id": str(uuid.uuid4()),
            "started_at": start_time,
            "completed_at": datetime.now(timezone.utc),
            "summary": summary
        })
        
        logger.info(f"=== Cleanup Completed in {duration:.2f}s ===")
        logger.info(f"Summary: {summary}")
        
        return summary
    
    except Exception as e:
        logger.error(f"Cleanup job failed: {e}")
        raise
    
    finally:
        client.close()


if __name__ == "__main__":
    import uuid
    asyncio.run(run_cleanup())
