from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query

from ..services.aggregator_service import aggregator_service
from ..services.market_data_service import market_data_service
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def require_token(x_upstox_access_token: Optional[str] = Header(None)) -> str:
    if not x_upstox_access_token:
        raise HTTPException(status_code=401, detail="Missing X-Upstox-Access-Token")
    return x_upstox_access_token


@router.post("/api/stream/start")
async def stream_start(payload: dict, token: str = Depends(require_token)):
    symbols: List[str] = payload.get("symbols") or []
    exchange: str = payload.get("exchange") or "NSE"
    if not symbols:
        raise HTTPException(status_code=400, detail="symbols required")
    
    # Start both aggregator service (legacy) and market data service (new)
    aggregator_result = await aggregator_service.start_stream(symbols, exchange, token)
    market_data_result = await market_data_service.start_data_collection(token)
    
    return {
        "aggregator": aggregator_result,
        "market_data": market_data_result,
        "status": "started" if market_data_result else "partial_failure"
    }


@router.post("/api/stream/stop")
async def stream_stop():
    aggregator_result = await aggregator_service.stop_stream()
    market_data_result = await market_data_service.stop_data_collection()
    
    return {
        "aggregator": aggregator_result,
        "market_data": market_data_result,
        "status": "stopped"
    }


@router.get("/api/candles")
async def get_candles(symbol: str = Query(...), timeframe: str = Query(...), limit: int = Query(300)):
    return {"candles": [c.__dict__ for c in aggregator_service.get_candles(symbol, timeframe, limit)]}


@router.post("/api/stream/ping")
async def stream_ping():
    # Lightweight health data for now
    return {"ok": True}

@router.get("/api/stream/status")
async def stream_status():
    """Get detailed status of market data collection"""
    return {
        "test": "working",
        "status": "ok"
    }


@router.post("/api/stream/recover")
async def stream_recover(payload: dict, token: str = Depends(require_token)):
    symbol: str = payload.get("symbol")
    since_ts: Optional[str] = payload.get("sinceTs")
    if not symbol or not since_ts:
        raise HTTPException(status_code=400, detail="symbol and sinceTs required")
    from datetime import datetime
    from ..utils.time_service import IST
    ts = datetime.fromisoformat(since_ts).astimezone(IST)
    await aggregator_service.recover_gaps(symbol, ts)
    return {"ok": True}
