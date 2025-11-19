"""
Models package for Peptimancer
Persistence-layer models for database operations

Note: For DTOs/schemas, import from schemas/ package
For backward compatibility, we re-export schemas here
"""

# Import persistence models from models directory
from .patentpulse import (
    PatentItemInput,
    PatentItemDB,
    CommercialBreakdown as PatentCommercialBreakdown,
    RunMetadata,
    DLQEntry,
    MarketSignalFeatures,
    MarketSignalProvenance,
    PatentMarketSignal
)
from .market_signals import MarketSignal, CommercialBreakdown
from .reclaim_pack import (
    ExportCriteria,
    PatentExportItem,
    ReclaimPackExport,
    ReclaimPackData
)
from .partner_share import (
    SharePolicy,
    PartnerShare,
    PartnerShareEvent
)

# Re-export schemas for backward compatibility
# This allows existing code to import from models
try:
    from schemas import (
        AdjustCreditsBody,
        SetTierBody,
        UserSummary,
        PlanUpsert,
        CheckoutBody,
        BillingState,
        CreditDebit,
        ShareCreationRequest,
        ShareRotationResult
    )
except ImportError:
    # Fallback to legacy models.py if schemas not available yet
    import importlib.util
    from pathlib import Path
    
    models_path = Path(__file__).parent.parent / "models.py"
    spec = importlib.util.spec_from_file_location("legacy_models", models_path)
    legacy_models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_models)
    
    AdjustCreditsBody = legacy_models.AdjustCreditsBody
    SetTierBody = legacy_models.SetTierBody
    UserSummary = legacy_models.UserSummary
    PlanUpsert = legacy_models.PlanUpsert
    CheckoutBody = legacy_models.CheckoutBody
    BillingState = legacy_models.BillingState
    CreditDebit = legacy_models.CreditDebit
    ShareCreationRequest = None
    ShareRotationResult = None

__all__ = [
    # PatentPulse persistence models
    'PatentItemInput',
    'PatentItemDB',
    'PatentCommercialBreakdown',
    'RunMetadata',
    'DLQEntry',
    'MarketSignalFeatures',
    'MarketSignalProvenance',
    'PatentMarketSignal',
    # Market signals
    'MarketSignal',
    'CommercialBreakdown',
    # Reclaim pack models
    'ExportCriteria',
    'PatentExportItem',
    'ReclaimPackExport',
    'ReclaimPackData',
    # Partner share models
    'PartnerShare',
    'SharePolicy',
    'PartnerShareEvent',
    # Re-exported schemas (for backward compatibility)
    'AdjustCreditsBody',
    'SetTierBody',
    'UserSummary',
    'PlanUpsert',
    'CheckoutBody',
    'BillingState',
    'CreditDebit',
    'ShareCreationRequest',
    'ShareRotationResult',
]
