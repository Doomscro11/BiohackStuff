# Chemistry Options API for Peptimancer
from fastapi import APIRouter, Depends, HTTPException, status
from middleware.auth import get_current_user
from constants.chemistry import ALLOWED_MOD_OPTIONS, EXCLUSION_OPTIONS, TIER_ORDER

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
        from billing.service import get_billing_state
        try:
            billing = await get_billing_state(user["id"])
            tier = billing.get("tier", "basic")
        except Exception:
            # Fallback to basic if billing service fails
            tier = "basic"
    
    # Helper to check if option is allowed for user's tier
    def allow(item):
        user_tier_level = TIER_ORDER.get(tier, 0)
        item_tier_level = TIER_ORDER.get(item.get("tier", "basic"), 0)
        return user_tier_level >= item_tier_level
    
    # Filter modifications by tier
    mods = [
        {"key": k, **v}
        for k, v in ALLOWED_MOD_OPTIONS.items()
        if allow(v)
    ]
    
    # Filter exclusions by tier
    exclusions = [
        {"key": k, **v}
        for k, v in EXCLUSION_OPTIONS.items()
        if allow(v)
    ]
    
    return {
        "tier": tier,
        "mods": mods,
        "exclusions": exclusions
    }
