"""Shared backend model exports.

This package-level module prevents import shadowing between the legacy
`backend/models.py` module and the `backend/models/` package.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class AdjustCreditsBody(BaseModel):
    userId: str
    delta: int
    reason: str = Field(min_length=2, max_length=80)


class SetTierBody(BaseModel):
    userId: str
    tier: str


class UserSummary(BaseModel):
    id: str
    email: EmailStr
    role: str
    tier: str
    credits: int
    lastLogin: Optional[datetime] = None


class PlanUpsert(BaseModel):
    code: str = Field(pattern=r"^(basic|pro|enterprise)$")
    price: int = Field(ge=0)
    credits: int = Field(ge=0)


class CheckoutBody(BaseModel):
    plan: Optional[str] = Field(None, pattern=r"^(basic|pro|enterprise)$")
    purchase_credits: Optional[int] = Field(None, ge=10)


class BillingState(BaseModel):
    tier: str
    credits: int
    renewsAt: Optional[datetime] = None
    subscriptionId: Optional[str] = None
    provider: Optional[str] = None
    history: list = []


class CreditDebit(BaseModel):
    amount: int = Field(gt=0)
    reason: str = Field(min_length=2, max_length=120)


__all__ = [
    "AdjustCreditsBody",
    "SetTierBody",
    "UserSummary",
    "PlanUpsert",
    "CheckoutBody",
    "BillingState",
    "CreditDebit",
]
