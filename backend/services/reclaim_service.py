"""
Reclaim Service
Handles reclaim pack generation, listing, and management logic
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'peptimancer_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Config
EXPORT_DIR = os.environ.get('RECLAIM_EXPORT_DIR', '/app/exports')


def _serialize_dates(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime objects to ISO strings"""
    if item.get("_id"):
        item["_id"] = str(item["_id"])
    
    date_fields = ["generated_at", "expires_at", "created_at", "updated_at"]
    for field in date_fields:
        if isinstance(item.get(field), datetime):
            item[field] = item[field].isoformat()
    
    return item


async def generate_reclaim_pack(
    format: str,
    limit: int,
    country: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a reclaim pack export
    
    Args:
        format: 'pdf' or 'json'
        limit: Number of top patents (1-100)
        country: Country filter (US, EP, JP, etc)
        status: Status filter (Expired, Lapsed, ExpiringSoon)
        
    Returns:
        Dict with file_id, file_name, path, size, items, viability_avg, timestamps
    """
    from jobs.reclaim_pack_generator import ReclaimPackGenerator
    from models.reclaim_pack import ExportCriteria
    
    logger.info(f"Generating {format} reclaim pack: limit={limit}, country={country}, status={status}")
    
    # Build criteria
    criteria = ExportCriteria(
        limit=limit,
        status_filter=[status] if status else None,
        country_filter=country
    )
    
    # Generate
    generator = ReclaimPackGenerator(criteria, format, EXPORT_DIR)
    export_meta = await generator.generate()
    
    # Return metadata
    return {
        "file_id": export_meta.file_id,
        "file_name": export_meta.file_name,
        "format": export_meta.format,
        "path": f"/api/patentpulse/reclaim/{export_meta.file_id}/download",
        "size_kb": export_meta.size_kb,
        "items": export_meta.count,
        "viability_avg": export_meta.viability_avg,
        "generated_at": export_meta.generated_at.isoformat(),
        "expires_at": export_meta.expires_at.isoformat()
    }


async def list_exports(limit: int = 20) -> Dict[str, Any]:
    """
    List recent exports
    
    Args:
        limit: Maximum number of exports to return
        
    Returns:
        Dict with 'exports' list and 'count'
    """
    cursor = db.patentpulse_exports.find().sort("generated_at", -1).limit(limit)
    exports = await cursor.to_list(length=limit)
    
    # Serialize dates
    exports = [_serialize_dates(exp) for exp in exports]
    
    logger.info(f"Listed {len(exports)} exports")
    
    return {
        "exports": exports,
        "count": len(exports)
    }


async def get_export_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get export metadata by file_id
    
    Returns:
        Export metadata dict or None if not found
    """
    export = await db.patentpulse_exports.find_one({"file_id": file_id})
    
    if export:
        _serialize_dates(export)
    
    return export


async def validate_export_access(export: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate if export can be accessed
    
    Returns:
        Dict with 'allowed' (bool) and optional 'reason' (str)
    """
    # Check if expired
    if export.get("expires_at"):
        if isinstance(export["expires_at"], str):
            expires_at = datetime.fromisoformat(export["expires_at"])
        else:
            expires_at = export["expires_at"]
        
        if expires_at < datetime.now(timezone.utc):
            return {'allowed': False, 'reason': 'Export has expired'}
    
    # Check if file exists
    file_path = Path(export["file_path"])
    if not file_path.exists():
        return {'allowed': False, 'reason': 'Export file not found on disk'}
    
    return {'allowed': True}


async def delete_export(file_id: str) -> Dict[str, Any]:
    """
    Delete an export (file and metadata)
    
    Returns:
        Dict with 'success' (bool) and 'message' (str)
    """
    # Find export
    export = await db.patentpulse_exports.find_one({"file_id": file_id})
    
    if not export:
        return {'success': False, 'message': f"Export {file_id} not found"}
    
    # Delete file
    file_path = Path(export["file_path"])
    if file_path.exists():
        file_path.unlink()
        logger.info(f"Deleted file: {file_path}")
    
    # Delete metadata
    await db.patentpulse_exports.delete_one({"file_id": file_id})
    
    logger.info(f"Deleted export {file_id}")
    
    return {'success': True, 'message': f"Export {file_id} deleted successfully"}
