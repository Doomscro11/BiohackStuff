# Admin User Management Routes for Peptimancer
import os
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from middleware.auth import get_current_user, require_role
from models import AdjustCreditsBody, SetTierBody, UserSummary

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]

# Collections
users_collection = db['users']
credits_ledger_collection = db['credits_ledger']

# Router
router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])

def _to_user_summary(doc) -> dict:
    """Convert MongoDB user document to UserSummary"""
    return {
        "id": str(doc["_id"]),
        "email": doc.get("email", ""),
        "role": doc.get("role", "researcher"),
        "tier": doc.get("tier", "basic"),
        "credits": int(doc.get("credits", 0)),
        "lastLogin": doc.get("lastLogin")
    }

@router.get("")
async def list_users(user=Depends(get_current_user)):
    """
    List all users with their tier and credits information
    Requires: admin role
    """
    # RBAC check
    require_role(user, ["admin"])
    
    try:
        # Fetch users (limited to 200 for performance)
        cursor = users_collection.find(
            {},
            {"email": 1, "role": 1, "tier": 1, "credits": 1, "lastLogin": 1}
        ).limit(200)
        
        users = await cursor.to_list(length=200)
        
        return {
            "items": [_to_user_summary(u) for u in users]
        }
    
    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )

@router.post("/adjust-credits")
async def adjust_credits(body: AdjustCreditsBody, user=Depends(get_current_user)):
    """
    Adjust user credits (add or subtract)
    Requires: admin role
    """
    # RBAC check
    require_role(user, ["admin"])
    
    # Validate userId
    try:
        oid = ObjectId(body.userId)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid userId format"
        )
    
    try:
        # Update user credits
        result = await users_collection.find_one_and_update(
            {"_id": oid},
            {"$inc": {"credits": body.delta}},
            return_document=True
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        new_balance = int(result.get("credits", 0))
        
        # Log to credits ledger
        await credits_ledger_collection.insert_one({
            "userId": str(oid),
            "delta": body.delta,
            "reason": body.reason,
            "balanceAfter": new_balance,
            "timestamp": datetime.utcnow(),
            "adjustedBy": user.get("email", "admin")
        })
        
        logger.info(f"Admin {user.get('email')} adjusted credits for user {body.userId}: delta={body.delta}, reason={body.reason}")
        
        return {
            "ok": True,
            "balance": new_balance
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to adjust credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to adjust credits: {str(e)}"
        )

@router.post("/set-tier")
async def set_tier(body: SetTierBody, user=Depends(get_current_user)):
    """
    Set user tier (basic, pro, enterprise, admin)
    Requires: admin role
    """
    # RBAC check
    require_role(user, ["admin"])
    
    # Validate tier
    if body.tier not in {"basic", "pro", "enterprise", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tier. Must be one of: basic, pro, enterprise, admin"
        )
    
    # Validate userId
    try:
        oid = ObjectId(body.userId)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid userId format"
        )
    
    try:
        # Update user tier
        result = await users_collection.find_one_and_update(
            {"_id": oid},
            {"$set": {"tier": body.tier}},
            return_document=True
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"Admin {user.get('email')} set tier for user {body.userId} to {body.tier}")
        
        return {
            "ok": True,
            "tier": result.get("tier")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set tier: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set tier: {str(e)}"
        )
