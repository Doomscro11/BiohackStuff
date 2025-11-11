#!/usr/bin/env python3
"""
PatentPulse Production Collector (Phase IXc)
Idempotent, incremental, self-healing patent data ingestion pipeline

Usage:
  python jobs/patentpulse_collector.py --mode dry-run --since 2025-10-01T00:00:00Z
  FEATURE_PATENTPULSE=true python jobs/patentpulse_collector.py --mode live
"""

import os
import sys
import logging
import argparse
import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs.patentpulse_source_adapters import get_adapter
from jobs.patentpulse_normalizer import normalize_item, fix_trivial_violations
from models.patentpulse import RunMetadata, DLQEntry, DataQualityError

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
patentpulse_runs = db['patentpulse_runs']
patentpulse_dlq = db['patentpulse_dlq']


class PatentPulseCollector:
    """Production-grade patent collector with idempotency and incremental sync"""
    
    def __init__(self, mode: str, since: Optional[datetime], until: Optional[datetime],
                 limit: int, source_filter: List[str], verbose: bool):
        self.mode = mode
        self.since = since
        self.until = until or datetime.now(timezone.utc)
        self.limit = limit
        self.source_filter = source_filter
        self.verbose = verbose
        
        # Run metadata
        self.run = RunMetadata(
            mode=mode,
            sources=source_filter,
            params={
                "since": since.isoformat() if since else None,
                "until": self.until.isoformat(),
                "limit": limit
            }
        )
        
        # Timing for SLO
        self.item_times = []  # Individual item processing times (ms)
    
    async def get_last_successful_run(self) -> Optional[datetime]:
        """Get finished_at from last successful run for incremental sync"""
        last_run = await patentpulse_runs.find_one(
            {"status": "success"},
            sort=[("finished_at", -1)]
        )
        
        if last_run and last_run.get("finished_at"):
            return last_run["finished_at"]
        
        return None
    
    async def upsert_patent_item(self, normalized_item: Dict[str, Any]) -> str:
        """
        Idempotent upsert by patent_id
        
        Returns:
            "insert", "update", or "unchanged"
        """
        start_time = time.time()
        patent_id = normalized_item["patent_id"]
        source_hash = normalized_item["source_hash"]
        
        # Check if exists
        existing = await patentpulse_items.find_one({"patent_id": patent_id})
        
        if not existing:
            # Insert new
            normalized_item["first_ingested_at"] = datetime.now(timezone.utc)
            normalized_item["last_ingested_at"] = datetime.now(timezone.utc)
            
            if self.mode == "live":
                await patentpulse_items.insert_one(normalized_item)
            
            self.run.counts["upserts"] += 1
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.item_times.append(elapsed_ms)
            
            if self.verbose:
                logger.info(f"  ✓ INSERT: {patent_id} ({elapsed_ms:.0f}ms)")
            
            return "insert"
        
        # Check if content changed via source_hash
        if existing.get("source_hash") != source_hash:
            # Update existing
            update_doc = {
                **normalized_item,
                "first_ingested_at": existing["first_ingested_at"],  # Preserve original
                "last_ingested_at": datetime.now(timezone.utc)
            }
            
            if self.mode == "live":
                await patentpulse_items.replace_one({"patent_id": patent_id}, update_doc)
            
            self.run.counts["updates"] += 1
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.item_times.append(elapsed_ms)
            
            if self.verbose:
                logger.info(f"  ✓ UPDATE: {patent_id} ({elapsed_ms:.0f}ms)")
            
            return "update"
        
        # Unchanged
        self.run.counts["unchanged"] += 1
        
        elapsed_ms = (time.time() - start_time) * 1000
        self.item_times.append(elapsed_ms)
        
        if self.verbose:
            logger.debug(f"  - SKIP: {patent_id} (unchanged)")
        
        return "unchanged"
    
    async def add_to_dlq(self, source: str, raw: Dict[str, Any], reason: str, error: str):
        """Add failed item to Dead Letter Queue"""
        patent_id = raw.get("patent_number") or raw.get("application_id") or raw.get("lens_id")
        
        dlq_entry = DLQEntry(
            patent_id=patent_id,
            source=source,
            payload=raw,
            reason=reason,
            last_error=error
        )
        
        if self.mode == "live":
            await patentpulse_dlq.insert_one(dlq_entry.model_dump())
        
        self.run.counts["dlq"] += 1
        logger.warning(f"  ✗ DLQ: {patent_id or 'unknown'} - {reason}")
    
    async def collect_from_source(self, source: str):
        """Collect patents from a single source with pagination"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Collecting from {source}...")
        logger.info(f"{'='*60}")
        
        try:
            adapter = get_adapter(source)
            page_token = None
            page_num = 1
            
            while True:
                logger.info(f"\n📄 Page {page_num} for {source}...")
                
                # Fetch page
                result = await adapter.fetch_changed(
                    since=self.since,
                    until=self.until,
                    page_token=page_token
                )
                
                items = result.get("items", [])
                page_token = result.get("next_token")
                
                logger.info(f"  Fetched {len(items)} items")
                self.run.counts["fetched"] += len(items)
                
                # Process each item
                for raw in items:
                    # Check limit
                    if self.run.counts["normalized"] >= self.limit:
                        logger.info(f"  Limit reached ({self.limit})")
                        return
                    
                    try:
                        # Normalize
                        normalized = normalize_item(source, raw)
                        self.run.counts["normalized"] += 1
                        
                        # Prepare for DB
                        item_dict = normalized.model_dump()
                        item_dict["source_hash"] = normalized.compute_source_hash()
                        
                        # Convert datetime to UTC
                        for key in ["expiry_date", "last_seen_at"]:
                            if key in item_dict and item_dict[key]:
                                item_dict[key] = item_dict[key].replace(tzinfo=timezone.utc)
                        
                        # Remove source_payload (too large for DB)
                        item_dict.pop("source_payload", None)
                        
                        # Upsert
                        await self.upsert_patent_item(item_dict)
                    
                    except DataQualityError as e:
                        # Try to fix trivial issues
                        fixed = fix_trivial_violations(raw)
                        if fixed:
                            try:
                                normalized = normalize_item(source, fixed)
                                item_dict = normalized.model_dump()
                                item_dict["source_hash"] = normalized.compute_source_hash()
                                item_dict.pop("source_payload", None)
                                await self.upsert_patent_item(item_dict)
                                continue
                            except:
                                pass
                        
                        # Can't fix, send to DLQ
                        await self.add_to_dlq(source, raw, "data_quality_violation", str(e))
                        self.run.counts["rejected"] += 1
                    
                    except Exception as e:
                        logger.error(f"  Unexpected error processing item: {e}")
                        await self.add_to_dlq(source, raw, "processing_error", str(e))
                        self.run.errors.append({
                            "stage": "normalize",
                            "source": source,
                            "message": str(e)
                        })
                
                # Check for next page
                if not page_token:
                    break
                
                page_num += 1
                
                # Respect pagination limit
                if page_num > 10:  # Max 10 pages per source
                    logger.warning(f"  Max pages reached for {source}")
                    break
        
        except Exception as e:
            logger.error(f"Source collection failed for {source}: {e}")
            self.run.errors.append({
                "stage": "source_fetch",
                "source": source,
                "message": str(e)
            })
    
    async def calculate_slo(self):
        """Calculate SLO metrics: p95 latency and error rate"""
        if not self.item_times:
            return
        
        # P95 latency
        sorted_times = sorted(self.item_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_ms = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        
        # Error rate
        total_attempts = self.run.counts["normalized"] + self.run.counts["rejected"]
        error_rate = self.run.counts["rejected"] / total_attempts if total_attempts > 0 else 0
        
        # DQ reject rate
        dq_reject_rate = self.run.counts["dlq"] / self.run.counts["fetched"] if self.run.counts["fetched"] > 0 else 0
        
        self.run.slo = {
            "p95_ms": int(p95_ms),
            "error_rate": round(error_rate, 4),
            "dq_reject_rate": round(dq_reject_rate, 4)
        }
        
        # Check SLO gates
        slo_pass = (
            p95_ms <= 900 and
            error_rate <= 0.02 and
            dq_reject_rate <= 0.05 and
            self.run.counts["duplicates"] == 0
        )
        
        if not slo_pass:
            logger.warning("⚠️  SLO VIOLATION detected!")
            if p95_ms > 900:
                logger.warning(f"  - p95 latency: {p95_ms:.0f}ms > 900ms")
            if error_rate > 0.02:
                logger.warning(f"  - Error rate: {error_rate:.2%} > 2%")
            if dq_reject_rate > 0.05:
                logger.warning(f"  - DQ reject rate: {dq_reject_rate:.2%} > 5%")
    
    async def run_collection(self):
        """Main collection orchestration"""
        logger.info("\n" + "="*60)
        logger.info("PATENTPULSE PRODUCTION COLLECTOR")
        logger.info("="*60)
        logger.info(f"Mode: {self.mode}")
        logger.info(f"Sources: {', '.join(self.source_filter)}")
        logger.info(f"Since: {self.since}")
        logger.info(f"Until: {self.until}")
        logger.info(f"Limit: {self.limit}")
        logger.info("="*60 + "\n")
        
        # Feature flag check for live mode
        if self.mode == "live":
            enabled = os.getenv("FEATURE_PATENTPULSE", "false").lower() == "true"
            if not enabled:
                logger.error("❌ FEATURE_PATENTPULSE=true required for live mode")
                self.run.status = "failed"
                self.run.notes = "Feature flag not enabled"
                return
        
        # Save run metadata (running)
        if self.mode == "live":
            await patentpulse_runs.insert_one(self.run.model_dump())
        
        # Collect from each source
        for source in self.source_filter:
            await self.collect_from_source(source)
        
        # Finalize
        self.run.finished_at = datetime.now(timezone.utc)
        await self.calculate_slo()
        
        # Determine status
        if self.run.errors:
            self.run.status = "partial" if self.run.counts["upserts"] > 0 else "failed"
        else:
            self.run.status = "success"
        
        # Update run metadata
        if self.mode == "live":
            await patentpulse_runs.update_one(
                {"run_id": self.run.run_id},
                {"$set": self.run.model_dump()}
            )
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("COLLECTION COMPLETE")
        logger.info("="*60)
        logger.info(f"Run ID: {self.run.run_id}")
        logger.info(f"Status: {self.run.status}")
        logger.info(f"Duration: {(self.run.finished_at - self.run.started_at).total_seconds():.1f}s")
        logger.info("\nCounts:")
        for key, value in self.run.counts.items():
            logger.info(f"  {key}: {value}")
        logger.info("\nSLO Metrics:")
        for key, value in self.run.slo.items():
            logger.info(f"  {key}: {value}")
        if self.run.errors:
            logger.info(f"\nErrors: {len(self.run.errors)}")
            for err in self.run.errors[:5]:  # Show first 5
                logger.info(f"  - {err['stage']}: {err['message']}")
        logger.info("="*60 + "\n")


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="PatentPulse Production Collector")
    parser.add_argument("--mode", choices=["dry-run", "live"], default="dry-run",
                        help="Collection mode (default: dry-run)")
    parser.add_argument("--since", type=str, help="Start datetime (ISO format)")
    parser.add_argument("--until", type=str, help="End datetime (ISO format)")
    parser.add_argument("--limit", type=int, default=500, help="Max items to collect")
    parser.add_argument("--source", type=str, default="all",
                        choices=["uspto", "wipo", "lens", "all"],
                        help="Source filter")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Parse dates
    if args.since:
        since = datetime.fromisoformat(args.since.replace('Z', '+00:00'))
    else:
        # Get last successful run or default to 7 days ago
        collector_temp = PatentPulseCollector("dry-run", None, None, 1, [], False)
        last_run = await collector_temp.get_last_successful_run()
        since = last_run or (datetime.now(timezone.utc) - timedelta(days=7))
        logger.info(f"Using since from last successful run: {since}")
    
    until = None
    if args.until:
        until = datetime.fromisoformat(args.until.replace('Z', '+00:00'))
    
    # Parse sources
    if args.source == "all":
        sources = ["USPTO", "WIPO", "LENS"]
    else:
        sources = [args.source.upper()]
    
    # Run collector
    collector = PatentPulseCollector(
        mode=args.mode,
        since=since,
        until=until,
        limit=args.limit,
        source_filter=sources,
        verbose=args.verbose
    )
    
    await collector.run_collection()
    
    # Close DB connection
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
