"""Tests for startup guards in server boot path."""

import pytest

from startup_guards import check_demo_otp_in_production


def test_demo_otp_blocked_in_production():
    """Must fail closed when ENABLE_DEMO_OTP is true and ENV is production."""
    import os
    os.environ["ENV"] = "production"
    os.environ["ENABLE_DEMO_OTP"] = "true"
    with pytest.raises(RuntimeError, match="ENABLE_DEMO_OTP is true but ENV is production"):
        check_demo_otp_in_production()


def test_demo_otp_allowed_in_development():
    """Must pass when ENABLE_DEMO_OTP is true and ENV is development."""
    import os
    os.environ["ENV"] = "development"
    os.environ["ENABLE_DEMO_OTP"] = "true"
    # Should not raise
    check_demo_otp_in_production()


def test_demo_otp_allowed_in_ci():
    """Must pass when ENABLE_DEMO_OTP is true and CI env var is set."""
    import os
    os.environ["ENV"] = "production"
    os.environ["ENABLE_DEMO_OTP"] = "false"
    # Should not raise
    check_demo_otp_in_production()


def test_demo_otp_defaults_to_disabled():
    """Must pass when ENABLE_DEMO_OTP is not set even in any env."""
    import os
    os.environ["ENV"] = "production"
    os.environ.pop("ENABLE_DEMO_OTP", None)
    check_demo_otp_in_production()