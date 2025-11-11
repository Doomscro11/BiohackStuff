"""
PatentPulse Source Adapters (Phase IXc)
Provides abstract base adapter and concrete implementations for USPTO, WIPO, LENS
Supports both mock and real modes via feature flags
"""

import os
import logging
import random
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Backoff configuration
BASE_BACKOFF = 0.5  # seconds
BACKOFF_FACTOR = 2
MAX_BACKOFF = 60  # seconds
MAX_ATTEMPTS = 5
REQUEST_TIMEOUT = 8  # seconds
PAGE_CAP = 30  # seconds per page


class RateLimitInfo(dict):
    """Rate limit information from API"""
    def __init__(self, remaining: int = 0, reset_at: Optional[datetime] = None):
        super().__init__(remaining=remaining, reset_at=reset_at)
        self.remaining = remaining
        self.reset_at = reset_at


class BaseAdapter(ABC):
    """Abstract base adapter for patent sources"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True):
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.source_name = self.__class__.__name__.replace("Adapter", "")
        logger.info(f"{self.source_name} adapter initialized (mock={mock_mode})")
    
    @abstractmethod
    async def fetch_changed(self, since: datetime, until: datetime, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch changed patents since the last run
        
        Args:
            since: Start datetime for incremental sync
            until: End datetime
            page_token: Continuation token for pagination
        
        Returns:
            {
                "items": [...],  # List of raw patent records
                "next_token": str | None,  # Next page token
                "rate_limit_info": RateLimitInfo | None
            }
        """
        pass
    
    async def fetch_with_backoff(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch with exponential backoff retry logic"""
        attempt = 0
        backoff = BASE_BACKOFF
        
        while attempt < MAX_ATTEMPTS:
            try:
                # In real implementation, use aiohttp here
                if self.mock_mode:
                    await asyncio.sleep(random.uniform(0.1, 0.3))  # Simulate API latency
                    return self._mock_response(params)
                else:
                    # Real API call would go here
                    raise NotImplementedError(f"Real API not implemented for {self.source_name}")
            
            except Exception as e:
                attempt += 1
                if attempt >= MAX_ATTEMPTS:
                    logger.error(f"{self.source_name} fetch failed after {MAX_ATTEMPTS} attempts: {e}")
                    raise
                
                logger.warning(f"{self.source_name} fetch attempt {attempt} failed, retrying in {backoff}s: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * BACKOFF_FACTOR, MAX_BACKOFF)
    
    @abstractmethod
    def _mock_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock response for testing"""
        pass


class USPTOAdapter(BaseAdapter):
    """USPTO Patent API Adapter"""
    
    def __init__(self, api_key: Optional[str] = None):
        mock_mode = os.getenv("FEATURE_PATENTPULSE_SOURCES", "false").lower() != "true" or not api_key
        super().__init__(api_key, mock_mode)
    
    async def fetch_changed(self, since: datetime, until: datetime, page_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch changed USPTO patents"""
        params = {
            "since": since.isoformat(),
            "until": until.isoformat(),
            "page_token": page_token,
            "status": ["expired", "lapsed"]
        }
        
        # Mock or real fetch
        result = await self.fetch_with_backoff("https://api.uspto.gov/patents/search", params)
        return result
    
    def _mock_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic USPTO mock data"""
        # Simulate 3-8 patents per page
        num_items = random.randint(3, 8)
        items = []
        
        for i in range(num_items):
            patent_id = f"US{random.randint(7000000, 9999999)}"
            expiry_date = datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1095))
            
            items.append({
                "patent_number": patent_id,
                "title": f"Peptide therapeutic composition for metabolic disease treatment",
                "assignee_name": random.choice(["Novo Nordisk", "Eli Lilly", "Amgen", "Genentech"]),
                "expiry_date": expiry_date.isoformat(),
                "status": random.choice(["Expired", "Lapsed"]),
                "abstract": "Novel peptide analogues with improved pharmacokinetic properties...",
                "classifications": ["A61K38/00", "C07K14/00"],
                "country": "US"
            })
        
        # Simulate pagination
        next_token = None
        if random.random() < 0.3:  # 30% chance of more pages
            next_token = f"page_{random.randint(2, 5)}"
        
        return {
            "items": items,
            "next_token": next_token,
            "rate_limit_info": RateLimitInfo(remaining=45, reset_at=datetime.now(timezone.utc) + timedelta(hours=1))
        }


