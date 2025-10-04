import os, time, jwt
from typing import Optional, TypedDict

APP_JWT_SECRET = os.getenv("APP_JWT_SECRET", "dev-secret-change")

class SessionData(TypedDict, total=False):
    user_id: str
    iat: int
    exp: int

def create_session_jwt(payload: dict, ttl_seconds: int = 60*60*18) -> str:
    now = int(time.time())
    body = {**payload, "iat": now, "exp": now + ttl_seconds}
    return jwt.encode(body, APP_JWT_SECRET, algorithm="HS256")

def verify_session_jwt(token: Optional[str]) -> Optional[SessionData]:
    if not token:
        return None
    try:
        data = jwt.decode(token, APP_JWT_SECRET, algorithms=["HS256"])
        return data  # type: ignore
    except Exception:
        return None
