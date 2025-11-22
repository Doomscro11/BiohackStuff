# Billing Service - Plans, Credits, Subscriptions for Peptimancer
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

logger = logging.getLogger(__name__)

def get_user_query(user_id: str) -> Dict[str, Any]:
    """Get user query that works with both ObjectId and string IDs"""
    try:
        # Try to use as ObjectId first (legacy users)
        return {"_id": ObjectId(user_id)}
    except:
        # Fall back to string ID (new users)
        return {"id": user_id}

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
users = db['users']
plans = db['plans']
subscriptions = db['subscriptions']
ledger = db['credits_ledger']

# Default plans from environment
DEFAULT_PLANS = {
    "basic": {
        "code": "basic",
        "price": int(os.getenv("PLAN_BASIC_PRICE", "0")),
        "credits": int(os.getenv("PLAN_BASIC_CREDITS", "10"))
    },
    "pro": {
        "code": "pro",
        "price": int(os.getenv("PLAN_PRO_PRICE", "49")),
        "credits": int(os.getenv("PLAN_PRO_CREDITS", "200"))
    },
    "enterprise": {
        "code": "enterprise",
        "price": int(os.getenv("PLAN_ENT_PRICE", "499")),
        "credits": int(os.getenv("PLAN_ENT_CREDITS", "5000"))
    }
}

async def ensure_seed_plans():
    """Seed default plans if they don't exist"""
    for code, plan_data in DEFAULT_PLANS.items():
        await plans.update_one(
            {"code": code},
            {"$setOnInsert": plan_data},
            upsert=True
        )
    logger.info("Plans seeded/verified")

async def get_user(user_id: str) -> dict:
    """Get user document"""
    return await users.find_one(get_user_query(user_id))

async def set_user_tier(user_id: str, tier: str):
    """Update user tier"""
    await users.update_one(
        get_user_query(user_id),
        {"$set": {"tier": tier}}
    )
    logger.info(f"User {user_id} tier set to {tier}")

async def add_credits(user_id: str, delta: int, reason: str, meta: Optional[Dict[str, Any]] = None) -> int:
    """
    Add or remove credits from user account
    Returns new balance
    """
    # Update user credits
    result = await users.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$inc": {"credits": delta}},
        return_document=True
    )
    
    balance = int(result.get("credits", 0)) if result else 0
    
    # Log to ledger (immutable audit trail)
    from audit_immutability import insert_strict
    await insert_strict(ledger, {
        "userId": str(user_id),
        "delta": delta,
        "reason": reason,
        "balanceAfter": balance,
        "timestamp": datetime.utcnow(),
        "meta": meta or {}
    })
    
    logger.info(f"Credits adjusted for user {user_id}: delta={delta}, balance={balance}, reason={reason}")
    
    return balance

async def consume_credits(user_id: str, amount: int, reason: str) -> int:
    """
    Consume credits (debit)
    Raises ValueError if insufficient credits
    Returns new balance
    """
    user_doc = await users.find_one({"_id": ObjectId(user_id)})
    current_balance = int(user_doc.get("credits", 0)) if user_doc else 0
    
    if current_balance < amount:
        logger.warning(f"Insufficient credits for user {user_id}: need={amount}, have={current_balance}")
        raise ValueError("INSUFFICIENT_CREDITS")
    
    return await add_credits(user_id, -amount, reason)

async def create_subscription(user_id: str, plan_code: str, provider: str, provider_sub_id: str):
    """
    Create or update subscription for user
    Grants tier and refills monthly credits
    """
    # Get plan details
    plan_doc = await plans.find_one({"code": plan_code})
    if not plan_doc:
        plan_doc = DEFAULT_PLANS.get(plan_code, DEFAULT_PLANS["basic"])
    
    # Calculate renewal date (30 days from now)
    renew_date = datetime.utcnow() + timedelta(days=30)
    
    # Update or create subscription
    await subscriptions.update_one(
        {"userId": str(user_id)},
        {"$set": {
            "userId": str(user_id),
            "plan": plan_code,
            "provider": provider,
            "providerSubId": provider_sub_id,
            "renewsAt": renew_date,
            "createdAt": datetime.utcnow()
        }},
        upsert=True
    )
    
    # Set user tier
    tier = "enterprise" if plan_code == "enterprise" else ("pro" if plan_code == "pro" else "basic")
    await set_user_tier(user_id, tier)
    
    # Grant monthly credits
    await add_credits(
        user_id,
        plan_doc["credits"],
        f"Monthly refill ({plan_code})",
        {"plan": plan_code, "subscription_id": provider_sub_id}
    )
    
    logger.info(f"Subscription created for user {user_id}: plan={plan_code}, renews={renew_date}")
    
    return plan_doc, renew_date

async def apply_credit_purchase(user_id: str, credits: int, provider: str, provider_tx_id: str) -> int:
    """
    Apply one-time credit purchase
    Returns new balance
    """
    balance = await add_credits(
        user_id,
        credits,
        "Credits purchase",
        {"provider": provider, "transaction_id": provider_tx_id}
    )
    
    logger.info(f"Credit purchase applied for user {user_id}: credits={credits}, balance={balance}")
    
    return balance

async def get_billing_state(user_id: str) -> dict:
    """
    Get complete billing state for user
    """
    # Get user data
    user_doc = await users.find_one(
        {"_id": ObjectId(user_id)},
        {"tier": 1, "credits": 1, "email": 1}
    )
    
    if not user_doc:
        return {
            "tier": "basic",
            "credits": 0,
            "renewsAt": None,
            "subscriptionId": None,
            "provider": None,
            "history": []
        }
    
    # Get subscription data
    sub_doc = await subscriptions.find_one({"userId": str(user_id)})
    
    # Get recent transaction history
    history_cursor = ledger.find({"userId": str(user_id)}).sort("timestamp", -1).limit(20)
    history = await history_cursor.to_list(length=20)
    
    # Convert ObjectIds to strings for JSON serialization
    for h in history:
        h["_id"] = str(h["_id"])
        if isinstance(h.get("timestamp"), datetime):
            h["ts"] = h["timestamp"].isoformat()
    
    return {
        "tier": user_doc.get("tier", "basic"),
        "credits": int(user_doc.get("credits", 0)),
        "renewsAt": sub_doc.get("renewsAt").isoformat() if sub_doc and sub_doc.get("renewsAt") else None,
        "subscriptionId": sub_doc.get("providerSubId") if sub_doc else None,
        "provider": sub_doc.get("provider") if sub_doc else None,
        "history": history
    }

async def get_all_plans() -> list:
    """Get all plan configurations (admin)"""
    await ensure_seed_plans()
    plans_cursor = plans.find({}, {"_id": 0}).sort("code", 1)
    return await plans_cursor.to_list(length=None)

async def upsert_plan(code: str, price: int, credits: int):
    """Update or create plan (admin)"""
    await plans.update_one(
        {"code": code},
        {"$set": {"price": price, "credits": credits}},
        upsert=True
    )
    logger.info(f"Plan updated: code={code}, price={price}, credits={credits}")
