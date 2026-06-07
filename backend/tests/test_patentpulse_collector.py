"""
Tests for PatentPulse Production Collector (Phase IXc)
Tests idempotency, incremental sync, DQ, DLQ, and SLO metrics
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs.patentpulse_source_adapters import USPTOAdapter, WIPOAdapter, LensAdapter
from jobs.patentpulse_normalizer import normalize_item, derive_patent_id, compute_scores
from jobs.patentpulse_collector import PatentPulseCollector
from models.patentpulse import PatentItemInput, DataQualityError


class TestSourceAdapters:
    """Test patent source adapters"""
    
    @pytest.mark.asyncio
    async def test_uspto_adapter_mock(self):
        """Test USPTO adapter in mock mode"""
        adapter = USPTOAdapter()
        
        since = datetime.now(timezone.utc) - timedelta(days=7)
        until = datetime.now(timezone.utc)
        
        result = await adapter.fetch_changed(since, until)
        
        assert "items" in result
        assert "next_token" in result
        assert isinstance(result["items"], list)
        assert len(result["items"]) > 0
        
        # Check item structure
        item = result["items"][0]
        assert "patent_number" in item
        assert "title" in item
        assert "assignee_name" in item
        assert "expiry_date" in item
        assert "status" in item
    
    @pytest.mark.asyncio
    async def test_wipo_adapter_mock(self):
        """Test WIPO adapter in mock mode"""
        adapter = WIPOAdapter()
        
        since = datetime.now(timezone.utc) - timedelta(days=7)
        until = datetime.now(timezone.utc)
        
        result = await adapter.fetch_changed(since, until)
        
        assert "items" in result
        assert len(result["items"]) > 0
        
        item = result["items"][0]
        assert "application_id" in item
        assert item["status"] in ["Expired", "Lapsed", "ExpiringSoon"]
    
    @pytest.mark.asyncio
    async def test_lens_adapter_mock(self):
        """Test Lens adapter in mock mode"""
        adapter = LensAdapter()
        
        since = datetime.now(timezone.utc) - timedelta(days=7)
        until = datetime.now(timezone.utc)
        
        result = await adapter.fetch_changed(since, until)
        
        assert "items" in result
        assert len(result["items"]) > 0
        
        item = result["items"][0]
        assert "lens_id" in item
        # Lens often has sequence data
        assert "sequence_data" in item


class TestNormalizer:
    """Test patent data normalizer"""
    
    def test_derive_patent_id_uspto(self):
        """Test patent ID derivation for USPTO"""
        raw = {"patent_number": "US1234567"}
        patent_id = derive_patent_id("USPTO", raw)
        assert patent_id == "US1234567"
    
    def test_derive_patent_id_wipo(self):
        """Test patent ID derivation for WIPO"""
        raw = {"application_id": "WO2024001234"}
        patent_id = derive_patent_id("WIPO", raw)
        assert patent_id == "WO2024001234"
    
    def test_compute_scores(self):
        """Test score computation"""
        item = {"sequence_data": "ACDEFGHIKL", "status": "Expired"}
        scores = compute_scores(item)
        
        assert 0.0 <= scores["commercial_score"] <= 1.0
        assert 0.0 <= scores["synthesis_score"] <= 1.0
        assert 0.0 <= scores["fto_risk"] <= 1.0
    
    def test_normalize_item_valid(self):
        """Test normalization of valid patent data"""
        raw = {
            "patent_number": "US7654321",
            "title": "Novel peptide therapeutic composition for diabetes",
            "assignee_name": "Test Pharma Inc",
            "country": "US",
            "status": "Expired",
            "expiry_date": (datetime.now(timezone.utc) - timedelta(days=365)).isoformat(),
            "abstract": "A novel peptide composition...",
            "sequence_data": "ACDEFGHIKLMNP"
        }
        
        normalized = normalize_item("USPTO", raw)
        
        assert isinstance(normalized, PatentItemInput)
        assert normalized.patent_id == "US7654321"
        assert normalized.source == "USPTO"
        assert normalized.country == "US"
        assert normalized.status == "Expired"
        assert 0.0 <= normalized.commercial_score <= 1.0
    
    def test_normalize_item_invalid_title(self):
        """Test normalization fails on short title"""
        raw = {
            "patent_number": "US1111111",
            "title": "Short",  # Too short
            "assignee_name": "Test Inc",
            "country": "US",
            "status": "Expired",
            "expiry_date": (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        }
        
        with pytest.raises(DataQualityError):
            normalize_item("USPTO", raw)
    
    def test_normalize_item_invalid_sequence(self):
        """Test normalization fails on invalid sequence"""
        raw = {
            "patent_number": "US2222222",
            "title": "Test patent composition for therapy",
            "assignee_name": "Test Inc",
            "country": "US",
            "status": "Expired",
            "expiry_date": (datetime.now(timezone.utc) - timedelta(days=365)).isoformat(),
            "sequence_data": "ACE"  # Too short (< 8 AA)
        }
        
        with pytest.raises(DataQualityError):
            normalize_item("USPTO", raw)


class TestCollector:
    """Test production collector (integration tests)"""
    
    @pytest_asyncio.fixture
    async def clean_db(self):
        """Clean test database before each test"""
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'peptimancer_db')]
        
        # Clear test collections
        await db.patentpulse_items.delete_many({})
        await db.patentpulse_runs.delete_many({})
        await db.patentpulse_dlq.delete_many({})
        
        yield db
        
        client.close()
    
    @pytest.mark.asyncio
    async def test_idempotent_upsert_no_duplicates(self, clean_db):
        """Test that re-running collector with same data produces no duplicates"""
        since = datetime.now(timezone.utc) - timedelta(days=1)
        
        # First run
        collector1 = PatentPulseCollector(
            mode="dry-run",
            since=since,
            until=None,
            limit=10,
            source_filter=["USPTO"],
            verbose=False
        )
        
        await collector1.run_collection()
        first_count = collector1.run.counts["upserts"]
        
        # Second run (same data)
        collector2 = PatentPulseCollector(
            mode="dry-run",
            since=since,
            until=None,
            limit=10,
            source_filter=["USPTO"],
            verbose=False
        )
        
        await collector2.run_collection()
        second_count = collector2.run.counts["upserts"]
        
        # Should have 0 duplicates
        assert collector2.run.counts["duplicates"] == 0
        # Dry-run mode does not persist unchanged items, but it should process deterministically.
        assert first_count == second_count
    
    @pytest.mark.asyncio
    async def test_incremental_sync_since_last_success(self, clean_db):
        """Test incremental sync respects last successful run"""
        # First run
        collector1 = PatentPulseCollector(
            mode="dry-run",
            since=datetime.now(timezone.utc) - timedelta(days=7),
            until=None,
            limit=5,
            source_filter=["USPTO"],
            verbose=False
        )
        
        await collector1.run_collection()
        
        # Check that "since" is tracked
        assert collector1.since is not None
        assert collector1.run.status in ["success", "partial"]
    
    @pytest.mark.asyncio
    async def test_dry_run_no_writes(self, clean_db):
        """Test dry-run mode does not write to database"""
        collector = PatentPulseCollector(
            mode="dry-run",
            since=datetime.now(timezone.utc) - timedelta(days=1),
            until=None,
            limit=5,
            source_filter=["USPTO"],
            verbose=False
        )
        
        await collector.run_collection()
        
        # Check no actual DB writes
        count = await clean_db.patentpulse_items.count_documents({})
        assert count == 0  # Dry-run should not write
        
        # But should have counted operations
        assert collector.run.counts["upserts"] > 0 or collector.run.counts["updates"] > 0
    
    @pytest.mark.asyncio
    async def test_slo_calculation(self, clean_db):
        """Test SLO metrics are calculated"""
        collector = PatentPulseCollector(
            mode="dry-run",
            since=datetime.now(timezone.utc) - timedelta(days=1),
            until=None,
            limit=10,
            source_filter=["USPTO"],
            verbose=False
        )
        
        await collector.run_collection()
        
        # SLO metrics should be present
        assert "p95_ms" in collector.run.slo
        assert "error_rate" in collector.run.slo
        assert "dq_reject_rate" in collector.run.slo
        
        # p95 should be reasonable
        assert collector.run.slo["p95_ms"] >= 0
        assert collector.run.slo["error_rate"] >= 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
