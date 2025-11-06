# Dynamic Settings Service for Peptimancer Enterprise
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from typing import Dict, Any, Optional, List
from .config_dynamic import DEFAULTS, validate_config_update

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
settings_collection = db['_runtime_settings']
audit_collection = db['_settings_audit']

# Cache configuration
_cache = {"value": DEFAULTS.copy(), "timestamp": datetime.min}
_TTL = timedelta(seconds=5)  # Cache TTL

logger = logging.getLogger(__name__)

async def _merge_env_overrides(doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge database settings with environment defaults"""
    merged = DEFAULTS.copy()
    if doc:
        # Only merge valid keys that exist in defaults
        for key, value in doc.items():
            if key in merged and key != "_id":
                merged[key] = value
    return merged

async def get_settings() -> Dict[str, Any]:
    """Get current runtime settings with caching"""
    global _cache
    now = datetime.utcnow()
    
    # Return cached value if still valid
    if now - _cache["timestamp"] < _TTL:
        return _cache["value"]
    
    try:
        # Fetch from database
        doc = await settings_collection.find_one({"_id": "runtime"})
        settings = await _merge_env_overrides(doc)
        
        # Update cache
        _cache = {"value": settings, "timestamp": now}
        return settings
        
    except Exception as e:
        logger.error(f"Failed to fetch settings from database: {e}")
        # Fallback to defaults if database is unavailable
        return DEFAULTS.copy()

async def set_settings(updates: Dict[str, Any], actor: str) -> Dict[str, Any]:
    """Update runtime settings with validation and audit trail"""
    try:
        # Validate updates
        validate_config_update(updates)
        
        # Get current settings for audit trail
        current_doc = await settings_collection.find_one({"_id": "runtime"}) or {}
        before_settings = await _merge_env_overrides(current_doc)
        
        # Apply updates
        after_settings = before_settings.copy()
        after_settings.update(updates)
        
        # Create audit record
        audit_record = {
            "timestamp": datetime.utcnow(),
            "actor": actor,
            "action": "settings_update",
            "before": before_settings,
            "after": after_settings,
            "changes": updates,
            "ip_address": None,  # Will be added by middleware if available
            "user_agent": None   # Will be added by middleware if available
        }
        
        # Store audit record
        await audit_collection.insert_one(audit_record)
        
        # Update settings
        await settings_collection.update_one(
            {"_id": "runtime"},
            {"$set": after_settings},
            upsert=True
        )
        
        # Invalidate cache
        global _cache
        _cache = {"value": DEFAULTS.copy(), "timestamp": datetime.min}
        
        logger.info(f"Settings updated by {actor}: {updates}")
        
        # Return updated settings
        return await get_settings()
        
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise

async def get_audit_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get settings change audit history"""
    try:
        cursor = audit_collection.find({}).sort("timestamp", -1).limit(limit)
        history = []
        
        async for record in cursor:
            # Convert ObjectId to string for JSON serialization
            record["_id"] = str(record["_id"])
            
            # Convert datetime to ISO string
            if isinstance(record.get("timestamp"), datetime):
                record["timestamp"] = record["timestamp"].isoformat()
            
            history.append(record)
            
        return history
        
    except Exception as e:
        logger.error(f"Failed to fetch audit history: {e}")
        return []

async def get_settings_info() -> Dict[str, Any]:
    """Get comprehensive settings information including metadata"""
    settings = await get_settings()
    
    # Get mode information
    from .config_dynamic import get_mode_display
    mode_info = get_mode_display(settings["integrationsMode"])
    
    # Get last update info
    last_audit = await audit_collection.find_one({}, sort=[("timestamp", -1)])
    
    return {
        "settings": settings,
        "mode_info": mode_info,
        "last_updated": last_audit["timestamp"].isoformat() if last_audit else None,
        "last_updated_by": last_audit["actor"] if last_audit else None,
        "cache_ttl_seconds": _TTL.total_seconds()
    }

async def reset_settings_to_defaults(actor: str) -> Dict[str, Any]:
    """Reset all settings to environment defaults"""
    return await set_settings(DEFAULTS.copy(), actor)

async def export_settings_backup() -> Dict[str, Any]:
    """Export current settings for backup purposes"""
    settings = await get_settings()
    history = await get_audit_history(100)
    
    return {
        "export_timestamp": datetime.utcnow().isoformat(),
        "current_settings": settings,
        "recent_history": history,
        "defaults": DEFAULTS
    }

# Initialize settings on module import
async def initialize_settings():
    """Initialize settings collection with defaults if not exists"""
    try:
        existing = await settings_collection.find_one({"_id": "runtime"})
        if not existing:
            logger.info("Initializing runtime settings with defaults")
            await settings_collection.insert_one({"_id": "runtime", **DEFAULTS})
            
            # Create initial audit record
            await audit_collection.insert_one({
                "timestamp": datetime.utcnow(),
                "actor": "system",
                "action": "settings_initialized",
                "before": {},
                "after": DEFAULTS,
                "changes": DEFAULTS
            })
    except Exception as e:
        logger.error(f"Failed to initialize settings: {e}")

# Utility functions for specific settings
async def is_demo_mode() -> bool:
    """Check if system is in demo mode"""
    settings = await get_settings()
    return settings["demoMode"]

async def get_rate_limit() -> int:
    """Get current rate limit based on mode"""
    settings = await get_settings()
    return settings["rateLimitDemo"] if settings["demoMode"] else settings["rateLimitLive"]

async def is_feature_enabled(feature: str) -> bool:
    """Check if a specific feature is enabled"""
    settings = await get_settings()
    feature_map = {
        "cro": "croEnabled",
        "billing": "billingEnabled", 
        "watermark": "watermarkExports",
        "enterprise": "enterpriseFeatures",
        "audit": "auditLogging"
    }
    
    if feature in feature_map:
        return settings.get(feature_map[feature], False)
    
    return False