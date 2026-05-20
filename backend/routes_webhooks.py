# Webhook Routes - Stripe Events for Peptimancer
import logging
from fastapi import APIRouter, Request, HTTPException, status
from billing.adapters import get_billing
from billing.service import create_subscription, apply_credit_purchase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

@router.post("/billing/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    Processes checkout completions, subscription updates, etc.
    """
    try:
        bill = get_billing()
        
        # Get request body and signature
        body = await request.body()
        signature = request.headers.get("stripe-signature", "")
        
        # Parse and verify webhook
        if hasattr(bill, 'parse_webhook'):
            if signature:  # Real Stripe
                event = bill.parse_webhook(body, signature)
            else:  # Mock mode
                event = bill.parse_webhook(request)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook parsing not supported"
            )
        
    except Exception as e:
        logger.error(f"Webhook parsing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook parse error: {str(e)}"
        )
    
    # Process event
    event_type = event.get("type")
    data = event.get("data", {})
    
    logger.info(f"Processing webhook event: type={event_type}")
    
    try:
        if event_type == "checkout.session.completed":
            # Phase VIII: Resolve user from session_id
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ.get('DB_NAME', 'peptimancer_db')]
            
            # Try to get session_id
            session_id = data.get("id") or request.query_params.get("sid")
            
            if session_id:
                # Look up user from session mapping
                session_doc = await db.checkout_sessions.find_one({"session_id": session_id})
                if session_doc:
                    user_id = session_doc["user_id"]
                    plan = session_doc.get("plan")
                    
                    # Try package_id first, fallback to direct credits
                    package_id = session_doc.get("package_id")
                    if package_id:
                        from billing.credit_packages import get_package
                        package = get_package(package_id)
                        credits = package["credits"] if package else 0
                    else:
                        credits = session_doc.get("purchase_credits", 0)
                else:
                    # Fallback: try query params or metadata
                    user_id = request.query_params.get("uid")
                    if data.get("metadata"):
                        user_id = data["metadata"].get("user_id", user_id)
                        plan = data["metadata"].get("plan")
                        
                        # Check for package_id in metadata
                        package_id = data["metadata"].get("package_id")
                        if package_id:
                            from billing.credit_packages import get_package
                            package = get_package(package_id)
                            credits = package["credits"] if package else 0
                        else:
                            credits = int(data["metadata"].get("credits", 0))
                    else:
                        plan = None
                        credits = 0
            else:
                user_id = None
            
            if not user_id:
                logger.warning("Checkout completed but no user_id found")
                return {"ok": True, "warning": "No user_id"}
            
            # Process plan subscription
            if plan and plan in ["basic", "pro", "enterprise"]:
                provider_id = data.get("id", "demo_sub")
                await create_subscription(user_id, plan, "stripe", provider_id)
                logger.info(f"Subscription created for user {user_id}: plan={plan}")
            
            # Process credit purchase
            if credits and credits > 0:
                provider_id = data.get("id", "demo_tx")
                await apply_credit_purchase(user_id, int(credits), "stripe", provider_id)
                logger.info(f"Credits purchased for user {user_id}: credits={credits}")
        
        elif event_type == "customer.subscription.deleted":
            # Handle subscription cancellation
            logger.info(f"Subscription deleted: {data.get('id')}")
            # Could downgrade user to basic tier here
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )

@router.get("/billing/mock/success")
async def mock_success(request: Request):
    """
    Mock billing success page - simulates Stripe webhook and redirects
    
    **Usage Examples:**
    
    1. Upgrade to Pro:
       GET /api/webhooks/billing/mock/success?uid=<USER_ID>&plan=pro
       - Sets tier to "pro"
       - Grants 200 monthly credits
       - Creates subscription with renewal date
    
    2. Purchase Credits:
       GET /api/webhooks/billing/mock/success?uid=<USER_ID>&credits=100
       - Adds 100 credits to balance
       - Creates ledger entry
    
    3. Upgrade + Credits:
       GET /api/webhooks/billing/mock/success?uid=<USER_ID>&plan=enterprise&credits=50
       - Upgrades to enterprise tier (5000 monthly credits)
       - Adds bonus 50 credits
    
    **Testing Flow:**
    1. Get your user_id from /api/auth/session
    2. Visit mock URL with your user_id
    3. Redirects to /billing?success=1
    4. Credits badge updates within 5 seconds
    5. Chemistry UI shows upgraded tier options
    
    **Environment:**
    - Works in BILLING_PROVIDER=mock mode
    - No actual payment processing
    - Instant tier/credit changes
    """
    import os
    from fastapi.responses import RedirectResponse
    
    # Extract parameters
    user_id = request.query_params.get("uid")
    plan = request.query_params.get("plan")
    credits = int(request.query_params.get("credits", "0") or "0")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing uid parameter"
        )
    
    try:
        # Process subscription
        if plan and plan in ["basic", "pro", "enterprise"]:
            await create_subscription(user_id, plan, "mock", f"mock_sub_{user_id}")
            logger.info(f"Mock subscription created: user={user_id}, plan={plan}")
        
        # Process credit purchase
        if credits > 0:
            await apply_credit_purchase(user_id, credits, "mock", f"mock_tx_{user_id}")
            logger.info(f"Mock credits purchased: user={user_id}, credits={credits}")
        
        # Redirect to billing page with success flag
        app_url = os.getenv("APP_URL", "http://localhost:3000")
        redirect_url = f"{app_url}/billing?success=1"
        
        logger.info(f"Mock payment complete, redirecting to: {redirect_url}")
        
        return RedirectResponse(
            url=redirect_url,
            status_code=302
        )
    
    except Exception as e:
        logger.error(f"Mock payment processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
