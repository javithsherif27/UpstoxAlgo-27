from fastapi import APIRouter, Depends, Header, HTTPException, Request
from ..services.auth_service import verify_session_jwt, SessionData
from ..services.upstox_client import get_profile
from ..models.dto import ProfileDTO

router = APIRouter()

async def require_auth(request: Request):
    data = verify_session_jwt(request.cookies.get("app_session"))
    if not data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return data

@router.get("/profile", response_model=ProfileDTO)
async def profile(x_upstox_access_token: str = Header(alias="X-Upstox-Access-Token"), session: SessionData = Depends(require_auth)):
    return await get_profile(x_upstox_access_token)
