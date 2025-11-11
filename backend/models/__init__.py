"""
Models package for Peptimancer
Exports models from both legacy models.py and new models/ directory
"""

# Import from legacy models.py for backward compatibility
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import AdjustCreditsBody, SetTierBody, UserSummary

# Import from new models directory
from models.patentpulse import *
from models.market_signals import *
from models.reclaim_pack import *
from models.partner_share import *

__all__ = [
    # Legacy models
    'AdjustCreditsBody',
    'SetTierBody',
    'UserSummary',
    # PatentPulse models
    'PatentPulseItem',
    'PatentFamily',
    'ClaimsSnapshot',
    'FTOSnapshot',
    # Market signals models
    'MarketSignal',
    'CommercialBreakdown',
    # Reclaim pack models
    'ReclaimPackRequest',
    'ReclaimPackItem',
    # Partner share models
    'PartnerShare',
    'SharePolicy',
    'ShareCreationRequest',
    'ShareRotationResult',
]
