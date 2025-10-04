from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query
from typing import List, Optional
from datetime import datetime
from ..services.auth_service import verify_session_jwt, SessionData
from ..services.market_data_service import market_data_service
from ..models.market_data_dto import (
    CandleDataDTO, CandleInterval, WebSocketStatusDTO, SubscriptionRequest
)
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

async def require_auth(request: Request):
    data = verify_session_jwt(request.cookies.get("app_session"))
    if not data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return data

@router.post("/market-data/start")
async def start_market_data_collection(
    x_upstox_access_token: str = Header(alias="X-Upstox-Access-Token"),
    session: SessionData = Depends(require_auth)
):
    """Start WebSocket connection and market data collection for selected instruments"""
    try:
        success = await market_data_service.start_data_collection(x_upstox_access_token)
        
        if success:
            return {"status": "ok", "message": "Market data collection started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start market data collection")
            
    except Exception as e:
        logger.error(f"Error starting market data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market-data/stop")
async def stop_market_data_collection(
    session: SessionData = Depends(require_auth)
):
    """Stop market data collection and close WebSocket connection"""
    try:
        success = await market_data_service.stop_data_collection()
        
        if success:
            return {"status": "ok", "message": "Market data collection stopped"}
        else:
            raise HTTPException(status_code=500, detail="Failed to stop market data collection")
            
    except Exception as e:
        logger.error(f"Error stopping market data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/status", response_model=WebSocketStatusDTO)
async def get_market_data_status(
    session: SessionData = Depends(require_auth)
):
    """Get current WebSocket connection and data collection status"""
    return market_data_service.get_websocket_status()

@router.get("/market-data/collection-status")
async def get_collection_status(
    session: SessionData = Depends(require_auth)
):
    """Get data collection status"""
    ws_status = market_data_service.get_websocket_status()
    is_collecting = market_data_service.is_data_collection_active()
    
    return {
        "is_collecting": is_collecting,
        "is_connected": ws_status.is_connected,
        "subscribed_instruments_count": len(ws_status.subscribed_instruments),
        "total_ticks_received": ws_status.total_ticks_received,
        "connection_time": ws_status.connection_time,
        "last_heartbeat": ws_status.last_heartbeat,
        "recent_errors": ws_status.errors
    }

@router.post("/market-data/subscribe")
async def subscribe_to_instruments(
    subscription_request: SubscriptionRequest,
    session: SessionData = Depends(require_auth)
):
    """Subscribe to additional instruments for market data"""
    try:
        await market_data_service.add_instruments_to_collection(
            subscription_request.instrument_keys
        )
        
        return {
            "status": "ok", 
            "message": f"Subscribed to {len(subscription_request.instrument_keys)} instruments"
        }
        
    except Exception as e:
        logger.error(f"Error subscribing to instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market-data/unsubscribe")
async def unsubscribe_from_instruments(
    instrument_keys: List[str],
    session: SessionData = Depends(require_auth)
):
    """Unsubscribe from instruments"""
    try:
        await market_data_service.remove_instruments_from_collection(instrument_keys)
        
        return {
            "status": "ok",
            "message": f"Unsubscribed from {len(instrument_keys)} instruments"
        }
        
    except Exception as e:
        logger.error(f"Error unsubscribing from instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/candles/{instrument_key}", response_model=List[CandleDataDTO])
async def get_candles(
    instrument_key: str,
    interval: CandleInterval = Query(CandleInterval.ONE_MINUTE),
    start_time: Optional[str] = Query(None, description="ISO format datetime"),
    end_time: Optional[str] = Query(None, description="ISO format datetime"),
    limit: int = Query(100, description="Maximum number of candles"),
    session: SessionData = Depends(require_auth)
):
    """Get historical candle data for an instrument"""
    try:
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        
        candles = await market_data_service.get_candles(
            instrument_key=instrument_key,
            interval=interval,
            start_time=start_dt,
            end_time=end_dt,
            limit=limit
        )
        
        return candles
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {e}")
    except Exception as e:
        logger.error(f"Error getting candles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/candles")
async def get_candles_for_selected_instruments(
    interval: CandleInterval = Query(CandleInterval.ONE_MINUTE),
    limit: int = Query(10, description="Number of candles per instrument"),
    session: SessionData = Depends(require_auth)
):
    """Get latest candles for all selected instruments"""
    try:
        # Get selected instruments
        from ..services.instrument_service import instrument_service
        selected_instruments = await instrument_service.get_selected_instruments()
        
        if not selected_instruments:
            return {"instruments": [], "message": "No instruments selected"}
        
        results = {}
        for instrument in selected_instruments:
            candles = await market_data_service.get_candles(
                instrument_key=instrument.instrument_key,
                interval=interval,
                limit=limit
            )
            results[instrument.instrument_key] = {
                "symbol": instrument.symbol,
                "candles": candles
            }
        
        return {
            "interval": interval.value,
            "instruments": results,
            "total_instruments": len(selected_instruments)
        }
        
    except Exception as e:
        logger.error(f"Error getting candles for selected instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/live-prices")
async def get_live_prices(
    session: SessionData = Depends(require_auth)
):
    """Get latest prices for selected instruments"""
    try:
        # Get selected instruments
        from ..services.instrument_service import instrument_service
        selected_instruments = await instrument_service.get_selected_instruments()
        
        if not selected_instruments:
            return {"prices": [], "message": "No instruments selected"}
        
        prices = {}
        for instrument in selected_instruments:
            # Get latest 1-minute candle as current price
            latest_candles = await market_data_service.get_candles(
                instrument_key=instrument.instrument_key,
                interval=CandleInterval.ONE_MINUTE,
                limit=1
            )
            
            if latest_candles:
                candle = latest_candles[0]
                prices[instrument.instrument_key] = {
                    "symbol": instrument.symbol,
                    "ltp": candle.close_price,
                    "open": candle.open_price,
                    "high": candle.high_price,
                    "low": candle.low_price,
                    "volume": candle.volume,
                    "timestamp": candle.timestamp.isoformat(),
                    "change": candle.close_price - candle.open_price,
                    "change_percent": ((candle.close_price - candle.open_price) / candle.open_price * 100) if candle.open_price > 0 else 0
                }
            else:
                prices[instrument.instrument_key] = {
                    "symbol": instrument.symbol,
                    "ltp": 0,
                    "message": "No recent data available"
                }
        
        return {
            "prices": prices,
            "total_instruments": len(selected_instruments),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting live prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))