class WIPOAdapter(BaseAdapter):
    """WIPO (World Intellectual Property Organization) API Adapter"""
    
    def __init__(self, api_key: Optional[str] = None):
        mock_mode = os.getenv("FEATURE_PATENTPULSE_SOURCES", "false").lower() != "true" or not api_key
        super().__init__(api_key, mock_mode)
    
    async def fetch_changed(self, since: datetime, until: datetime, page_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch changed WIPO patents"""
        params = {
            "since": since.isoformat(),
            "until": until.isoformat(),
            "page_token": page_token,
            "classifications": ["A61K", "C07K"]  # Pharma and peptides
        }
        
        result = await self.fetch_with_backoff("https://patentscope.wipo.int/api/v1/search", params)
        return result
    
    def _mock_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic WIPO mock data"""
        num_items = random.randint(2, 6)
        items = []
        
        for i in range(num_items):
            country = random.choice(["WO", "EP", "JP"])
            patent_id = f"{country}{random.randint(2000000, 9999999)}"
            
            # WIPO often has ExpiringSoon patents
            if random.random() < 0.4:
                expiry_date = datetime.now(timezone.utc) + timedelta(days=random.randint(30, 730))
                status = "ExpiringSoon"
            else:
                expiry_date = datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1095))
                status = random.choice(["Expired", "Lapsed"])
            
            items.append({
                "application_id": patent_id,
                "title": f"Modified peptide sequence with enhanced stability",
                "applicant": random.choice(["Sanofi", "Merck", "Pfizer", "Takeda"]),
                "expiry_date": expiry_date.isoformat(),
                "status": status,
                "abstract": "Peptide compositions with improved therapeutic efficacy...",
                "country_code": country
            })
        
        next_token = None
        if random.random() < 0.2:
            next_token = f"wipo_page_{random.randint(2, 4)}"
        
        return {
            "items": items,
            "next_token": next_token,
            "rate_limit_info": RateLimitInfo(remaining=30, reset_at=datetime.now(timezone.utc) + timedelta(minutes=30))
        }


class LensAdapter(BaseAdapter):
    """Lens.org Patent API Adapter"""
    
    def __init__(self, api_key: Optional[str] = None):
        mock_mode = os.getenv("FEATURE_PATENTPULSE_SOURCES", "false").lower() != "true" or not api_key
        super().__init__(api_key, mock_mode)
    
    async def fetch_changed(self, since: datetime, until: datetime, page_token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch changed Lens patents"""
        params = {
            "query": "peptide OR GLP-1 OR insulin",
            "date_published_start": since.isoformat(),
            "date_published_end": until.isoformat(),
            "scroll_id": page_token
        }
        
        result = await self.fetch_with_backoff("https://api.lens.org/patent/search", params)
        return result
    
    def _mock_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic Lens mock data"""
        num_items = random.randint(4, 10)
        items = []
        
        for i in range(num_items):
            country = random.choice(["US", "EP", "CA", "JP"])
            patent_id = f"{country}{random.randint(5000000, 9999999)}"
            expiry_date = datetime.now(timezone.utc) - timedelta(days=random.randint(90, 1460))
            
            # Lens often includes sequence data
            has_sequence = random.random() < 0.8
            sequence = None
            if has_sequence:
                amino_acids = "ACDEFGHIKLMNPQRSTVWY"
                seq_length = random.randint(8, 20)
                sequence = ''.join(random.choice(amino_acids) for _ in range(seq_length))
            
            items.append({
                "lens_id": patent_id,
                "title": f"Bioactive peptide analog for therapeutic use",
                "owners": random.choice(["AstraZeneca", "Bayer", "Bristol-Myers Squibb", "Roche"]),
                "expiry_date": expiry_date.isoformat(),
                "legal_status": "Expired",
                "sequence_data": sequence,
                "jurisdiction": country
            })
        
        next_token = None
        if random.random() < 0.25:
            next_token = f"lens_scroll_{random.randint(100, 999)}"
        
        return {
            "items": items,
            "next_token": next_token,
            "rate_limit_info": RateLimitInfo(remaining=50, reset_at=datetime.now(timezone.utc) + timedelta(hours=1))
        }


def get_adapter(source: str, api_key: Optional[str] = None) -> BaseAdapter:
    """Factory function to get appropriate adapter"""
    adapters = {
        "USPTO": USPTOAdapter,
        "WIPO": WIPOAdapter,
        "LENS": LensAdapter
    }
    
    if source.upper() not in adapters:
        raise ValueError(f"Unknown source: {source}. Valid sources: {list(adapters.keys())}")
    
    return adapters[source.upper()](api_key=api_key)
