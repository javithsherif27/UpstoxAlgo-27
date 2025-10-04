from ..services.auth_service import create_session_jwt, verify_session_jwt

def test_jwt_roundtrip():
    token = create_session_jwt({"user_id": "abc"}, ttl_seconds=60)
    data = verify_session_jwt(token)
    assert data and data["user_id"] == "abc"
