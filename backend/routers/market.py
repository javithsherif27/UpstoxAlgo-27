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
    """Get candles for TradingView chart - bridges to market_data_service database"""
    try:
        # First try aggregator service (for live streaming data)
        agg_candles = aggregator_service.get_candles(symbol, timeframe, limit)
        if agg_candles:
            return {"candles": [c.__dict__ for c in agg_candles]}
        
        # Fallback to database candles via market_data_service
        from ..services.instrument_service import instrument_service
        from ..models.market_data_dto import CandleInterval
        
        # Find instrument by symbol
        selected_instruments = await instrument_service.get_selected_instruments()
        instrument = None
        for inst in selected_instruments:
            if inst.symbol == symbol:
                instrument = inst
                break
        
        if not instrument:
            logger.warning(f"Instrument not found for symbol: {symbol}")
            return {"candles": []}
        
        # Map timeframe to our interval enum
        interval_map = {
            "1m": CandleInterval.ONE_MINUTE,
            "5m": CandleInterval.FIVE_MINUTE,
            "15m": CandleInterval.FIFTEEN_MINUTE,
            "1h": CandleInterval.ONE_MINUTE,  # Fallback to 1m for 1h
            "1d": CandleInterval.ONE_DAY
        }
        
        interval = interval_map.get(timeframe, CandleInterval.ONE_DAY)
        
        # Get candles from database
        db_candles = await market_data_service.get_candles(
            instrument_key=instrument.instrument_key,
            interval=interval,
            limit=limit
        )
        
        # Convert to format expected by TradingView
        candles = []
        for candle in reversed(db_candles):  # Reverse to get chronological order
            candles.append({
                "start": candle.timestamp.isoformat(),
                "o": candle.open_price,
                "h": candle.high_price,
                "l": candle.low_price,
                "c": candle.close_price,
                "v": candle.volume
            })
        
        logger.info(f"Returning {len(candles)} candles for {symbol} ({timeframe})")
        return {"candles": candles}
        
    except Exception as e:
        logger.error(f"Error getting candles for {symbol}: {e}")
        return {"candles": []}


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
