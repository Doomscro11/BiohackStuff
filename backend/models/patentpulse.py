"""
PatentPulse Pydantic Models & Validators
Enforces data quality rules and schema consistency
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
import hashlib


class DataQualityError(Exception):
    """Raised when a patent item fails data quality validation"""
    pass


class PatentItemInput(BaseModel):
    """Input model for raw patent data from sources"""
    patent_id: str = Field(..., min_length=5, max_length=50)
    source: Literal["USPTO", "WIPO", "LENS"]
    title: str = Field(..., min_length=10, max_length=500)
    assignee: str = Field(..., max_length=200)
    country: Literal["US", "CA", "JP", "EP", "WO"]
    status: Literal["Expired", "Lapsed", "ExpiringSoon"]
    expiry_date: datetime
    keywords: List[str] = Field(default_factory=list, max_length=20)
    sequence_data: Optional[str] = None
    commercial_score: float = Field(..., ge=0.0, le=1.0)
    synthesis_score: float = Field(..., ge=0.0, le=1.0)
    fto_risk: float = Field(..., ge=0.0, le=1.0)
    repurpose_notes: str = Field(..., max_length=1000)
    last_seen_at: datetime
    source_payload: dict = Field(default_factory=dict)  # Original payload for hash
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @field_validator('expiry_date')
    @classmethod
    def validate_expiry_date(cls, v, info):
        """Validate expiry date based on status"""
        status = info.data.get('status')
        now = datetime.utcnow()
        
        if status in ["Expired", "Lapsed"]:
            if v >= now:
                raise ValueError(f"Expiry date must be in the past for {status} patents")
        elif status == "ExpiringSoon":
            # Must expire within 24 months
            if v <= now or (v - now).days > 730:
                raise ValueError("ExpiringSoon patents must expire within 24 months from now")
        
        return v
    
    @field_validator('sequence_data')
    @classmethod
    def validate_sequence(cls, v):
        """Validate amino acid sequence format"""
        if v is None or v == "":
            return None
        
        # Check 3-letter format: Ala-Glu-Gly-...
        if '-' in v:
            parts = v.split('-')
            if not (8 <= len(parts) <= 25):
                raise ValueError(f"Sequence length must be 8-25 amino acids, got {len(parts)}")
            
            # Validate each part is 3 letters
            for part in parts:
                if len(part) != 3 or not part[0].isupper() or not part[1:].islower():
                    raise ValueError(f"Invalid amino acid format: {part}")
        else:
            # Single-letter format: AEGKLM...
            if not (8 <= len(v) <= 25):
                raise ValueError(f"Sequence length must be 8-25 amino acids, got {len(v)}")
            
            valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
            if not all(c in valid_aa for c in v):
                raise ValueError(f"Invalid amino acid characters in sequence")
        
        return v
    
    def compute_source_hash(self) -> str:
        """Compute stable hash of source content for change detection"""
        # Hash key fields that indicate content change
        content = f"{self.title}|{self.assignee}|{self.expiry_date.isoformat()}|{self.sequence_data or ''}"
        content += f"|{self.commercial_score}|{self.synthesis_score}|{self.fto_risk}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class PatentItemDB(BaseModel):
    """Database model for patentpulse_items collection"""
    patent_id: str
    source: str
    title: str
    assignee: str
    country: str
    status: str
    expiry_date: datetime
    keywords: List[str]
    sequence_data: Optional[str]
    commercial_score: float
    synthesis_score: float
    fto_risk: float
    repurpose_notes: str
    last_seen_at: datetime
    first_ingested_at: datetime
    last_ingested_at: datetime
    source_hash: str
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class RunMetadata(BaseModel):
    """Metadata for a collector run"""
    run_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    mode: Literal["dry-run", "live"]
    sources: List[str]
    params: dict
    counts: dict = Field(default_factory=lambda: {
        "fetched": 0,
        "normalized": 0,
        "upserts": 0,
        "updates": 0,
        "unchanged": 0,
        "rejected": 0,
        "dlq": 0,
        "duplicates": 0
    })
    errors: List[dict] = Field(default_factory=list)
    status: Literal["running", "success", "partial", "failed"] = "running"
    slo: dict = Field(default_factory=dict)
    notes: str = ""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class DLQEntry(BaseModel):
    """Dead Letter Queue entry for failed items"""
    patent_id: Optional[str] = None
    source: str
    payload: dict
    reason: str
    retries: int = 0
    first_failed_at: datetime
    last_failed_at: datetime
    last_error: str
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
