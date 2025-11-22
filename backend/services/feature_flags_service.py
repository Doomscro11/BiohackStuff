"""
Feature Flags Service
Manages feature visibility and access control (architectural framework only)
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'peptimancer_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]


# Default feature flags (all disabled by default)
DEFAULT_FLAGS = {
    'advanced_mode_enabled': False,
    'experimental_ui_enabled': False,
    'preview_mode_enabled': False,
    'extended_analytics_enabled': False
}


async def get_feature_flags() -> Dict[str, Any]:
    """
    Get current feature flags
    
    Returns:
        Dict with feature flag states
    """
    flags_doc = await db.feature_flags.find_one({'_id': 'global'})
    
    if not flags_doc:
        # Initialize with defaults
        flags_doc = {
            '_id': 'global',
            'flags': DEFAULT_FLAGS.copy(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        await db.feature_flags.insert_one(flags_doc)
    
    return flags_doc.get('flags', DEFAULT_FLAGS)


async def update_feature_flag(flag_key: str, enabled: bool, config: Optional[Dict] = None, updated_by: Optional[str] = None) -> Dict[str, Any]:
    """
    Update a feature flag
    
    Args:
        flag_key: Feature flag identifier
        enabled: Enable or disable
        config: Optional configuration
        updated_by: User who updated the flag
        
    Returns:
        Updated flag state
    """
    now = datetime.now(timezone.utc).isoformat()
    
    update_data = {
        f'flags.{flag_key}': enabled,
        'updated_at': now
    }
    
    if updated_by:
        update_data['updated_by'] = updated_by
    
    if config:
        update_data[f'config.{flag_key}'] = config
    
    await db.feature_flags.update_one(
        {'_id': 'global'},
        {'$set': update_data},
        upsert=True
    )
    
    logger.info(f"Feature flag '{flag_key}' set to {enabled} by {updated_by or 'system'}")
    
    return {
        'flag_key': flag_key,
        'enabled': enabled,
        'config': config,
        'updated_at': now,
        'updated_by': updated_by
    }


async def get_user_feature_level(user_id: str) -> int:
    """
    Get user's feature access level
    
    Args:
        user_id: User identifier
        
    Returns:
        Feature level (0-4)
    """
    user = await db.users.find_one({'id': user_id})
    
    if not user:
        return 0
    
    return user.get('feature_level', 0)


async def set_user_feature_level(user_id: str, level: int, updated_by: Optional[str] = None) -> Dict[str, Any]:
    """
    Set user's feature access level
    
    Args:
        user_id: User identifier
        level: Feature level (0-4)
        updated_by: Admin who updated the level
        
    Returns:
        Updated user data
    """
    if not (0 <= level <= 4):
        raise ValueError("Feature level must be between 0 and 4")
    
    now = datetime.now(timezone.utc)
    
    result = await db.users.update_one(
        {'id': user_id},
        {
            '$set': {
                'feature_level': level,
                'feature_level_updated_at': now.isoformat(),
                'feature_level_updated_by': updated_by
            }
        }
    )
    
    if result.matched_count == 0:
        raise ValueError(f"User {user_id} not found")
    
    logger.info(f"User {user_id} feature level set to {level} by {updated_by or 'system'}")
    
    return {
        'user_id': user_id,
        'feature_level': level,
        'updated_at': now.isoformat(),
        'updated_by': updated_by
    }


async def get_feature_audit_log(limit: int = 100) -> list:
    """
    Get feature flag change audit log
    
    Args:
        limit: Maximum number of log entries
        
    Returns:
        List of audit log entries
    """
    cursor = db.feature_audit_log.find().sort('timestamp', -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    
    for log in logs:
        log['_id'] = str(log['_id'])
    
    return logs


async def log_feature_access(user_id: str, feature_key: str, level: int, metadata: Optional[Dict] = None):
    """
    Log feature access for analytics
    
    Args:
        user_id: User identifier
        feature_key: Feature that was accessed
        level: Feature level at time of access
        metadata: Additional metadata
    """
    await db.feature_audit_log.insert_one({
        'user_id': user_id,
        'feature_key': feature_key,
        'level': level,
        'metadata': metadata or {},
        'timestamp': datetime.now(timezone.utc).isoformat()
    })
