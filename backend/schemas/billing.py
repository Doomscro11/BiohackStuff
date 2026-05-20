"""
Billing API Schemas
Request/response models for billing operations
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PlanUpsert(BaseModel):
    """Request body for creating/updating a billing plan"""
    code: str = Field(pattern=r"^(basic|pro|enterprise)$")
    price: int = Field(ge=0)  # USD monthly
    credits: int = Field(ge=0)


class CheckoutBody(BaseModel):
    """Request body for initiating checkout"""
    plan: Optional[str] = Field(None, pattern=r"^(basic|pro|enterprise)$")
    purchase_credits: Optional[int] = Field(None, ge=10)


class BillingState(BaseModel):
    """Response model for user's billing state"""
    tier: str
    credits: int
    renewsAt: Optional[datetime] = None
    subscriptionId: Optional[str] = None
    provider: Optional[str] = None
    history: list = []


class CreditDebit(BaseModel):
    """Request body for credit debit operations"""
    amount: int = Field(gt=0)
    reason: str = Field(min_length=2, max_length=120)
