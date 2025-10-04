import pytest
import respx
from httpx import Response
from backend.services.upstox_client import get_profile

@respx.mock
@pytest.mark.asyncio
async def test_get_profile_nested_format():
    # Test typical Upstox API response with nested data
    mock_response = {
        "status": "success",
        "data": {
            "user_name": "John Doe",
            "user_id": "CLIENT123",
            "is_active": True
        }
    }
    respx.get("https://api.upstox.com/v2/user/profile").mock(return_value=Response(200, json=mock_response))
    data = await get_profile("token123")
    assert data["name"] == "John Doe"
    assert data["client_id"] == "CLIENT123"
    assert data["kyc_status"] == "ACTIVE"

@respx.mock
@pytest.mark.asyncio
async def test_get_profile_direct_format():
    # Test direct format for backward compatibility
    respx.get("https://api.upstox.com/v2/user/profile").mock(return_value=Response(200, json={"name":"Test","client_id":"CID","kyc_status":"VERIFIED"}))
    data = await get_profile("token123")
    assert data["client_id"] == "CID"
