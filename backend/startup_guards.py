"""Startup guards that prevent running in unsafe configurations.

Each guard raises RuntimeError with a clear message if the condition
is violated, so the process fails closed at boot time.
"""

import os
import logging

logger = logging.getLogger(__name__)


def check_demo_otp_in_production() -> None:
    """Fail if ENABLE_DEMO_OTP=true when ENV=production.

    Demo OTP returns the one-time code in the API response body, bypassing
    real SMTP delivery. In production this would leak authentication tokens
    and must never be enabled.
    """
    env = os.environ.get("ENV", "development").strip().lower()
    raw = os.environ.get("ENABLE_DEMO_OTP", "false").strip().lower()
    demo_otp_enabled = raw in ("1", "true", "yes", "y", "on")

    if demo_otp_enabled and env == "production":
        raise RuntimeError(
            "ENABLE_DEMO_OTP is true but ENV is production. "
            "Demo OTP leaks authentication codes in the API response. "
            "Set ENABLE_DEMO_OTP=false for production deployments."
        )

    if demo_otp_enabled:
        logger.warning(
            "ENABLE_DEMO_OTP=true — authentication codes are returned in "
            "the API response body. This is safe for development/CI but "
            "must be false in production."
        )


def run_all() -> None:
    """Run every registered startup guard."""
    check_demo_otp_in_production()