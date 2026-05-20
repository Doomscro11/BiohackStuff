# Billing Routes - User & Admin for Peptimancer
import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status
from middleware.auth import get_current_user, require_admin
from billing.adapters import get_billing
from billing.service import (
    ensure_seed_plans, get_billing_state, get_all_plans, upsert_plan
)
from models import CheckoutBody, PlanUpsert

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.on_event("startup")
async def seed_billing_plans_on_startup():
    """Seed default billing plans during application startup.

    This must not run at module import time because clean imports and CI smoke
    checks may occur without a running asyncio event loop.
    """
    await ensure_seed_plans()


# ==================== User Billing Routes ====================

@router.get("/state")
async def billing_state(request: Request):
    """Get user's billing state: tier, credits, subscription, history"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    state = await get_billing_state(user["id"])
    return state

@router.post("/checkout")
async def billing_checkout(body: CheckoutBody, request: Request):
    """
    Create checkout session for plan subscription or credit purchase
    Redirects user to Stripe Checkout (or mock page in mock mode)
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Validate request
    if not (body.plan or body.purchase_credits or body.package_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specify either 'plan', 'purchase_credits', or 'package_id'"
        )
    
    try:
        bill = get_billing()
        result = bill.create_checkout(
            user["id"],
            user["email"],
            plan=body.plan,
            purchase_credits=body.purchase_credits,
            package_id=body.package_id
        )
        
        # Phase VIII: Persist session→user mapping for webhook resolution
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'peptimancer_db')]
        
        await db.checkout_sessions.insert_one({
            "session_id": result.session_id,
            "user_id": user["id"],
            "email": user["email"],
            "plan": body.plan,
            "purchase_credits": body.purchase_credits,
            "package_id": body.package_id,
            "provider": result.provider,
            "created_at": datetime.utcnow()
        })
        
        logger.info(f"Checkout session created for user {user['id']}: {result.session_id}")
        
        return {
            "ok": True,
            "provider": result.provider,
            "url": result.url,
            "session": result.session_id
        }
    
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout: {str(e)}"
        )

# ==================== Admin Billing Routes ====================

@router.get("/admin/plans")
async def admin_get_plans(request: Request):
    """Get all billing plans (admin only)"""
    user = require_admin(request)
    
    # Phase 7.1: Require 2FA
    if not getattr(request.state, "admin2fa", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA verification required"
        )
    
    plans_list = await get_all_plans()
    return {"items": plans_list}

@router.put("/admin/plans")
async def admin_upsert_plan(body: PlanUpsert, request: Request):
    """Update or create billing plan (admin only)"""
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    
    user = require_admin(request)
    
    # Phase 7.1: Require 2FA
    if not getattr(request.state, "admin2fa", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA verification required"
        )
    
    # Validate inputs
    if body.price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be >= 0"
        )
    
    if body.credits < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credits must be >= 0"
        )
    
    # Get old plan for audit trail
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'peptimancer_db')]
    
    old_plan = await db.plans.find_one({"code": body.code})
    
    # Update plan
    await upsert_plan(body.code, body.price, body.credits)
    
    # Write to settings history for audit
    from audit_immutability import insert_strict
    await insert_strict(db._settings_history, {
        "type": "plan_update",
        "plan_code": body.code,
        "before": {
            "price": old_plan.get("price") if old_plan else None,
            "credits": old_plan.get("credits") if old_plan else None
        },
        "after": {
            "price": body.price,
            "credits": body.credits
        },
        "user": user.get("email"),
        "ts": datetime.utcnow()
    })
    
    logger.info(f"Admin {user['email']} updated plan: {body.code} (price={body.price}, credits={body.credits})")
    
    return {"ok": True}