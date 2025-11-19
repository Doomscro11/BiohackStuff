"""
Chemistry Service
Handles chemistry options and tier-based filtering logic
"""

import logging
from typing import List, Dict, Any, Optional

from constants.chemistry import MODIFICATIONS, EXCLUSIONS

logger = logging.getLogger(__name__)


def get_chemistry_options(tier: str = 'basic') -> Dict[str, Any]:
    """
    Get chemistry options filtered by user tier
    
    Args:
        tier: User tier (basic, pro, enterprise)
        
    Returns:
        Dict with 'modifications' and 'exclusions' lists
    """
    tier = tier.lower()
    
    # Filter modifications by tier
    filtered_mods = [
        mod for mod in MODIFICATIONS
        if _tier_allows_access(tier, mod.get('tier', 'basic'))
    ]
    
    # Filter exclusions by tier
    filtered_exclusions = [
        excl for excl in EXCLUSIONS
        if _tier_allows_access(tier, excl.get('tier', 'basic'))
    ]
    
    logger.info(f"Chemistry options for tier '{tier}': {len(filtered_mods)} mods, {len(filtered_exclusions)} exclusions")
    
    return {
        'modifications': filtered_mods,
        'exclusions': filtered_exclusions
    }


def _tier_allows_access(user_tier: str, required_tier: str) -> bool:
    """
    Check if user tier allows access to feature
    
    Tier hierarchy: basic < pro < enterprise
    """
    tier_order = {
        'basic': 0,
        'pro': 1,
        'enterprise': 2
    }
    
    user_level = tier_order.get(user_tier.lower(), 0)
    required_level = tier_order.get(required_tier.lower(), 0)
    
    return user_level >= required_level


def validate_modification_selection(
    modifications: List[str],
    user_tier: str = 'basic'
) -> Dict[str, Any]:
    """
    Validate that selected modifications are allowed for user tier
    
    Returns:
        Dict with 'valid' (bool) and optional 'denied_mods' (list)
    """
    chemistry_options = get_chemistry_options(user_tier)
    allowed_mod_ids = {mod['id'] for mod in chemistry_options['modifications']}
    
    denied_mods = [mod for mod in modifications if mod not in allowed_mod_ids]
    
    if denied_mods:
        return {
            'valid': False,
            'denied_mods': denied_mods,
            'message': f"Modifications not allowed for tier '{user_tier}': {', '.join(denied_mods)}"
        }
    
    return {'valid': True}


def validate_exclusion_selection(
    exclusions: List[str],
    user_tier: str = 'basic'
) -> Dict[str, Any]:
    """
    Validate that selected exclusions are allowed for user tier
    
    Returns:
        Dict with 'valid' (bool) and optional 'denied_exclusions' (list)
    """
    chemistry_options = get_chemistry_options(user_tier)
    allowed_excl_ids = {excl['id'] for excl in chemistry_options['exclusions']}
    
    denied_exclusions = [excl for excl in exclusions if excl not in allowed_excl_ids]
    
    if denied_exclusions:
        return {
            'valid': False,
            'denied_exclusions': denied_exclusions,
            'message': f"Exclusions not allowed for tier '{user_tier}': {', '.join(denied_exclusions)}"
        }
    
    return {'valid': True}


def get_modification_by_id(mod_id: str) -> Optional[Dict[str, Any]]:
    """Get modification details by ID"""
    for mod in MODIFICATIONS:
        if mod['id'] == mod_id:
            return mod
    return None


def get_exclusion_by_id(excl_id: str) -> Optional[Dict[str, Any]]:
    """Get exclusion details by ID"""
    for excl in EXCLUSIONS:
        if excl['id'] == excl_id:
            return excl
    return None
