"""
PatentPulse Normalizer (Phase IXc)
Normalizes raw patent data from different sources into canonical PatentItemInput
Enforces data quality rules and computes scores
"""

import logging
import hashlib
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from models.patentpulse import PatentItemInput, DataQualityError

logger = logging.getLogger(__name__)


def derive_patent_id(source: str, raw: Dict[str, Any]) -> str:
    """
    Derive stable patent_id from raw data
    Priority: explicit id > family id > composite hash
    """
    # USPTO
    if source == "USPTO":
        return raw.get("patent_number", "")
    
    # WIPO
    elif source == "WIPO":
        return raw.get("application_id", "")
    
    # LENS
    elif source == "LENS":
        return raw.get("lens_id", "")
    
    # Fallback: generate composite hash
    title = raw.get("title", "")
    assignee = raw.get("assignee_name") or raw.get("applicant") or raw.get("owners", "")
    composite = f"{source}|{title[:50]}|{assignee}"
    return f"{source}_{hashlib.md5(composite.encode()).hexdigest()[:12]}"


def compute_source_hash(raw: Dict[str, Any]) -> str:
    """
    Compute stable hash of raw patent content
    Used for change detection (idempotency)
    """
    # Extract key fields
    title = raw.get("title", "")
    abstract = raw.get("abstract", "")
    expiry = raw.get("expiry_date", "")
    
    content = f"{title}|{abstract[:200]}|{expiry}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def normalize_country(raw: Dict[str, Any]) -> str:
    """
    Normalize country code to standard format
    Returns one of: US, CA, JP, EP, WO
    """
    country = raw.get("country") or raw.get("country_code") or raw.get("jurisdiction", "US")
    country = country.upper()
    
    # Map to canonical codes
    if country in ["US", "USA"]:
        return "US"
    elif country in ["CA", "CAN"]:
        return "CA"
    elif country in ["JP", "JPN"]:
        return "JP"
    elif country in ["EP", "EPO"]:
        return "EP"
    elif country in ["WO", "PCT"]:
        return "WO"
    else:
        # Default to US if unknown
        logger.warning(f"Unknown country code: {country}, defaulting to US")
        return "US"


def normalize_status(raw: Dict[str, Any]) -> str:
    """
    Normalize patent status to canonical format
    Returns one of: Expired, Lapsed, ExpiringSoon
    """
    status = raw.get("status") or raw.get("legal_status", "Expired")
    status_lower = status.lower()
    
    if "expiring" in status_lower or "active" in status_lower:
        return "ExpiringSoon"
    elif "lapsed" in status_lower or "abandoned" in status_lower:
        return "Lapsed"
    else:
        return "Expired"


def compute_scores(item: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute commercial, synthesis, and FTO risk scores
    In production, this would use ML models or heuristics
    For MVP, generates realistic scores based on data
    """
    # Base scores with some variance
    commercial_score = random.uniform(0.4, 0.9)
    synthesis_score = random.uniform(0.2, 0.7)
    fto_risk = random.uniform(0.1, 0.5)
    
    # Adjust based on presence of sequence data (higher commercial value)
    if item.get("sequence_data"):
        commercial_score += 0.05
    
    # Adjust based on status (ExpiringSoon = higher risk)
    if item.get("status") == "ExpiringSoon":
        fto_risk += 0.15
    
    # Clamp to [0, 1]
    commercial_score = max(0.0, min(1.0, commercial_score))
    synthesis_score = max(0.0, min(1.0, synthesis_score))
    fto_risk = max(0.0, min(1.0, fto_risk))
    
    return {
        "commercial_score": round(commercial_score, 3),
        "synthesis_score": round(synthesis_score, 3),
        "fto_risk": round(fto_risk, 3)
    }


def normalize_item(source: str, raw: Dict[str, Any]) -> PatentItemInput:
    """
    Normalize raw patent data into PatentItemInput
    
    Args:
        source: Source name (USPTO, WIPO, LENS)
        raw: Raw patent data from adapter
    
    Returns:
        PatentItemInput with validated data
    
    Raises:
        DataQualityError if data fails validation
    """
    try:
        # Derive patent_id
        patent_id = derive_patent_id(source, raw)
        if not patent_id or len(patent_id) < 5:
            raise DataQualityError(f"Invalid patent_id: {patent_id}")
        
        # Extract and normalize fields
        title = raw.get("title") or "Untitled Patent"
        if len(title) < 10:
            raise DataQualityError(f"Title too short: {title}")
        
        # Assignee (multiple possible fields)
        assignee = raw.get("assignee_name") or raw.get("applicant") or raw.get("owners") or "Unknown"
        
        # Country
        country = normalize_country(raw)
        
        # Status
        status = normalize_status(raw)
        
        # Expiry date
        expiry_str = raw.get("expiry_date")
        if not expiry_str:
            raise DataQualityError("Missing expiry_date")
        
        if isinstance(expiry_str, datetime):
            expiry_date = expiry_str
        else:
            expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
        
        # Keywords (extract from title/abstract if not provided)
        keywords = raw.get("keywords", [])
        if not keywords:
            # Simple keyword extraction from title
            title_lower = title.lower()
            keyword_candidates = ["peptide", "glp-1", "insulin", "analog", "therapeutic", "formulation"]
            keywords = [kw for kw in keyword_candidates if kw in title_lower]
        
        # Sequence data
        sequence_data = raw.get("sequence_data")
        
        # Compute scores
        scores = compute_scores({**raw, "status": status, "sequence_data": sequence_data})
        
        # Repurpose notes
        repurpose_notes = raw.get("repurpose_notes") or "Potential for commercial repurposing post-expiry."
        
        # Create PatentItemInput
        item = PatentItemInput(
            patent_id=patent_id,
            source=source,
            title=title[:500],  # Truncate to max length
            assignee=assignee[:200],
            country=country,
            status=status,
            expiry_date=expiry_date,
            keywords=keywords[:20],  # Max 20 keywords
            sequence_data=sequence_data,
            commercial_score=scores["commercial_score"],
            synthesis_score=scores["synthesis_score"],
            fto_risk=scores["fto_risk"],
            repurpose_notes=repurpose_notes[:1000],
            last_seen_at=datetime.now(timezone.utc),
            source_payload=raw
        )
        
        return item
    
    except Exception as e:
        logger.error(f"Normalization failed for {source}: {e}")
        raise DataQualityError(f"Normalization error: {str(e)}")


def fix_trivial_violations(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Attempt to fix trivial data quality violations
    Returns fixed item or None if unfixable
    """
    try:
        # Fix missing title
        if not item.get("title") or len(item["title"]) < 10:
            item["title"] = "Patent Composition (Title Missing)"
        
        # Fix missing assignee
        if not item.get("assignee"):
            item["assignee"] = "Unknown Assignee"
        
        # Fix empty keywords
        if not item.get("keywords"):
            item["keywords"] = ["biotech", "pharma"]
        
        return item
    except:
        return None
