"""
PatentPulse Reclaim Pack API Routes (Phase IXe)
Endpoints for generating and managing patent export reports
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

# Import generator
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jobs.reclaim_pack_generator import ReclaimPackGenerator
from models.reclaim_pack import ExportCriteria, ReclaimPackExport

logger = logging.getLogger(__name__)

# Database
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]
patentpulse_exports = db['patentpulse_exports']

# Config
EXPORT_DIR = os.environ.get('RECLAIM_EXPORT_DIR', '/app/exports')

router = APIRouter(prefix="/api/patentpulse/reclaim", tags=["patentpulse_reclaim"])


def require_admin_2fa(request: Request):
    """Require admin with 2FA for reclaim pack access"""
    from middleware.auth import require_admin
    
    user = require_admin(request)
    
    # Check admin2fa
    if not getattr(request.state, 'admin2fa', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin 2FA required for PatentPulse Reclaim"
        )
    
    return user


def check_feature_flag():
    """Check if reclaim feature is enabled"""
    enabled = os.getenv("FEATURE_PATENTPULSE_RECLAIM", "false").lower() == "true"
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reclaim Pack feature not enabled. Set FEATURE_PATENTPULSE_RECLAIM=true"
        )


@router.get("/export")
async def generate_export(
    format: str = Query("pdf", regex="^(pdf|json)$"),
    limit: int = Query(10, ge=1, le=100),
    country: Optional[str] = Query(None, max_length=2),
    status: Optional[str] = Query(None, regex="^(Expired|Lapsed|ExpiringSoon)$"),
    user=Depends(require_admin_2fa)
):
    """
    Generate a reclaim pack export
    
    Query params:
    - format: pdf or json
    - limit: number of top patents (1-100)
    - country: country filter (US, EP, JP, etc)
    - status: status filter (Expired, Lapsed, ExpiringSoon)
    
    Returns metadata and download info
    """
    check_feature_flag()
    
    try:
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
    
    except Exception as e:
        logger.error(f"Export generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export generation failed: {str(e)}"
        )


@router.get("/list")
async def list_exports(
    limit: int = Query(20, ge=1, le=100),
    user=Depends(require_admin_2fa)
):
    """
    List recent exports
    Returns list of export metadata, sorted by generated_at DESC
    """
    check_feature_flag()
    
    try:
        cursor = patentpulse_exports.find().sort("generated_at", -1).limit(limit)
        exports = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for exp in exports:
            exp["_id"] = str(exp["_id"])
            
            # Convert datetime fields
            for date_field in ["generated_at", "expires_at"]:
                if date_field in exp and isinstance(exp[date_field], datetime):
                    exp[date_field] = exp[date_field].isoformat()
        
        return {
            "exports": exports,
            "count": len(exports)
        }
    
    except Exception as e:
        logger.error(f"Failed to list exports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list exports: {str(e)}"
        )


@router.get("/{file_id}/download")
async def download_export(
    file_id: str,
    user=Depends(require_admin_2fa)
):
    """
    Download an export file by file_id
    Returns file stream
    """
    check_feature_flag()
    
    try:
        # Find export metadata
        export = await patentpulse_exports.find_one({"file_id": file_id})
        
        if not export:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export {file_id} not found"
            )
        
        # Check if expired
        if export.get("expires_at") and export["expires_at"] < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Export has expired"
            )
        
        # Check if file exists
        file_path = Path(export["file_path"])
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found on disk"
            )
        
        # Return file
        media_type = "application/pdf" if export["format"] == "pdf" else "application/json"
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=export["file_name"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed for {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


@router.delete("/{file_id}")
async def delete_export(
    file_id: str,
    user=Depends(require_admin_2fa)
):
    """
    Delete an export (file and metadata)
    Admin only
    """
    check_feature_flag()
    
    try:
        # Find export
        export = await patentpulse_exports.find_one({"file_id": file_id})
        
        if not export:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export {file_id} not found"
            )
        
        # Delete file
        file_path = Path(export["file_path"])
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
        
        # Delete metadata
        await patentpulse_exports.delete_one({"file_id": file_id})
        
        return {"message": f"Export {file_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed for {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )
