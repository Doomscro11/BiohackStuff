# Chemistry Options API for Peptimancer
from fastapi import APIRouter, Depends, HTTPException, status
from middleware.auth import get_current_user
from constants.chemistry import ALLOWED_MOD_OPTIONS, EXCLUSION_OPTIONS, TIER_ORDER

router = APIRouter(prefix="/api/chemistry", tags=["chemistry"])

@router.get("/options")
def chemistry_options(user=Depends(get_current_user)):
    """
    Serve canonical chemistry options (modifications & exclusions) with tier filtering
    Anonymous users get basic tier options
    """
    # Get user tier (default to basic for anonymous)
    tier = "basic"
    if user:
        tier = user.get("tier", "basic")
    
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
