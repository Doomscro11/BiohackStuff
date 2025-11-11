"""
Tests for Partner Portal (Phase IXf+)
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.partner_share import PartnerShare, SharePolicy, ShareCreationRequest
from routes.partner_shares import generate_share_token, verify_share_token, check_rate_limit
from analytics.partner_analytics import track_event, get_share_analytics, cleanup_old_events
from watermark.pdf_watermark import mask_email, add_json_watermark_headers


# MongoDB test setup
@pytest.fixture
async def clean_db():
    """Clean database before and after tests"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'peptimancer_test_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Clean collections
    await db.partner_shares.delete_many({})
    await db.partner_share_events.delete_many({})
    await db.patentpulse_exports.delete_many({})
    
    yield db
    
    # Cleanup after tests
    await db.partner_shares.delete_many({})
    await db.partner_share_events.delete_many({})
    await db.patentpulse_exports.delete_many({})
    
    client.close()


# ============================================================
# Token Tests
# ============================================================

def test_generate_share_token():
    """Test share token generation"""
    share_id = "test_share_123"
    file_id = "test_file_456"
    expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    
    token = generate_share_token(share_id, file_id, expires_at)
    
    # Token should have 4 parts separated by |
    parts = token.split('|')
    assert len(parts) == 4
    assert parts[0] == share_id
    assert parts[1] == file_id
    assert parts[2] == str(int(expires_at.timestamp()))
    assert len(parts[3]) == 64  # SHA256 hex digest


def test_verify_share_token_valid():
    """Test token verification with valid token"""
    share_id = "test_share_123"
    file_id = "test_file_456"
    expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    
    token = generate_share_token(share_id, file_id, expires_at)
    result = verify_share_token(token)
    
    assert result is not None
    assert result["share_id"] == share_id
    assert result["file_id"] == file_id
    assert abs((result["expires_at"] - expires_at).total_seconds()) < 1


def test_verify_share_token_expired():
    """Test token verification with expired token"""
    share_id = "test_share_123"
    file_id = "test_file_456"
    expires_at = datetime.now(timezone.utc) - timedelta(days=1)  # Expired
    
    token = generate_share_token(share_id, file_id, expires_at)
    result = verify_share_token(token)
    
    assert result is None  # Token should be rejected


def test_verify_share_token_invalid_signature():
    """Test token verification with tampered signature"""
    share_id = "test_share_123"
    file_id = "test_file_456"
    expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    
    token = generate_share_token(share_id, file_id, expires_at)
    
    # Tamper with token
    tampered = token.replace('123', '999')
    result = verify_share_token(tampered)
    
    assert result is None  # Tampered token should be rejected


# ============================================================
# Watermarking Tests
# ============================================================

def test_mask_email():
    """Test email masking for watermarks"""
    assert mask_email("john.doe@company.com") == "j*******e@company.com"
    assert mask_email("a@test.com") == "a***@test.com"
    assert mask_email("ab@test.com") == "a***@test.com"
    assert mask_email("invalid") == "i***"


def test_add_json_watermark_headers():
    """Test JSON watermark metadata"""
    data = {"patents": [{"id": "US123"}]}
    recipient = "partner@company.com"
    expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    company = "ACME Pharma"
    
    result = add_json_watermark_headers(data, recipient, expires_at, company)
    
    assert "_watermark" in result
    assert result["_watermark"]["recipient"] == mask_email(recipient)
    assert result["_watermark"]["company"] == company
    assert result["_watermark"]["confidential"] is True
    assert result["_watermark"]["redistribution_prohibited"] is True


# ============================================================
# Analytics Tests
# ============================================================

@pytest.mark.asyncio
async def test_track_event(clean_db):
    """Test analytics event tracking"""
    share_id = "test_share_123"
    
    event_id = await track_event(
        share_id=share_id,
        event="open",
        ip="192.168.1.1",
        user_agent="Mozilla/5.0",
        geo_country="US"
    )
    
    assert event_id is not None
    
    # Verify event stored
    event = await clean_db.partner_share_events.find_one({"event_id": event_id})
    assert event is not None
    assert event["share_id"] == share_id
    assert event["event"] == "open"
    assert event["ip"] == "192.168.1.1"


@pytest.mark.asyncio
async def test_get_share_analytics(clean_db):
    """Test retrieving share analytics"""
    share_id = "test_share_123"
    
    # Track multiple events
    await track_event(share_id, "open", "192.168.1.1")
    await track_event(share_id, "open", "192.168.1.2")
    await track_event(share_id, "download", "192.168.1.1")
    await track_event(share_id, "blocked", "192.168.1.3", reason="rate_limit")
    
    analytics = await get_share_analytics(share_id)
    
    assert analytics["opens"] == 2
    assert analytics["downloads"] == 1
    assert analytics["blocked"] == 1
    assert analytics["last_access_at"] is not None
    assert len(analytics["top_ips"]) == 3


