"""
DEPRECATED: Partner Shares API

This module has been deprecated and all endpoints now return 410 Gone.
Partner Shares feature has been removed from the application.

TODO: Future external sharing/export feature will be implemented separately
as a dedicated "Export to PDF / Share Report" system with improved security.
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/patentpulse/partner", tags=["partner_shares_deprecated"])

@router.get("/shares", summary="[DEPRECATED] List partner shares")
async def list_shares_deprecated():
    """
    DEPRECATED: Partner Shares feature has been removed.
    Returns 410 Gone for backward compatibility.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Partner Shares have been deprecated in this version. External sharing will be reintroduced in a future release."
    )

@router.post("/shares", summary="[DEPRECATED] Create partner share")
async def create_share_deprecated():
    """
    DEPRECATED: Partner share creation is no longer supported.
    Returns 410 Gone for backward compatibility.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Partner Shares have been deprecated in this version. External sharing will be reintroduced in a future release."
    )

@router.post("/shares/{share_id}/rotate", summary="[DEPRECATED] Rotate share token")
async def rotate_share_deprecated(share_id: str):
    """
    DEPRECATED: Token rotation is no longer supported.
    Returns 410 Gone for backward compatibility.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Partner Shares have been deprecated in this version. External sharing will be reintroduced in a future release."
    )

@router.post("/shares/{share_id}/revoke", summary="[DEPRECATED] Revoke partner share")
async def revoke_share_deprecated(share_id: str):
    """
    DEPRECATED: Share revocation is no longer supported.
    Returns 410 Gone for backward compatibility.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Partner Shares have been deprecated in this version. External sharing will be reintroduced in a future release."
    )

@router.get("/shares/{share_id}", summary="[DEPRECATED] Get share details")
async def get_share_deprecated(share_id: str):
    """
    DEPRECATED: Share details endpoint is no longer supported.
    Returns 410 Gone for backward compatibility.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Partner Shares have been deprecated in this version. External sharing will be reintroduced in a future release."
    )

# All endpoints now return clean 410 errors with no database operations
# No response body consumption issues possible - FastAPI handles HTTP exceptions correctly
