"""
Reclaim Pack Export Models (Phase IXe)
Models for PatentPulse export generation and tracking
"""

from datetime import datetime, timezone
from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field


class ExportCriteria(BaseModel):
    """Criteria used for export generation"""
    limit: int = 10
    status_filter: Optional[List[str]] = None
    country_filter: Optional[str] = None
    min_viability_score: float = 0.0
    sort_by: str = "viability_score"
    
    class Config:
        arbitrary_types_allowed = True


class PatentExportItem(BaseModel):
    """Individual patent item in export"""
    patent_id: str
    title: str
    assignee: str
    country: str
    status: str
    expiry_date: str
    commercial_score: float
    commercial_score_adj: Optional[float] = None
    fto_risk: float
    synthesis_score: float
    market_factor: Optional[float] = None
    viability_score: float
    repurpose_notes: str
    
    class Config:
        arbitrary_types_allowed = True


class ReclaimPackExport(BaseModel):
    """Reclaim Pack export metadata"""
    file_id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    file_name: str
    format: Literal["pdf", "json"]
    criteria: Dict[str, Any]
    count: int
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    viability_avg: float
    top_country: str
    created_by: Optional[str] = None
    file_path: str
    size_kb: int = 0
    
    class Config:
        arbitrary_types_allowed = True


class ReclaimPackData(BaseModel):
    """Complete reclaim pack data structure"""
    metadata: Dict[str, Any]
    summary: Dict[str, Any]
    items: List[PatentExportItem]
    totals: Dict[str, int]
    disclaimer: str
    
    class Config:
        arbitrary_types_allowed = True
