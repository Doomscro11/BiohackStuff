# Chemistry Options API for Peptimancer
from fastapi import APIRouter, Depends, HTTPException, status
from middleware.auth import get_current_user
from services import chemistry_service
from billing.service import get_billing_state

router = APIRouter(prefix="/api/chemistry", tags=["chemistry"])

@router.get("/options")
async def chemistry_options(user=Depends(get_current_user)):
    """
    Serve canonical chemistry options (modifications & exclusions) with tier filtering
    Anonymous users get basic tier options
    """
    # Get user tier (default to basic for anonymous)
    tier = "basic"
    if user:
        # Fetch tier from billing service
        try:
            billing = await get_billing_state(user["id"])
            tier = billing.get("tier", "basic")
        except Exception:
            # Fallback to basic if billing service fails
            tier = "basic"
    
    # Get filtered options from service
    return chemistry_service.get_chemistry_options(tier)
