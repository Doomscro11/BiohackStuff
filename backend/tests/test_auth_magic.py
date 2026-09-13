"""Regression tests for the auth magic-code fixes.

Covers:
- send_otp_email now performs real SMTP delivery (and fails closed when SMTP
  is not configured / delivery errors).
- magic/request enforces a resend cooldown.
"""

import asyncio
from unittest import mock

import pytest


# --- SMTP sender tests -----------------------------------------------------


def test_send_otp_email_blocking_builds_and_sends():
    """Delivery should send exactly one message with the OTP and a subject."""
    from routes_auth import _send_otp_email_blocking
    from email import message_from_string

    sent = {}

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            sent["host"] = args[0]
            sent["kwargs"] = kwargs

        def starttls(self):
            sent["starttls"] = True

        def login(self, user, pwd):
            sent["login"] = (user, pwd)

        def sendmail(self, sender, recipients, message):
            sent["sender"] = sender
            sent["recipients"] = recipients
            sent["message"] = message

        def quit(self):
            sent["quit"] = True

    with mock.patch.dict("os.environ", {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "user@example.com",
        "SMTP_PASSWORD": "s3cret",
        "SMTP_FROM": "noreply@example.com",
        "SMTP_USE_TLS": "true",
        "SMTP_USE_SSL": "false",
    }):
        with mock.patch("routes_auth.smtplib.SMTP", FakeSMTP):
            _send_otp_email_blocking("dev@example.com", "123456")

    # Decode the MIME payload the way a mail client would
    msg = message_from_string(sent["message"])
    payload = msg.get_payload(decode=True).decode("utf-8")

    assert "123456" in payload
    assert "verification code" in payload.lower()
    assert "verification code" in msg["Subject"].lower()
    assert sent["host"] == "smtp.example.com"
    assert sent["login"] == ("user@example.com", "s3cret")
    assert sent["recipients"] == ["dev@example.com"]
    assert sent.get("starttls") is True
    assert sent.get("quit") is True


def test_send_otp_email_blocking_fails_closed_when_smtp_unconfigured():
    """Without SMTP_HOST the sender must raise, not silently succeed."""
    from routes_auth import _send_otp_email_blocking

    with mock.patch.dict("os.environ", {}, clear=True):
        with pytest.raises(RuntimeError, match="SMTP_HOST is not configured"):
            _send_otp_email_blocking("dev@example.com", "123456")


def test_send_otp_email_blocking_uses_ssl_when_configured():
    """SMTP_USE_SSL=true should use SMTP_SSL, not plain SMTP."""
    from routes_auth import _send_otp_email_blocking

    used_ssl = {}

    class FakeSMTPSSL:
        def __init__(self, *args, **kwargs):
            used_ssl["args"] = args

        def login(self, user, pwd):
            pass

        def sendmail(self, sender, recipients, message):
            pass

        def quit(self):
            pass

    with mock.patch.dict("os.environ", {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_USE_SSL": "true",
        "SMTP_USE_TLS": "false",
    }):
        with mock.patch("routes_auth.smtplib.SMTP_SSL", FakeSMTPSSL):
            _send_otp_email_blocking("dev@example.com", "123456")

    assert used_ssl["args"][0] == "smtp.example.com"


@pytest.mark.asyncio
async def test_send_otp_email_awaits_delivery_and_returns_true():
    """send_otp_email should run the blocking sender and report success."""
    from routes_auth import send_otp_email

    with mock.patch("routes_auth._send_otp_email_blocking") as blocking:
        result = await send_otp_email("dev@example.com", "123456")
    blocking.assert_called_once_with("dev@example.com", "123456")
    assert result is True


@pytest.mark.asyncio
async def test_send_otp_email_propagates_delivery_failure():
    """A failed delivery should surface as an exception to the caller."""
    from routes_auth import send_otp_email

    with mock.patch(
        "routes_auth._send_otp_email_blocking",
        side_effect=RuntimeError("SMTP down"),
    ):
        with pytest.raises(RuntimeError, match="SMTP down"):
            await send_otp_email("dev@example.com", "123456")


# --- Resend cooldown tests -------------------------------------------------


def test_is_resend_too_soon_false_with_no_recent_code():
    """A user with no prior code request is not rate-limited."""
    from routes_auth import is_resend_too_soon

    async def run():
        return await is_resend_too_soon("dev@example.com")

    fake_count = mock.AsyncMock(return_value=0)
    with mock.patch("routes_auth.magic_codes_collection") as mc:
        mc.count_documents = fake_count
        assert asyncio.run(run()) is False
    fake_count.assert_awaited_once()


def test_is_resend_too_soon_true_with_recent_code():
    """A code requested within the cooldown window should be blocked."""
    from routes_auth import is_resend_too_soon

    async def run():
        return await is_resend_too_soon("dev@example.com")

    fake_count = mock.AsyncMock(return_value=1)
    with mock.patch("routes_auth.magic_codes_collection") as mc:
        mc.count_documents = fake_count
        assert asyncio.run(run()) is True