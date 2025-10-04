from fastapi import APIRouter, Response, Depends, HTTPException
from pydantic import BaseModel
from ..services.auth_service import create_session_jwt

class LoginRequest(BaseModel):
    user_id: str

router = APIRouter()

COOKIE_NAME = "app_session"

@router.post("/login")
async def login(req: LoginRequest, response: Response):
    token = create_session_jwt({"user_id": req.user_id})
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # False for localhost development
        samesite="lax",
        path="/",
        max_age=60*60*18,
    )
    return {"status": "ok"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "ok"}
