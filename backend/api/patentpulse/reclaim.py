"""
PatentPulse Reclaim Pack API Routes (Phase IXe)
Endpoints for generating and managing patent export reports
"""

import os
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, status, Depends, Query
from fastapi.responses import FileResponse
from pathlib import Path

from services import reclaim_service

logger = logging.getLogger(__name__)

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
        return await reclaim_service.generate_reclaim_pack(
            format=format,
            limit=limit,
            country=country,
            status=status
        )
    except Exception as e:
        logger.error(f"Export generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export generation failed: {str(e)}"
        )


@router.get("/exports")
async def get_exports_list(
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get list of available exports (no auth required for dropdown population)
    Returns list of export metadata for selection
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        # Fetch exports directly from database
        exports = []
        async for export in db.reclaim_pack_exports.find().sort("generated_at", -1).limit(limit):
            exports.append({
                "export_id": export.get("export_id"),
                "filename": export.get("filename"),
                "format": export.get("format"),
                "generated_at": export.get("generated_at"),
                "item_count": export.get("item_count"),
                "file_size_kb": export.get("file_size_kb"),
                "metadata": export.get("metadata", {})
            })
        
        client.close()
        return {"exports": exports}
    except Exception as e:
        logger.error(f"Failed to list exports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list exports: {str(e)}"
        )


@router.get("/list")
async def list_exports(
    limit: int = Query(20, ge=1, le=100),
    user=Depends(require_admin_2fa)
):
    """
    List recent exports (admin only, with 2FA)
    Returns list of export metadata, sorted by generated_at DESC
    """
    check_feature_flag()
    
    try:
        return await reclaim_service.list_exports(limit=limit)
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
        # Get export metadata
        export = await reclaim_service.get_export_metadata(file_id)
        
        if not export:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export {file_id} not found"
            )
        
        # Validate access
        validation = await reclaim_service.validate_export_access(export)
        if not validation['allowed']:
            if 'expired' in validation['reason']:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail=validation['reason']
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=validation['reason']
                )
        
        # Return file
        file_path = Path(export["file_path"])
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
        result = await reclaim_service.delete_export(file_id)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result['message']
            )
        
        return {"message": result['message']}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed for {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )
