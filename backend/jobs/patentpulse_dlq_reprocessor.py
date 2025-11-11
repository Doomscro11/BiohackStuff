#!/usr/bin/env python3
"""
PatentPulse DLQ Reprocessor (Phase IXc)
Retries failed items from Dead Letter Queue

Usage:
  python jobs/patentpulse_dlq_reprocessor.py --max-retries 3 --dry-run
  FEATURE_PATENTPULSE=true python jobs/patentpulse_dlq_reprocessor.py
"""

import os
import sys
import logging
import argparse
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs.patentpulse_normalizer import normalize_item, fix_trivial_violations
from models.patentpulse import DataQualityError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
patentpulse_items = db['patentpulse_items']
patentpulse_dlq = db['patentpulse_dlq']


class DLQReprocessor:
    """Reprocess failed items from DLQ"""
    
    def __init__(self, max_retries: int, dry_run: bool):
        self.max_retries = max_retries
        self.dry_run = dry_run
        
        # Counters
        self.processed = 0
        self.fixed = 0
        self.skipped = 0
        self.failed = 0
    
    async def reprocess_entry(self, entry: dict) -> bool:
        """
        Reprocess a single DLQ entry
        
        Returns:
            True if successfully fixed and upserted, False otherwise
        """
        patent_id = entry.get("patent_id") or "unknown"
        source = entry.get("source")
        payload = entry.get("payload", {})
        retries = entry.get("retries", 0)
        
        logger.info(f"\n{'='*40}")
        logger.info(f"Reprocessing: {patent_id} (retries: {retries})")
        logger.info(f"Reason: {entry.get('reason')}")
        
        # Check retry limit
        if retries >= self.max_retries:
            logger.warning(f"  ✗ Max retries reached ({self.max_retries}), skipping")
            self.skipped += 1
            return False
        
        try:
            # Try to fix trivial issues
            fixed_payload = fix_trivial_violations(payload)
            if not fixed_payload:
                raise DataQualityError("Could not fix violations")
            
            # Normalize
            normalized = normalize_item(source, fixed_payload)
            
            # Prepare for DB
            item_dict = normalized.model_dump()
            item_dict["source_hash"] = normalized.compute_source_hash()
            item_dict["first_ingested_at"] = datetime.now(timezone.utc)
            item_dict["last_ingested_at"] = datetime.now(timezone.utc)
            item_dict.pop("source_payload", None)
            
            # Upsert to items collection
            if not self.dry_run:
                await patentpulse_items.update_one(
                    {"patent_id": item_dict["patent_id"]},
                    {"$set": item_dict},
                    upsert=True
                )
                
                # Remove from DLQ
                await patentpulse_dlq.delete_one({"dlq_id": entry.get("dlq_id")})
            
            logger.info(f"  ✓ FIXED: {patent_id}")
            self.fixed += 1
            return True
        
        except Exception as e:
            logger.error(f"  ✗ FAILED: {patent_id} - {str(e)}")
            
            # Increment retry count
            if not self.dry_run:
                await patentpulse_dlq.update_one(
                    {"dlq_id": entry.get("dlq_id")},
                    {
                        "$set": {
                            "last_failed_at": datetime.now(timezone.utc),
                            "last_error": str(e)
                        },
                        "$inc": {"retries": 1}
                    }
                )
            
            self.failed += 1
            return False
    
    async def run(self):
        """Main reprocessing loop"""
        logger.info("\n" + "="*60)
        logger.info("PATENTPULSE DLQ REPROCESSOR")
        logger.info("="*60)
        logger.info(f"Max retries: {self.max_retries}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("="*60 + "\n")
        
        # Fetch all DLQ entries
        cursor = patentpulse_dlq.find({}).sort("first_failed_at", 1)
        entries = await cursor.to_list(length=None)
        
        logger.info(f"Found {len(entries)} entries in DLQ")
        
        if not entries:
            logger.info("No entries to reprocess")
            return
        
        # Process each entry
        for entry in entries:
            self.processed += 1
            await self.reprocess_entry(entry)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("REPROCESSING COMPLETE")
        logger.info("="*60)
        logger.info(f"Processed: {self.processed}")
        logger.info(f"Fixed: {self.fixed}")
        logger.info(f"Skipped: {self.skipped}")
        logger.info(f"Failed: {self.failed}")
        logger.info("="*60 + "\n")


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="PatentPulse DLQ Reprocessor")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Max retry attempts per item (default: 3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run mode (no DB writes)")
    
    args = parser.parse_args()
    
    # Run reprocessor
    reprocessor = DLQReprocessor(
        max_retries=args.max_retries,
        dry_run=args.dry_run
    )
    
    await reprocessor.run()
    
    # Close DB connection
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
