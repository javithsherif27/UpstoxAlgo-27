from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query
from typing import List, Optional
from datetime import datetime
from ..services.auth_service import verify_session_jwt, SessionData
from ..services.market_data_service import market_data_service
from ..models.market_data_dto import (
    CandleDataDTO, CandleInterval, WebSocketStatusDTO, SubscriptionRequest, FetchHistoricalRequest
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

@router.post("/market-data/fetch-historical")
async def fetch_historical_data(
    # Query parameters for easier testing
    symbol: str = Query("BYKE", description="Stock symbol (default: BYKE)"),
    days_back: int = Query(30, description="Number of days back from today (default: 30)"),
    interval: str = Query("1DAY", description="Candle interval"),
    from_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    # JSON body as alternative (optional)
    request: FetchHistoricalRequest = None
    # session: SessionData = Depends(require_auth)  # Temporarily disabled for testing
):
    """
    Fetch historical candle data from Upstox API and store in database
    Accepts either JSON body or query parameters for convenience
    """
    try:
        from ..services.upstox_client import upstox_client
        from ..services.instrument_service import instrument_service
        from datetime import datetime, timedelta
        
        # Handle both JSON body and query parameters - prioritize query parameters
        logger.info(f"Received parameters: symbol={symbol}, days_back={days_back}, interval={interval}, from_date={from_date}, to_date={to_date}")
        logger.info(f"Request body: {request}")
        
        # Use query parameters if provided, otherwise fall back to request body
        if symbol:
            # Use query parameters
            req_symbol = symbol
            req_interval = interval
            if days_back:
                # Calculate dates from days_back
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                req_from_date = start_date.strftime("%Y-%m-%d")
                req_to_date = end_date.strftime("%Y-%m-%d")
            else:
                req_from_date = from_date
                req_to_date = to_date
        elif request:
            # Use JSON body
            req_symbol = request.symbol
            req_interval = request.interval
            req_from_date = request.from_date
            req_to_date = request.to_date
        else:
            # Neither provided
            req_symbol = None
            req_interval = interval
            req_from_date = from_date
            req_to_date = to_date
        
        # Validate required parameters
        if not req_symbol:
            return {"status": "error", "message": "Symbol is required"}
        if not req_from_date or not req_to_date:
            return {"status": "error", "message": "from_date and to_date are required (or use days_back)"}
        
        logger.info(f"Fetching historical data for {req_symbol} from {req_from_date} to {req_to_date}")
        
        # Get instrument key for the symbol
        instruments = await instrument_service.get_all_instruments()
        instrument = None
        for inst in instruments:
            if inst.symbol == req_symbol:
                instrument = inst
                break
        
        if not instrument:
            logger.warning(f"Instrument not found for symbol: {req_symbol}, using mock instrument for testing")
            # Create a mock instrument for testing purposes
            from ..models.dto import InstrumentDTO
            instrument = InstrumentDTO(
                instrument_key=f"NSE_EQ|{req_symbol}",  # Mock instrument key
                symbol=req_symbol,
                name=f"{req_symbol} Limited",
                exchange="NSE",
                tradingsymbol=req_symbol
            )
        
        # Fetch historical data from Upstox API
        if req_interval == "1DAY":
            historical_data = await upstox_client.get_historical_candles(
                instrument_key=instrument.instrument_key,
                interval="day",
                from_date=req_from_date,
                to_date=req_to_date
            )
        else:
            # For intraday intervals
            historical_data = await upstox_client.get_intraday_candles(
                instrument_key=instrument.instrument_key,
                interval=req_interval.lower(),
                from_date=req_from_date,
                to_date=req_to_date
            )
        
        if not historical_data or "data" not in historical_data:
            return {"status": "error", "message": "No historical data received from Upstox API"}
        
        # Store candles in database
        candles_stored = 0
        for candle_data in historical_data["data"]["candles"]:
            try:
                # Parse Upstox candle format: [timestamp, open, high, low, close, volume, open_interest]
                timestamp_str = candle_data[0]
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                candle_dto = CandleDataDTO(
                    instrument_key=instrument.instrument_key,
                    symbol=instrument.symbol,
                    interval=CandleInterval.ONE_DAY if req_interval == "1DAY" else CandleInterval.ONE_MINUTE,
                    timestamp=timestamp,
                    open_price=float(candle_data[1]),
                    high_price=float(candle_data[2]),
                    low_price=float(candle_data[3]),
                    close_price=float(candle_data[4]),
                    volume=int(candle_data[5]) if candle_data[5] else 0,
                    open_interest=int(candle_data[6]) if len(candle_data) > 6 and candle_data[6] else None,
                    tick_count=0
                )
                
                await market_data_service.store_candle_data(candle_dto)
                candles_stored += 1
                
            except Exception as candle_error:
                logger.warning(f"Error storing candle: {candle_error}")
                continue
        
        return {
            "status": "success",
            "message": f"Fetched and stored {candles_stored} candles for {req_symbol}",
            "symbol": req_symbol,
            "interval": req_interval,
            "candles_stored": candles_stored,
            "from_date": req_from_date,
            "to_date": req_to_date
        }
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/market-data/live-prices")
async def get_live_prices(
    session: SessionData = Depends(require_auth)
):
    """Get latest prices from real-time WebSocket tick data for selected instruments"""
    try:
        # Get selected instruments
        from ..services.instrument_service import instrument_service
        selected_instruments = await instrument_service.get_selected_instruments()
        
        if not selected_instruments:
            return {"prices": {}, "message": "No instruments selected"}
        
        # Get instrument keys
        instrument_keys = [inst.instrument_key for inst in selected_instruments]
        
        # Get latest tick data from WebSocket
        latest_ticks = await market_data_service.get_latest_ticks(instrument_keys)
        
        # If no live tick data available, fall back to candle data
        if not latest_ticks:
            logger.warning("No live tick data available, falling back to candle data")
            prices = {}
            for instrument in selected_instruments:
                # Prefer latest 1-minute candle, else 5m, else 15m
                candle = None
                for interval in (CandleInterval.ONE_MINUTE, CandleInterval.FIVE_MINUTE, CandleInterval.FIFTEEN_MINUTE):
                    latest = await market_data_service.get_candles(
                        instrument_key=instrument.instrument_key,
                        interval=interval,
                        limit=1
                    )
                    if latest:
                        candle = latest[0]
                        break

                if candle:
                    prices[instrument.instrument_key] = {
                        "symbol": instrument.symbol,
                        "ltp": candle.close_price,
                        "open": candle.open_price,
                        "high": candle.high_price,
                        "low": candle.low_price,
                        "volume": candle.volume,
                        "timestamp": candle.timestamp.isoformat(),
                        "change": candle.close_price - candle.open_price,
                        "change_percent": ((candle.close_price - candle.open_price) / candle.open_price * 100) if candle.open_price > 0 else 0,
                        "source": "candle"
                    }
                else:
                    # No candle data available - need to fetch historical data
                    prices[instrument.instrument_key] = {
                        "symbol": instrument.symbol,
                        "ltp": 0,
                        "open": 0,
                        "high": 0,
                        "low": 0,
                        "volume": 0,
                        "change": 0,
                        "change_percent": 0,
                        "message": "No historical data available - fetch required",
                        "source": "none"
                    }
        else:
            # Use live tick data
            prices = {}
            for instrument_key, tick_data in latest_ticks.items():
                prices[instrument_key] = {
                    **tick_data,
                    "source": "websocket"
                }
        
        return {
            "prices": prices,
            "total_instruments": len(selected_instruments),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting live prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))