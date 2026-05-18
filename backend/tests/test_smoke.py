"""Backend smoke tests for release-gate stabilization."""


def test_jwt_module_imports():
    from auth.jwt import sign_jwt, verify_jwt, extract_user_from_payload

    token = sign_jwt({
        "sub": "smoke-user",
        "email": "smoke@example.com",
        "role": "researcher",
        "orgId": "default",
    })
    payload = verify_jwt(token)
    user = extract_user_from_payload(payload)

    assert user["id"] == "smoke-user"
    assert user["email"] == "smoke@example.com"
    assert user["role"] == "researcher"


def test_chemistry_service_basic_options():
    from services import chemistry_service

    result = chemistry_service.get_chemistry_options("basic")

    assert result["tier"] == "basic"
    assert isinstance(result["mods"], list)
    assert isinstance(result["exclusions"], list)


def test_partner_share_token_round_trip():
    from datetime import datetime, timezone, timedelta
    from services import partner_share_service

    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    token = partner_share_service.generate_share_token(
        "share-smoke",
        "file-smoke",
        expires_at,
    )
    verified = partner_share_service.verify_share_token(token)

    assert verified is not None
    assert verified["share_id"] == "share-smoke"
    assert verified["file_id"] == "file-smoke"
