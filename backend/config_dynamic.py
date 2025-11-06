# Dynamic Runtime Configuration for Peptimancer Enterprise
import os
from typing import Dict, Any

# Default configuration values from environment
DEFAULTS = {
    "integrationsMode": os.getenv("INTEGRATIONS_MODE", "sandbox"),  # mock, sandbox, live
    "demoMode": os.getenv("DEMO_MODE", "false").lower() == "true",
    "watermarkExports": os.getenv("WATERMARK_EXPORTS", "true").lower() == "true",
    "croEnabled": os.getenv("CRO_ENABLED", "true").lower() == "true",
    "billingEnabled": os.getenv("BILLING_ENABLED", "true").lower() == "true",
    "rateLimitDemo": int(os.getenv("RATE_LIMIT_DEMO", "10")),
    "rateLimitLive": int(os.getenv("RATE_LIMIT_LIVE", "100")),
    "maxAnalogues": int(os.getenv("MAX_ANALOGUES", "10")),
    "enterpriseFeatures": os.getenv("ENTERPRISE_FEATURES", "true").lower() == "true",
    "auditLogging": os.getenv("AUDIT_LOGGING", "true").lower() == "true"
}

# Allowed values for validation
ALLOWED_MODES = {"mock", "sandbox", "live"}

# Configuration schema for validation
CONFIG_SCHEMA = {
    "integrationsMode": {"type": str, "allowed": ALLOWED_MODES},
    "demoMode": {"type": bool},
    "watermarkExports": {"type": bool},
    "croEnabled": {"type": bool},
    "billingEnabled": {"type": bool},
    "rateLimitDemo": {"type": int, "min": 1, "max": 1000},
    "rateLimitLive": {"type": int, "min": 1, "max": 10000},
    "maxAnalogues": {"type": int, "min": 1, "max": 20},
    "enterpriseFeatures": {"type": bool},
    "auditLogging": {"type": bool}
}

def validate_config_update(updates: Dict[str, Any]) -> None:
    """Validate configuration updates against schema"""
    for key, value in updates.items():
        if key not in CONFIG_SCHEMA:
            raise ValueError(f"Unknown configuration key: {key}")
        
        schema = CONFIG_SCHEMA[key]
        
        # Type validation
        if not isinstance(value, schema["type"]):
            raise ValueError(f"Invalid type for {key}: expected {schema['type'].__name__}")
        
        # Value validation
        if "allowed" in schema and value not in schema["allowed"]:
            raise ValueError(f"Invalid value for {key}: must be one of {schema['allowed']}")
        
        if "min" in schema and value < schema["min"]:
            raise ValueError(f"Invalid value for {key}: must be >= {schema['min']}")
        
        if "max" in schema and value > schema["max"]:
            raise ValueError(f"Invalid value for {key}: must be <= {schema['max']}")

def get_mode_display(mode: str) -> Dict[str, Any]:
    """Get display information for integration mode"""
    mode_info = {
        "mock": {
            "name": "Mock Mode",
            "description": "All integrations use mock responses - safe for development",
            "color": "green",
            "features": ["No external API calls", "Predictable responses", "No costs incurred"]
        },
        "sandbox": {
            "name": "Sandbox Mode", 
            "description": "Test integrations with sandbox endpoints - safe for testing",
            "color": "yellow",
            "features": ["Sandbox API endpoints", "Test data only", "Limited functionality"]
        },
        "live": {
            "name": "Live Mode",
            "description": "Production integrations with real endpoints - use with caution",
            "color": "red",
            "features": ["Production API calls", "Real data processing", "Costs may apply"]
        }
    }
    return mode_info.get(mode, {"name": mode, "description": "Unknown mode", "color": "gray", "features": []})