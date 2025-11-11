#!/usr/bin/env python3
"""
Market Signals Enricher (Phase IXd)
Enriches patent items with market intelligence to adjust commercial scores

Usage:
  python jobs/market_signals_enricher.py --mode dry-run --limit 50
  FEATURE_PATENTPULSE_SIGNALS=true python jobs/market_signals_enricher.py --mode live
"""

import os
import sys
import logging
import argparse
import asyncio
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs.market_signals_adapters import get_signal_adapter
from models.patentpulse import MarketSignalFeatures, MarketSignalProvenance, PatentMarketSignal

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
patentpulse_signals = db['patentpulse_signals']


class MarketSignalsEnricher:
    """Enrich patents with market signals and adjust commercial scores"""
    
    def __init__(self, mode: str, since: Optional[datetime], limit: int,
                 source_filter: Optional[List[str]], weights: Dict[str, float]):
        self.mode = mode
        self.since = since
        self.limit = limit
        self.source_filter = source_filter
        self.weights = weights
        
        # Counters
        self.processed = 0
        self.enriched = 0
        self.cached = 0
        self.failed = 0
        self.clamped = 0
    
    def normalize_keyword_key(self, keywords: List[str]) -> str:
        """Generate normalized keyword key for fallback queries"""
        if not keywords:
            return "peptide_biotech"
        
        # Take top 3 keywords, normalize
        top_keywords = keywords[:3]
        normalized = [kw.lower().strip() for kw in top_keywords]
        return "_".join(sorted(normalized))
    
    async def get_cached_signals(self, patent_id: str, keyword_key: str) -> Optional[Dict[str, Any]]:
        """Check if fresh signals exist in cache (TTL 24h)"""
        # Try patent_id first
        cached = await patentpulse_signals.find_one({
            "patent_id": patent_id,
            "ttl_expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if cached:
            return cached
        
        # Fallback to keyword_key
        cached = await patentpulse_signals.find_one({
            "keyword_key": keyword_key,
            "ttl_expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        return cached
    
    async def fetch_market_signals(self, query: str) -> Dict[str, Any]:
        """Fan-out to all signal adapters and merge results"""
        results = {}
        provenance = []
        
        try:
            # Vendor catalog
            vendor_adapter = get_signal_adapter("vendor")
            vendor_data = await vendor_adapter.fetch(query)
            
            if vendor_data.get("available"):
                results["avg_price"] = vendor_data.get("avg_price")
                results["price_dispersion"] = vendor_data.get("price_dispersion")
                results["availability_score"] = min(1.0, vendor_data.get("in_stock_count", 0) / max(vendor_data.get("vendor_count", 1), 1))
                provenance.append({
                    "source": "VendorCatalogAdapter",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "meta": {"vendor_count": vendor_data.get("vendor_count")}
                })
        except Exception as e:
            logger.warning(f"Vendor adapter failed: {e}")
        
        try:
            # Search trends
            search_adapter = get_signal_adapter("search")
            search_data = await search_adapter.fetch(query)
            
            if search_data.get("search_index") is not None:
                results["search_index"] = search_data["search_index"] / 100.0  # Normalize to 0-1
                provenance.append({
                    "source": "SearchTrendAdapter",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "meta": {"trend": search_data.get("trend")}
                })
        except Exception as e:
            logger.warning(f"Search adapter failed: {e}")
        
        try:
            # Social chatter
            social_adapter = get_signal_adapter("social")
            social_data = await social_adapter.fetch(query)
            
            results["social_sentiment"] = social_data.get("sentiment", 0.0)
            results["social_volume"] = social_data.get("volume", 0)
            provenance.append({
                "source": "SocialChatterAdapter",
                "ts": datetime.now(timezone.utc).isoformat(),
                "meta": {"volume": social_data.get("volume")}
            })
        except Exception as e:
            logger.warning(f"Social adapter failed: {e}")
        
        try:
            # Marketplace
            marketplace_adapter = get_signal_adapter("marketplace")
            marketplace_data = await marketplace_adapter.fetch(query)
            
            if marketplace_data.get("active"):
                results["market_velocity"] = marketplace_data.get("velocity_score", 0.0)
                provenance.append({
                    "source": "MarketplaceAdapter",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "meta": {"transaction_count": marketplace_data.get("transaction_count")}
                })
        except Exception as e:
            logger.warning(f"Marketplace adapter failed: {e}")
        
        return {"features": results, "provenance": provenance}
    
    def calculate_market_factor(self, features: Dict[str, Any]) -> float:
        """
        Calculate market factor from signal features
        Formula: 0.35*search + 0.25*availability + 0.20*(1-dispersion) + 0.20*sentiment
        """
        search_index = features.get("search_index", 0.5)  # Default neutral
        availability = features.get("availability_score", 0.5)
        dispersion = features.get("price_dispersion", 0.5)
        sentiment = features.get("social_sentiment", 0.0)
        
        # Normalize dispersion (lower is better)
        dispersion_norm = 1.0 - self._sigmoid(dispersion)
        
        # Only use positive sentiment
        sentiment_contrib = max(sentiment, 0)
        
        # Weighted combination
        market_factor = (
            0.35 * search_index +
            0.25 * availability +
            0.20 * dispersion_norm +
            0.20 * sentiment_contrib
        )
        
        return max(0.0, min(1.0, market_factor))
    
    def _sigmoid(self, x: float) -> float:
        """Sigmoid normalization for dispersion"""
        try:
            return 1 / (1 + math.exp(-x))
        except:
            return 0.5
    
    def calculate_adjusted_score(self, base_score: float, market_factor: float,
                                   weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate adjusted commercial score
        Returns dict with adjusted score, delta, and clamp flag
        """
        base_w = weights.get("base", 0.6)
        market_w = weights.get("market", 0.4)
        
        # Calculate raw adjusted score
        raw_adjusted = base_w * base_score + market_w * market_factor
        
        # Floor clamp: prevent reduction > 0.25
        floor = base_score - 0.25
        adjusted = max(raw_adjusted, floor)
        
        # Ceiling clamp to [0, 1]
        adjusted = max(0.0, min(1.0, adjusted))
        
        delta = adjusted - base_score
        clamped = (adjusted > raw_adjusted)  # Was floor clamp applied?
        
        return {
            "base_score": base_score,
            "market_factor": market_factor,
            "adjusted_score": round(adjusted, 3),
            "delta": round(delta, 3),
            "clamped": clamped,
            "weights": weights
        }
    
    async def enrich_patent(self, patent: Dict[str, Any]) -> bool:
        """Enrich a single patent with market signals"""
        patent_id = patent["patent_id"]
        logger.info(f"\nEnriching: {patent_id}")
        
        try:
            # Generate query keys
            keyword_key = self.normalize_keyword_key(patent.get("keywords", []))
            query = patent_id  # Try patent_id first, fallback to keywords
            
            # Check cache
            cached_signals = await self.get_cached_signals(patent_id, keyword_key)
            
            if cached_signals:
                logger.info(f"  ✓ Using cached signals")
                features = cached_signals.get("features", {})
                provenance = cached_signals.get("provenance", [])
                self.cached += 1
            else:
                # Fetch fresh signals
                logger.info(f"  → Fetching fresh signals...")
                signal_data = await self.fetch_market_signals(query)
                features = signal_data["features"]
                provenance = signal_data["provenance"]
                
                # Cache signals (TTL 24h)
                signal_doc = PatentMarketSignal(
                    patent_id=patent_id,
                    keyword_key=keyword_key,
                    features=MarketSignalFeatures(**features),
                    provenance=[MarketSignalProvenance(**p) for p in provenance],
                    ttl_expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                
                if self.mode == "live":
                    await patentpulse_signals.update_one(
                        {"patent_id": patent_id},
                        {"$set": signal_doc.dict()},
                        upsert=True
                    )
            
            # Calculate market factor
            market_factor = self.calculate_market_factor(features)
            logger.info(f"  Market factor: {market_factor:.3f}")
            
            # Calculate adjusted score
            base_score = patent["commercial_score"]
            adjustment = self.calculate_adjusted_score(base_score, market_factor, self.weights)
            
            logger.info(f"  Base: {base_score:.3f} → Adjusted: {adjustment['adjusted_score']:.3f} (Δ {adjustment['delta']:+.3f})")
            
            if adjustment["clamped"]:
                logger.warning(f"  ⚠️  Floor clamp applied (prevented drop > 0.25)")
                self.clamped += 1
            
            # Update patent item
            commercial_breakdown = {
                "base": base_score,
                "market_factor": market_factor,
                "weights": self.weights,
                "inputs": features
            }
            
            if self.mode == "live":
                await patentpulse_items.update_one(
                    {"patent_id": patent_id},
                    {"$set": {
                        "commercial_score_adj": adjustment["adjusted_score"],
                        "commercial_breakdown": commercial_breakdown,
                        "market_last_refreshed_at": datetime.now(timezone.utc)
                    }}
                )
            
            self.enriched += 1
            return True
        
        except Exception as e:
            logger.error(f"  ✗ Enrichment failed for {patent_id}: {e}")
            self.failed += 1
            return False
    
    async def run(self):
        """Main enrichment orchestration"""
        logger.info("\n" + "="*60)
        logger.info("MARKET SIGNALS ENRICHER")
        logger.info("="*60)
        logger.info(f"Mode: {self.mode}")
        logger.info(f"Limit: {self.limit}")
        logger.info(f"Weights: base={self.weights['base']}, market={self.weights['market']}")
        logger.info("="*60 + "\n")
        
        # Feature flag check for live mode
        if self.mode == "live":
            enabled = os.getenv("FEATURE_PATENTPULSE_SIGNALS", "false").lower() == "true"
            if not enabled:
                logger.error("❌ FEATURE_PATENTPULSE_SIGNALS=true required for live mode")
                return
        
        # Build candidate query
        query = {}
        
        if self.since:
            # Items ingested/updated since
            query["$or"] = [
                {"last_ingested_at": {"$gte": self.since}},
                {"market_last_refreshed_at": {"$lt": datetime.now(timezone.utc) - timedelta(hours=24)}}
            ]
        else:
            # Items never enriched or stale (>24h)
            query["$or"] = [
                {"market_last_refreshed_at": {"$exists": False}},
                {"market_last_refreshed_at": {"$lt": datetime.now(timezone.utc) - timedelta(hours=24)}}
            ]
        
        if self.source_filter:
            query["source"] = {"$in": self.source_filter}
        
        # Fetch candidates
        cursor = patentpulse_items.find(query).sort("commercial_score", -1).limit(self.limit)
        candidates = await cursor.to_list(self.limit)
        
        logger.info(f"Found {len(candidates)} candidates for enrichment\n")
        
        if not candidates:
            logger.info("No patents to enrich")
            return
        
        # Enrich each patent
        for patent in candidates:
            self.processed += 1
            await self.enrich_patent(patent)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("ENRICHMENT COMPLETE")
        logger.info("="*60)
        logger.info(f"Processed: {self.processed}")
        logger.info(f"Enriched: {self.enriched}")
        logger.info(f"Cached: {self.cached}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Clamped: {self.clamped}")
        logger.info("="*60 + "\n")


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Market Signals Enricher")
    parser.add_argument("--mode", choices=["dry-run", "live"], default="dry-run",
                        help="Enrichment mode (default: dry-run)")
    parser.add_argument("--since", type=str, help="Only enrich items changed since (ISO format)")
    parser.add_argument("--limit", type=int, default=200, help="Max items to enrich")
    parser.add_argument("--source-filter", type=str,
                        help="Comma-separated source filter (uspto,wipo,lens)")
    parser.add_argument("--weights", type=str, default="base:0.6,market:0.4",
                        help="Score weights as base:X,market:Y")
    
    args = parser.parse_args()
    
    # Parse dates
    since = None
    if args.since:
        since = datetime.fromisoformat(args.since.replace('Z', '+00:00'))
    
    # Parse source filter
    source_filter = None
    if args.source_filter:
        source_filter = [s.strip().upper() for s in args.source_filter.split(',')]
    
    # Parse weights
    weights_dict = {"base": 0.6, "market": 0.4}
    if args.weights:
        for part in args.weights.split(','):
            key, val = part.split(':')
            weights_dict[key.strip()] = float(val.strip())
    
    # Run enricher
    enricher = MarketSignalsEnricher(
        mode=args.mode,
        since=since,
        limit=args.limit,
        source_filter=source_filter,
        weights=weights_dict
    )
    
    await enricher.run()
    
    # Close DB connection
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
