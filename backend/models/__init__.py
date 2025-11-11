"""
Models package for Peptimancer
Exports models from both legacy models.py and new models/ directory
"""

# Import from legacy models.py for backward compatibility
# We need to import directly from the file to avoid circular imports
import sys
import importlib.util
from pathlib import Path

# Load models.py directly
models_path = Path(__file__).parent.parent / "models.py"
spec = importlib.util.spec_from_file_location("legacy_models", models_path)
legacy_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_models)

# Import classes from legacy models
AdjustCreditsBody = legacy_models.AdjustCreditsBody
SetTierBody = legacy_models.SetTierBody
UserSummary = legacy_models.UserSummary
PlanUpsert = legacy_models.PlanUpsert
CheckoutBody = legacy_models.CheckoutBody
BillingState = legacy_models.BillingState
CreditDebit = legacy_models.CreditDebit

# Import from new models directory
from .patentpulse import *
from .market_signals import *
from .reclaim_pack import *
from .partner_share import *

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
