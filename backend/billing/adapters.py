# Billing Adapters - Stripe + Mock for Peptimancer
import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

MODE = os.getenv("BILLING_PROVIDER", "mock").lower() or "mock"

@dataclass
class CheckoutResult:
    provider: str
    url: str
    session_id: str

class MockBilling:
    """Mock billing adapter for testing without Stripe"""
    
    def create_checkout(self, user_id: str, email: str, plan: str = None, purchase_credits: int = None) -> CheckoutResult:
        """Create a mock checkout session"""
        sid = f"mock_{user_id}"
        url = f"/billing/mock/success?sid={sid}&plan={plan or ''}&credits={purchase_credits or 0}&uid={user_id}"
        logger.info(f"Mock checkout created for user {user_id}: plan={plan}, credits={purchase_credits}")
        return CheckoutResult(provider="mock", url=url, session_id=sid)

    def parse_webhook(self, request) -> Dict[str, Any]:
        """Parse mock webhook event"""
        # In mock, return a sample event dict from query params
        return {
            "type": "checkout.session.completed",
            "data": {
                "plan": request.query_params.get("plan"),
                "credits": int(request.query_params.get("credits", "0")),
                "id": request.query_params.get("sid", "mock_tx")
            }
        }

# Try to import Stripe
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False
    logger.warning("Stripe library not installed - only mock billing available")

class StripeBilling:
    """Stripe billing adapter for production"""
    
    def __init__(self):
        if not STRIPE_AVAILABLE:
            raise RuntimeError("Stripe library not installed")
        
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.pub_key = os.getenv("STRIPE_PUBLIC_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not stripe.api_key:
            raise RuntimeError("STRIPE_SECRET_KEY not configured")
        
        logger.info("Stripe billing adapter initialized")

    def create_checkout(self, user_id: str, email: str, plan: str = None, purchase_credits: int = None) -> CheckoutResult:
        """Create a Stripe Checkout session"""
        line_items = []
        mode = "payment"  # Default for one-time purchases
        
        if plan:
            # Subscription mode for plans
            mode = "subscription"
            # In production, use pre-created price IDs with lookup_key
            # For demo, we create dynamic prices
            plan_prices = {
                "basic": int(os.getenv("PLAN_BASIC_PRICE", "0")),
                "pro": int(os.getenv("PLAN_PRO_PRICE", "49")),
                "enterprise": int(os.getenv("PLAN_ENT_PRICE", "499"))
            }
            
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "recurring": {"interval": "month"},
                    "product_data": {"name": f"Peptimancer {plan.capitalize()} Plan"},
                    "unit_amount": plan_prices.get(plan, 0) * 100  # Convert to cents
                },
                "quantity": 1
            })
        
        if purchase_credits:
            # One-time credit purchase
            # Simple pricing: $0.05 per credit, minimum $5
            unit_amount = max(500, purchase_credits * 5)  # cents
            
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Peptimancer Credits ({purchase_credits})"},
                    "unit_amount": unit_amount
                },
                "quantity": 1
            })
        
        app_url = os.getenv("APP_URL", "http://localhost:3000")
        
        session = stripe.checkout.Session.create(
            mode=mode,
            line_items=line_items,
            success_url=f"{app_url}/app/settings/billing?success=1&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{app_url}/app/settings/billing?canceled=1",
            customer_email=email,
            metadata={
                "user_id": user_id,
                "plan": plan or "",
                "credits": str(purchase_credits or 0)
            }
        )
        
        logger.info(f"Stripe checkout created for user {user_id}: session_id={session.id}")
        
        return CheckoutResult(
            provider="stripe",
            url=session.url,
            session_id=session.id
        )

    def parse_webhook(self, request_body: bytes, signature: str) -> Dict[str, Any]:
        """Parse and verify Stripe webhook event"""
        try:
            event = stripe.Webhook.construct_event(
                request_body,
                signature,
                self.webhook_secret
            )
            
            logger.info(f"Stripe webhook received: type={event['type']}")
            
            return {
                "type": event["type"],
                "data": event.get("data", {}).get("object", {})
            }
        except Exception as e:
            logger.error(f"Stripe webhook verification failed: {e}")
            raise

def get_billing():
    """Get the appropriate billing adapter based on configuration"""
    if MODE == "stripe" and STRIPE_AVAILABLE:
        return StripeBilling()
    return MockBilling()
