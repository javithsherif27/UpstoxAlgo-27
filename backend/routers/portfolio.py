from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request

from ..services.auth_service import verify_session_jwt, SessionData
from ..services.portfolio_service import portfolio_service


router = APIRouter()


async def require_auth(request: Request) -> SessionData:
    data = verify_session_jwt(request.cookies.get("app_session"))
    if not data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return data


def require_token(x_upstox_access_token: Optional[str] = Header(None)) -> str:
    if not x_upstox_access_token:
        raise HTTPException(status_code=401, detail="Missing X-Upstox-Access-Token")
    return x_upstox_access_token


@router.get("/api/portfolio/holdings")
async def get_holdings_endpoint(
    _session: SessionData = Depends(require_auth),
    x_upstox_access_token: str | None = Header(default=None, alias="X-Upstox-Access-Token"),
):
    holdings = portfolio_service.get_holdings()
    if not holdings and x_upstox_access_token:
        await portfolio_service.refresh_rest(x_upstox_access_token)
        holdings = portfolio_service.get_holdings()
    return {"holdings": holdings}


@router.get("/api/portfolio/positions")
async def get_positions_endpoint(
    _session: SessionData = Depends(require_auth),
    x_upstox_access_token: str | None = Header(default=None, alias="X-Upstox-Access-Token"),
):
    positions = portfolio_service.get_positions()
    if not positions and x_upstox_access_token:
        await portfolio_service.refresh_rest(x_upstox_access_token)
        positions = portfolio_service.get_positions()
    return {"positions": positions}


@router.post("/api/portfolio/stream/start")
async def start_portfolio_stream(token: str = Depends(require_token), _session: SessionData = Depends(require_auth)):
    await portfolio_service.start_stream(token)
    return {"ok": True}


@router.post("/api/portfolio/stream/stop")
async def stop_portfolio_stream(_session: SessionData = Depends(require_auth)):
    await portfolio_service.stop_stream()
    return {"ok": True}


@router.get("/api/portfolio/stream/status")
async def portfolio_stream_status(_session: SessionData = Depends(require_auth)):
    return portfolio_service.get_status()