@pytest.mark.asyncio
async def test_cleanup_old_events(clean_db):
    """Test cleaning up old analytics events"""
    share_id = "test_share_123"
    
    # Create old event
    old_event = {
        "event_id": "old_event",
        "share_id": share_id,
        "event": "open",
        "ts": datetime.now(timezone.utc) - timedelta(days=200),
        "ip": "192.168.1.1"
    }
    await clean_db.partner_share_events.insert_one(old_event)
    
    # Create recent event
    await track_event(share_id, "download", "192.168.1.1")
    
    deleted_count = await cleanup_old_events(days=180)
    
    assert deleted_count == 1
    
    # Verify only recent event remains
    remaining = await clean_db.partner_share_events.count_documents({})
    assert remaining == 1


# ============================================================
# Rate Limiting Tests
# ============================================================

def test_check_rate_limit():
    """Test per-IP rate limiting"""
    ip = "192.168.1.100"
    
    # First 30 requests should pass
    for i in range(30):
        assert check_rate_limit(ip) is True
    
    # 31st request should be rate limited
    assert check_rate_limit(ip) is False


# ============================================================
# Integration Tests
# ============================================================

@pytest.mark.asyncio
async def test_share_creation_flow(clean_db):
    """Test complete share creation flow"""
    # Create export file
    export_doc = {
        "file_id": "export_123",
        "file_name": "reclaim_pack_2024.pdf",
        "format": "pdf",
        "generated_at": datetime.now(timezone.utc),
        "file_path": "/tmp/test.pdf"
    }
    await clean_db.patentpulse_exports.insert_one(export_doc)
    
    # Create share
    share = PartnerShare(
        share_id="share_123",
        file_id="export_123",
        file_name="reclaim_pack_2024.pdf",
        format="pdf",
        recipient_email="partner@company.com",
        recipient_first_name="John",
        company_or_project="ACME Pharma",
        policy=SharePolicy(
            expires_at=datetime.now(timezone.utc) + timedelta(days=14),
            max_downloads=10
        ),
        share_token="test_token",
        created_by="admin@peptimancer.com"
    )
    
    await clean_db.partner_shares.insert_one(share.dict())
    
    # Verify share created
    saved_share = await clean_db.partner_shares.find_one({"share_id": "share_123"})
    assert saved_share is not None
    assert saved_share["recipient_email"] == "partner@company.com"
    assert saved_share["state"] == "active"


@pytest.mark.asyncio
async def test_share_download_tracking(clean_db):
    """Test download count tracking"""
    # Create share
    share = PartnerShare(
        share_id="share_123",
        file_id="export_123",
        file_name="test.pdf",
        format="pdf",
        recipient_email="partner@company.com",
        recipient_first_name="John",
        company_or_project="ACME",
        policy=SharePolicy(
            expires_at=datetime.now(timezone.utc) + timedelta(days=14),
            max_downloads=3
        ),
        share_token="test_token",
        created_by="admin@test.com"
    )
    
    await clean_db.partner_shares.insert_one(share.dict())
    
    # Simulate 3 downloads
    for i in range(3):
        await track_event(share.share_id, "download", f"192.168.1.{i}")
        await clean_db.partner_shares.update_one(
            {"share_id": share.share_id},
            {"$inc": {"download_count": 1}}
        )
    
    # Verify download count
    updated_share = await clean_db.partner_shares.find_one({"share_id": share.share_id})
    assert updated_share["download_count"] == 3
    
    # Verify analytics
    analytics = await get_share_analytics(share.share_id)
    assert analytics["downloads"] == 3


@pytest.mark.asyncio
async def test_share_revocation(clean_db):
    """Test share revocation flow"""
    # Create share
    share = PartnerShare(
        share_id="share_123",
        file_id="export_123",
        file_name="test.pdf",
        format="pdf",
        recipient_email="partner@company.com",
        recipient_first_name="John",
        company_or_project="ACME",
        policy=SharePolicy(
            expires_at=datetime.now(timezone.utc) + timedelta(days=14),
            max_downloads=10
        ),
        share_token="test_token",
        created_by="admin@test.com"
    )
    
    await clean_db.partner_shares.insert_one(share.dict())
    
    # Revoke share
    await clean_db.partner_shares.update_one(
        {"share_id": share.share_id},
        {
            "$set": {
                "state": "revoked",
                "revoked_at": datetime.now(timezone.utc),
                "revoked_by": "admin@test.com",
                "revoked_reason": "Security concern"
            }
        }
    )
    
    # Track revocation event
    await track_event(share.share_id, "revoked", "internal", reason="Security concern")
    
    # Verify revocation
    revoked_share = await clean_db.partner_shares.find_one({"share_id": share.share_id})
    assert revoked_share["state"] == "revoked"
    assert revoked_share["revoked_by"] == "admin@test.com"
    
    # Verify analytics
    analytics = await get_share_analytics(share.share_id)
    assert analytics["revoked"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
