"""
Market Signals Adapters (Phase IXd)
Adapters for fetching market intelligence signals from various sources
Supports both mock and real modes via feature flags
"""

import os
import logging
import random
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import math

logger = logging.getLogger(__name__)


class BaseSignalAdapter(ABC):
    """Abstract base adapter for market signals"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True):
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.adapter_name = self.__class__.__name__
        logger.info(f"{self.adapter_name} initialized (mock={mock_mode})")
    
    @abstractmethod
    async def fetch(self, query: str) -> Dict[str, Any]:
        """
        Fetch signal data for query
        
        Args:
            query: Search query (patent_id or keyword combination)
        
        Returns:
            Dict with signal-specific features
        """
        pass


class VendorCatalogAdapter(BaseSignalAdapter):
    """Adapter for peptide vendor catalog pricing and availability"""
    
    def __init__(self, api_key: Optional[str] = None):
        mock_mode = os.getenv("FEATURE_PATENTPULSE_SIGNALS", "false").lower() != "true" or not api_key
        super().__init__(api_key, mock_mode)
    
    async def fetch(self, query: str) -> Dict[str, Any]:
        """Fetch pricing and availability from vendor catalogs"""
        if self.mock_mode:
            await asyncio.sleep(random.uniform(0.1, 0.3))  # Simulate API latency
            
            # Simulate vendor data
            has_data = random.random() < 0.7  # 70% have vendor data
            
            if not has_data:
                return {"available": False}
            
            # Generate realistic pricing
            base_price = random.uniform(50, 5000)  # USD per mg
            vendors = random.randint(2, 8)
            prices = [base_price * random.uniform(0.7, 1.5) for _ in range(vendors)]
            
            return {
                "available": True,
                "avg_price": round(sum(prices) / len(prices), 2),
                "min_price": round(min(prices), 2),
                "max_price": round(max(prices), 2),
                "vendor_count": vendors,
                "in_stock_count": random.randint(1, vendors),
                "price_dispersion": round((max(prices) - min(prices)) / (sum(prices) / len(prices)), 3) if prices else 0
            }
        else:
            # Real API implementation would go here
            raise NotImplementedError("Real vendor catalog API not implemented")


class SearchTrendAdapter(BaseSignalAdapter):
    """Adapter for search trend data (Google Trends-like)"""
    
    def __init__(self, api_key: Optional[str] = None):
        mock_mode = os.getenv("FEATURE_PATENTPULSE_SIGNALS", "false").lower() != "true" or not api_key
        super().__init__(api_key, mock_mode)
    
    async def fetch(self, query: str) -> Dict[str, Any]:
        """Fetch search trend index (0-100)"""
        if self.mock_mode:
            await asyncio.sleep(random.uniform(0.1, 0.2))
            
            # Generate search trend (0-100 scale)
            # Higher for common therapeutic peptides
            base_interest = random.uniform(20, 80)
            
            # Boost for certain keywords
            query_lower = query.lower()
            if any(kw in query_lower for kw in ["glp-1", "insulin", "growth hormone"]):
                base_interest += 15
            
            return {
                "search_index": min(100, round(base_interest, 1)),
                "trend": random.choice(["rising", "stable", "declining"]),
                "related_queries": ["peptide synthesis", "therapeutic peptides", "peptide analogs"]
            }
        else:
            raise NotImplementedError("Real search trend API not implemented")


class SocialChatterAdapter(BaseSignalAdapter):
    """Adapter for social media sentiment and volume"""
    
    def __init__(self, api_key: Optional[str] = None):
        mock_mode = os.getenv("FEATURE_PATENTPULSE_SIGNALS", "false").lower() != "true" or not api_key
        super().__init__(api_key, mock_mode)
    
    async def fetch(self, query: str) -> Dict[str, Any]:
        """Fetch social sentiment and volume"""
        if self.mock_mode:
            await asyncio.sleep(random.uniform(0.1, 0.25))
            
            # Generate sentiment (-1 to 1) and volume
            has_chatter = random.random() < 0.5  # 50% have social mentions
            
            if not has_chatter:
                return {
                    "sentiment": 0.0,
                    "volume": 0,
                    "sources": []
                }
            
            sentiment = random.uniform(-0.3, 0.8)  # Slight positive bias for therapeutics
            volume = random.randint(10, 5000)
            
            return {
                "sentiment": round(sentiment, 3),
                "volume": volume,
                "sources": ["Twitter", "Reddit", "LinkedIn"],
                "keywords": ["peptide", "therapeutic", "biotech"]
            }
        else:
            raise NotImplementedError("Real social chatter API not implemented")


class MarketplaceAdapter(BaseSignalAdapter):
    """Adapter for marketplace transaction data"""
    
    def __init__(self, api_key: Optional[str] = None):
        mock_mode = os.getenv("FEATURE_PATENTPULSE_SIGNALS", "false").lower() != "true" or not api_key
        super().__init__(api_key, mock_mode)
    
    async def fetch(self, query: str) -> Dict[str, Any]:
        """Fetch marketplace transaction data"""
        if self.mock_mode:
            await asyncio.sleep(random.uniform(0.1, 0.2))
            
            # Generate transaction velocity
            has_transactions = random.random() < 0.4  # 40% have marketplace data
            
            if not has_transactions:
                return {
                    "active": False,
                    "transaction_count": 0
                }
            
            transactions = random.randint(5, 200)
            avg_transaction_value = random.uniform(1000, 50000)
            
            return {
                "active": True,
                "transaction_count": transactions,
                "avg_value": round(avg_transaction_value, 2),
                "velocity_score": min(1.0, transactions / 200)  # Normalize to 0-1
            }
        else:
            raise NotImplementedError("Real marketplace API not implemented")


def get_signal_adapter(adapter_type: str, api_key: Optional[str] = None):
    """Factory function to get appropriate signal adapter"""
    adapters = {
        "vendor": VendorCatalogAdapter,
        "search": SearchTrendAdapter,
        "social": SocialChatterAdapter,
        "marketplace": MarketplaceAdapter
    }
    
    if adapter_type.lower() not in adapters:
        raise ValueError(f"Unknown adapter type: {adapter_type}")
    
    return adapters[adapter_type.lower()](api_key=api_key)
