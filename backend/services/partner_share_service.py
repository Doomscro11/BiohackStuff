"""
Partner Share Service
Handles share token generation, verification, and share management logic
"""

import os
import hmac
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

from models.partner_share import PartnerShare, SharePolicy
from analytics.partner_analytics import track_event

logger = logging.getLogger(__name__)

# Configuration from environment
PARTNER_SIGNING_SECRET = os.environ.get('PARTNER_SIGNING_SECRET', 'change_this_secret_in_production')
PARTNER_SHARE_TTL_DAYS = int(os.environ.get('PARTNER_SHARE_TTL_DAYS', '14'))
PARTNER_MAX_DOWNLOADS = int(os.environ.get('PARTNER_MAX_DOWNLOADS', '10'))
WATERMARK_ENABLED = os.environ.get('WATERMARK_ENABLED', 'true').lower() == 'true'

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'peptimancer_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


def generate_share_token(share_id: str, file_id: str, expires_at: datetime) -> str:
    """
    Generate HMAC-signed share token
    
    Format: share_id|file_id|expires_at|signature
    """
    expires_ts = int(expires_at.timestamp())
    message = f"{share_id}|{file_id}|{expires_ts}"
    signature = hmac.new(
        PARTNER_SIGNING_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    token = f"{share_id}|{file_id}|{expires_ts}|{signature}"
    return token


def verify_share_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify share token and extract data
    
    Returns:
        Dict with share_id, file_id, expires_at or None if invalid
    """
    try:
        parts = token.split('|')
        if len(parts) != 4:
            return None
        
        share_id, file_id, expires_ts_str, signature = parts
        expires_ts = int(expires_ts_str)
        
        # Verify signature
        message = f"{share_id}|{file_id}|{expires_ts}"
        expected_signature = hmac.new(
            PARTNER_SIGNING_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning(f"Invalid signature for token")
            return None
        
        # Check expiry
        expires_at = datetime.fromtimestamp(expires_ts, tz=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            logger.warning(f"Expired token for share {share_id}")
            return None
        
        return {
            'share_id': share_id,
            'file_id': file_id,
            'expires_at': expires_at
        }
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


async def create_partner_share(
    reclaim_pack_id: str,
    recipient_org: str,
    recipient_email: str,
    created_by: str,
    policy: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a new partner share
    
    Returns:
        Dict with share_id, token, and share details
    """
    share_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    
    # Use default policy if not provided
    if not policy:
        policy = {
            'ttl_days': PARTNER_SHARE_TTL_DAYS,
            'max_downloads': PARTNER_MAX_DOWNLOADS,
            'allowed_ips': [],
            'watermark': WATERMARK_ENABLED
        }
    
    expires_at = created_at + timedelta(days=policy.get('ttl_days', PARTNER_SHARE_TTL_DAYS))
    
    # Generate token
    token = generate_share_token(share_id, reclaim_pack_id, expires_at)
    
    # Create share document
    share = {
        'share_id': share_id,
        'reclaim_pack_id': reclaim_pack_id,
        'recipient_org': recipient_org,
        'recipient_email': recipient_email,
        'token': token,
        'created_by': created_by,
        'created_at': created_at.isoformat(),
        'expires_at': expires_at.isoformat(),
        'status': 'active',
        'access_count': 0,
        'download_count': 0,
        'policy': policy,
        'last_accessed': None
    }
    
    # Store in database
    await db.partner_shares.insert_one(share)
    
    logger.info(f"Created partner share {share_id} for {recipient_org}")
    
    return {
        'share_id': share_id,
        'token': token,
        'expires_at': expires_at,
        'share_url': f"/share/{token}"
    }


async def get_share_by_id(share_id: str) -> Optional[Dict[str, Any]]:
    """Get share by ID"""
    share = await db.partner_shares.find_one({'share_id': share_id}, {'_id': 0})
    return share


async def get_share_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Get share by token"""
    share = await db.partner_shares.find_one({'token': token}, {'_id': 0})
    return share


async def validate_share_access(
    share: Dict[str, Any],
    client_ip: Optional[str] = None
) -> Dict[str, bool]:
    """
    Validate if access to share is allowed
    
    Returns:
        Dict with 'allowed' (bool) and optional 'reason' (str)
    """
    # Check status
    if share.get('status') != 'active':
        return {'allowed': False, 'reason': f"Share is {share.get('status')}"}
    
    # Check expiry
    expires_at = datetime.fromisoformat(share['expires_at'])
    if datetime.now(timezone.utc) > expires_at:
        return {'allowed': False, 'reason': 'Share has expired'}
    
    # Check download limit
    policy = share.get('policy', {})
    max_downloads = policy.get('max_downloads', PARTNER_MAX_DOWNLOADS)
    if share.get('download_count', 0) >= max_downloads:
        return {'allowed': False, 'reason': 'Download limit reached'}
    
    # Check IP whitelist if configured
    allowed_ips = policy.get('allowed_ips', [])
    if allowed_ips and client_ip:
        if client_ip not in allowed_ips:
            return {'allowed': False, 'reason': 'IP not whitelisted'}
    
    return {'allowed': True}


async def increment_access_count(share_id: str):
    """Increment the access count for a share"""
    await db.partner_shares.update_one(
        {'share_id': share_id},
        {
            '$inc': {'access_count': 1},
            '$set': {'last_accessed': datetime.now(timezone.utc).isoformat()}
        }
    )


async def increment_download_count(share_id: str):
    """Increment the download count for a share"""
    await db.partner_shares.update_one(
        {'share_id': share_id},
        {
            '$inc': {'download_count': 1},
            '$set': {'last_accessed': datetime.now(timezone.utc).isoformat()}
        }
    )


async def revoke_share(share_id: str) -> bool:
    """
    Revoke a share
    
    Returns:
        True if revoked, False if not found
    """
    result = await db.partner_shares.update_one(
        {'share_id': share_id},
        {'$set': {'status': 'revoked'}}
    )
    
    if result.modified_count > 0:
        logger.info(f"Revoked share {share_id}")
        return True
    
    return False


async def list_shares(
    status: Optional[str] = None,
    recipient_org: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List partner shares with optional filters
    """
    query = {}
    
    if status:
        query['status'] = status
    
    if recipient_org:
        query['recipient_org'] = recipient_org
    
    cursor = db.partner_shares.find(query, {'_id': 0}).limit(limit).sort('created_at', -1)
    shares = await cursor.to_list(length=limit)
    
    return shares


async def cleanup_expired_shares() -> int:
    """
    Mark expired shares as expired
    
    Returns:
        Number of shares marked as expired
    """
    now = datetime.now(timezone.utc).isoformat()
    
    result = await db.partner_shares.update_many(
        {
            'status': 'active',
            'expires_at': {'$lt': now}
        },
        {'$set': {'status': 'expired'}}
    )
    
    count = result.modified_count
    if count > 0:
        logger.info(f"Marked {count} shares as expired")
    
    return count
