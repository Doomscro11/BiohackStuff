"""
Market Signals Models (Phase IXd)
Simplified models for API responses and enricher logic
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class MarketFactorCalculation(BaseModel):
    """Result of market factor calculation"""
    market_factor: float = Field(..., ge=0.0, le=1.0)
    search_index: Optional[float] = None
    availability_score: Optional[float] = None
    dispersion_norm: Optional[float] = None
    sentiment: Optional[float] = None
    market_velocity: Optional[float] = None


class ScoreAdjustmentResult(BaseModel):
    """Result of commercial score adjustment"""
    base_score: float
    market_factor: float
    adjusted_score: float
    delta: float
    clamped: bool  # True if floor clamp was applied
    weights: Dict[str, float]
