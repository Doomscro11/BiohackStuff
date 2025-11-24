# Credit Package Definitions for Peptimancer
# Centralized pricing for one-time credit purchases

CREDIT_PACKAGES = {
    "credits_100": {
        "id": "credits_100",
        "credits": 100,
        "price_usd": 5.00,
        "price_cents": 500,
        "display_name": "100 Credits Pack",
        "popular": False
    },
    "credits_250": {
        "id": "credits_250",
        "credits": 250,
        "price_usd": 12.00,
        "price_cents": 1200,
        "display_name": "250 Credits Pack",
        "popular": True
    },
    "credits_500": {
        "id": "credits_500",
        "credits": 500,
        "price_usd": 20.00,
        "price_cents": 2000,
        "display_name": "500 Credits Pack",
        "popular": False
    },
    "credits_1000": {
        "id": "credits_1000",
        "credits": 1000,
        "price_usd": 35.00,
        "price_cents": 3500,
        "display_name": "1000 Credits Pack",
        "popular": False
    }
}

def get_package(package_id: str):
    """Get package by ID, returns None if not found"""
    return CREDIT_PACKAGES.get(package_id)

def get_all_packages():
    """Get all available packages"""
    return list(CREDIT_PACKAGES.values())
