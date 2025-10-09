from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query
from typing import List, Optional
from datetime import datetime
import sqlite3
from ..services.auth_service import verify_session_jwt, SessionData
from ..services.market_data_service import market_data_service
from ..models.market_data_dto import (
    CandleDataDTO, CandleInterval, WebSocketStatusDTO, SubscriptionRequest, FetchHistoricalRequest
)
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Debug endpoint for chart testing
@router.get("/market-data/debug-candles/{symbol}")
async def debug_candles(symbol: str):
    """Debug endpoint that returns fake candle data for testing chart component"""
    import random
    from datetime import datetime, timedelta
    
    # Generate fake candle data for testing
    candles = []
    base_price = 100.0
    current_time = datetime.now()
    
    for i in range(50):  # 50 candles
        # Random walk for price
        change = random.uniform(-2, 2)
        base_price += change
        
        # Ensure valid OHLC
        open_price = base_price
        close_price = base_price + random.uniform(-1, 1)
        high_price = max(open_price, close_price) + random.uniform(0, 0.5)
        low_price = min(open_price, close_price) - random.uniform(0, 0.5)
        volume = random.randint(10000, 100000)
        
        candle_time = current_time - timedelta(days=50-i)
        
        candles.append({
            "timestamp": candle_time.isoformat(),
            "open_price": round(open_price, 2),
            "high_price": round(high_price, 2),
            "low_price": round(low_price, 2),
            "close_price": round(close_price, 2),
            "volume": volume
        })
    
    return candles

# Removed test endpoint - using only real data from database

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
    interval: CandleInterval = Query(CandleInterval.ONE_DAY),
    start_time: Optional[str] = Query(None, description="ISO format datetime"),
    end_time: Optional[str] = Query(None, description="ISO format datetime"),
    limit: int = Query(100, description="Maximum number of candles"),
    # session: SessionData = Depends(require_auth)  # Temporarily disabled for testing
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
    interval: CandleInterval = Query(CandleInterval.ONE_DAY),
    limit: int = Query(10, description="Number of candles per instrument"),
    # session: SessionData = Depends(require_auth)  # Temporarily disabled for testing
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
    symbol: Optional[str] = Query(None, description="Stock symbol; if omitted, fetch for all selected instruments"),
    days_back: int = Query(30, description="Number of days back from today (default: 30)"),
    interval: str = Query("1DAY", description="Candle interval"),
    from_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    x_upstox_access_token: str | None = Header(default=None, alias="X-Upstox-Access-Token"),
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
        
        # Validate required parameters (symbol can be None -> meaning 'all selected')
        if not req_from_date or not req_to_date:
            return {"status": "error", "message": "from_date and to_date are required (or use days_back)"}
        
        logger.info(f"Fetching historical data: symbol={req_symbol}, range {req_from_date} to {req_to_date}; interval={req_interval}")
        
        # Determine target instruments list
        target_instruments = []
        if req_symbol:
            instrument = await instrument_service.get_instrument_by_symbol(req_symbol, x_upstox_access_token)
            if not instrument:
                return {"status": "error", "message": f"Instrument not found for symbol: {req_symbol}. Please refresh instruments cache via /api/instruments/refresh with a valid token."}
            target_instruments = [instrument]
        else:
            # Fetch for all selected instruments
            from ..services.instrument_service import instrument_service as isvc
            selected = await isvc.get_selected_instruments()
            if not selected:
                return {"status": "error", "message": "No instruments selected"}
            # Map to cached instruments by symbol to ensure real instrument_key is used
            for sel in selected:
                inst = await instrument_service.get_instrument_by_symbol(sel.symbol, x_upstox_access_token)
                if inst:
                    target_instruments.append(inst)

        # Ensure the instruments are in the selected list so UI tracks them (best-effort)
        try:
            for inst in target_instruments:
                await instrument_service.add_selected_instrument(inst)
        except Exception:
            pass
        
    # Map interval: API expects specific strings
        interval_map = {
            "1DAY": "day",
            "1MINUTE": "1minute",
            "5MINUTE": "5minute",
            "15MINUTE": "15minute",
            "30MINUTE": "30minute",
            "60MINUTE": "60minute",
            "WEEK": "week",
            "MONTH": "month",
        }
        api_interval = interval_map.get(req_interval.upper(), "day")

        total_candles_stored = 0
        results = []
        
        for instrument in target_instruments:
            # Fetch historical/intraday data from Upstox API (pass token if provided)
            if api_interval == "day" or api_interval in ("week", "month"):
                historical_data = await upstox_client.get_historical_candles(
                    instrument_key=instrument.instrument_key,
                    interval=api_interval,
                    from_date=req_from_date,
                    to_date=req_to_date,
                    token=x_upstox_access_token,
                )
            else:
                # minute intervals should use intraday endpoint
                historical_data = await upstox_client.get_intraday_candles(
                    instrument_key=instrument.instrument_key,
                    interval=api_interval,
                    from_date=req_from_date,
                    to_date=req_to_date,
                    token=x_upstox_access_token,
                )
            
            if not historical_data or "data" not in historical_data:
                results.append({"symbol": instrument.symbol, "instrument_key": instrument.instrument_key, "stored": 0, "status": "no-data"})
                continue
            
            # Store candles in database
            candles_stored = 0
            for candle_data in historical_data.get("data", {}).get("candles", []):
                try:
                    # Parse Upstox candle format: [timestamp, open, high, low, close, volume, open_interest]
                    timestamp_str = candle_data[0]
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Map back to our enum for storage
                    storage_interval = CandleInterval.ONE_DAY if api_interval in ("day", "week", "month") else CandleInterval.ONE_MINUTE

                    candle_dto = CandleDataDTO(
                        instrument_key=instrument.instrument_key,
                        symbol=instrument.symbol,
                        interval=storage_interval,
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
            total_candles_stored += candles_stored
            results.append({"symbol": instrument.symbol, "instrument_key": instrument.instrument_key, "stored": candles_stored, "status": "ok"})
        
        return {
            "status": "success",
            "message": f"Fetched and stored {total_candles_stored} candles",
            "interval": req_interval.upper(),
            "total_candles_stored": total_candles_stored,
            "from_date": req_from_date,
            "to_date": req_to_date,
            "results": results,
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
                # Prefer latest 1-minute candle, else 5m, else 15m, finally 1d
                chosen_candle = None
                for interval in (
                    CandleInterval.ONE_MINUTE,
                    CandleInterval.FIVE_MINUTE,
                    CandleInterval.FIFTEEN_MINUTE,
                    CandleInterval.ONE_DAY,
                ):
                    latest = await market_data_service.get_candles(
                        instrument_key=instrument.instrument_key,
                        interval=interval,
                        limit=1
                    )
                    if latest:
                        chosen_candle = latest[0]
                        break

                if chosen_candle:
                    ltp = chosen_candle.close_price
                    open_price = chosen_candle.open_price
                    high = chosen_candle.high_price
                    low = chosen_candle.low_price
                    vol = chosen_candle.volume

                    # Compute change vs previous close if available (better signal for watchlist)
                    prev_close = None
                    daily = await market_data_service.get_candles(
                        instrument_key=instrument.instrument_key,
                        interval=CandleInterval.ONE_DAY,
                        limit=2
                    )
                    if daily and len(daily) >= 2:
                        prev_close = daily[1].close_price
                    
                    if prev_close and prev_close > 0:
                        change = ltp - prev_close
                        change_pct = (change / prev_close) * 100
                    else:
                        change = ltp - open_price
                        change_pct = ((ltp - open_price) / open_price * 100) if open_price > 0 else 0

                    prices[instrument.instrument_key] = {
                        "symbol": instrument.symbol,
                        "ltp": ltp,
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "volume": vol,
                        "timestamp": chosen_candle.timestamp.isoformat(),
                        "change": change,
                        "change_percent": change_pct,
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

# Enhanced Historical Data Endpoints with Multiple Timeframes
@router.post("/market-data/fetch-historical-all")
async def fetch_historical_all_timeframes(
    days_back: int = Query(30, description="Number of days to fetch"),
    x_upstox_access_token: str | None = Header(default=None, alias="X-Upstox-Access-Token"),
    # session: SessionData = Depends(require_auth)  # Disabled for testing
):
    """
    Fetch historical data for ALL supported timeframes (1m, 5m, 15m, 1d) for all selected instruments
    Uses rate limiting and queuing to respect Upstox API limits
    """
    try:
        if not x_upstox_access_token:
            return {"status": "error", "message": "X-Upstox-Access-Token header is required"}
        
        from ..services.historical_data_manager import historical_data_manager
        
        logger.info(f"Starting comprehensive historical data fetch for {days_back} days")
        
        # Fetch all timeframes with rate limiting
        results = await historical_data_manager.fetch_all_timeframes(
            token=x_upstox_access_token,
            days_back=days_back
        )
        
        # Calculate summary statistics
        total_instruments = 0
        total_candles = 0
        success_count = 0
        
        summary = {}
        for interval, interval_results in results.items():
            successful_instruments = [r for r in interval_results if r.success]
            interval_candles = sum(r.candles_count for r in successful_instruments)
            
            summary[interval] = {
                "instruments_processed": len(interval_results),
                "instruments_successful": len(successful_instruments),
                "total_candles": interval_candles,
                "success_rate": f"{len(successful_instruments)/len(interval_results)*100:.1f}%" if interval_results else "0%"
            }
            
            total_instruments = len(interval_results)  # Same for all intervals
            total_candles += interval_candles
            success_count += len(successful_instruments)
        
        return {
            "status": "success",
            "message": f"Fetched historical data for {len(results)} timeframes",
            "total_instruments": total_instruments,
            "total_candles": total_candles,
            "days_back": days_back,
            "intervals_processed": list(results.keys()),
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_historical_all_timeframes: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/market-data/fetch-historical-1m")
async def fetch_historical_1m(
    days_back: int = Query(7, description="Number of days to fetch (max 7 for 1m data)"),
    x_upstox_access_token: str | None = Header(default=None, alias="X-Upstox-Access-Token"),
    # session: SessionData = Depends(require_auth)  # Disabled for testing
):
    """Fetch 1-minute historical data for all selected instruments"""
    try:
        if not x_upstox_access_token:
            return {"status": "error", "message": "X-Upstox-Access-Token header is required"}
        
        from ..services.historical_data_manager import historical_data_manager, IntervalType
        
        # Limit 1m data to prevent excessive API calls
        days_back = min(days_back, 7)
        
        logger.info(f"Fetching 1-minute data for {days_back} days")
        
        results = await historical_data_manager.fetch_single_interval(
            token=x_upstox_access_token,
            interval=IntervalType.ONE_MINUTE,
            days_back=days_back
        )
        
        successful = [r for r in results if r.success]
        total_candles = sum(r.candles_count for r in successful)
        
        return {
            "status": "success",
            "message": f"Fetched 1-minute data for {len(successful)}/{len(results)} instruments",
            "interval": "1minute",
            "instruments_processed": len(results),
            "instruments_successful": len(successful),
            "total_candles": total_candles,
            "days_back": days_back,
            "results": [{"symbol": r.symbol, "success": r.success, "candles": r.candles_count, "error": r.error_message} for r in results],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_historical_1m: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/market-data/fetch-historical-5m")
async def fetch_historical_5m(
    days_back: int = Query(15, description="Number of days to fetch"),
    x_upstox_access_token: str | None = Header(default=None, alias="X-Upstox-Access-Token"),
    # session: SessionData = Depends(require_auth)  # Disabled for testing
):
    """Fetch 5-minute historical data for all selected instruments"""
    try:
        if not x_upstox_access_token:
            return {"status": "error", "message": "X-Upstox-Access-Token header is required"}
        
        from ..services.historical_data_manager import historical_data_manager, IntervalType
        
        logger.info(f"Fetching 5-minute data for {days_back} days")
        
        results = await historical_data_manager.fetch_single_interval(
            token=x_upstox_access_token,
            interval=IntervalType.FIVE_MINUTE,
            days_back=days_back
        )
        
        successful = [r for r in results if r.success]
        total_candles = sum(r.candles_count for r in successful)
        
        return {
            "status": "success",
            "message": f"Fetched 5-minute data for {len(successful)}/{len(results)} instruments",
            "interval": "5minute",
            "instruments_processed": len(results),
            "instruments_successful": len(successful),
            "total_candles": total_candles,
            "days_back": days_back,
            "results": [{"symbol": r.symbol, "success": r.success, "candles": r.candles_count, "error": r.error_message} for r in results],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_historical_5m: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/market-data/fetch-historical-15m")
async def fetch_historical_15m(
    days_back: int = Query(30, description="Number of days to fetch"),
    x_upstox_access_token: str | None = Header(default=None, alias="X-Upstox-Access-Token"),
    # session: SessionData = Depends(require_auth)  # Disabled for testing
):
    """Fetch 15-minute historical data for all selected instruments"""
    try:
        if not x_upstox_access_token:
            return {"status": "error", "message": "X-Upstox-Access-Token header is required"}
        
        from ..services.historical_data_manager import historical_data_manager, IntervalType
        
        logger.info(f"Fetching 15-minute data for {days_back} days")
        
        results = await historical_data_manager.fetch_single_interval(
            token=x_upstox_access_token,
            interval=IntervalType.FIFTEEN_MINUTE,
            days_back=days_back
        )
        
        successful = [r for r in results if r.success]
        total_candles = sum(r.candles_count for r in successful)
        
        return {
            "status": "success",
            "message": f"Fetched 15-minute data for {len(successful)}/{len(results)} instruments",
            "interval": "15minute",
            "instruments_processed": len(results),
            "instruments_successful": len(successful),
            "total_candles": total_candles,
            "days_back": days_back,
            "results": [{"symbol": r.symbol, "success": r.success, "candles": r.candles_count, "error": r.error_message} for r in results],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_historical_15m: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/market-data/fetch-historical-1d")
async def fetch_historical_1d(
    days_back: int = Query(365, description="Number of days to fetch"),
    x_upstox_access_token: str | None = Header(default=None, alias="X-Upstox-Access-Token"),
    # session: SessionData = Depends(require_auth)  # Disabled for testing
):
    """Fetch daily historical data for all selected instruments"""
    try:
        if not x_upstox_access_token:
            return {"status": "error", "message": "X-Upstox-Access-Token header is required"}
        
        from ..services.historical_data_manager import historical_data_manager, IntervalType
        
        logger.info(f"Fetching daily data for {days_back} days")
        
        results = await historical_data_manager.fetch_single_interval(
            token=x_upstox_access_token,
            interval=IntervalType.ONE_DAY,
            days_back=days_back
        )
        
        successful = [r for r in results if r.success]
        total_candles = sum(r.candles_count for r in successful)
        
        return {
            "status": "success",
            "message": f"Fetched daily data for {len(successful)}/{len(results)} instruments",
            "interval": "day",
            "instruments_processed": len(results),
            "instruments_successful": len(successful),
            "total_candles": total_candles,
            "days_back": days_back,
            "results": [{"symbol": r.symbol, "success": r.success, "candles": r.candles_count, "error": r.error_message} for r in results],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_historical_1d: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/market-data/fetch-status")
async def get_fetch_status(
    # session: SessionData = Depends(require_auth)  # Disabled for testing
):
    """Get status of historical data fetching operations"""
    try:
        from ..services.historical_data_manager import historical_data_manager
        
        # Check if fetcher is currently processing
        is_processing = historical_data_manager.fetcher.is_processing
        queue_size = historical_data_manager.fetcher.request_queue.qsize()
        active_requests = historical_data_manager.fetcher.active_requests
        
        # Get database statistics
        conn = sqlite3.connect('market_data.db')
        cursor = conn.cursor()
        
        # Count by interval
        cursor.execute("SELECT interval, COUNT(*) as count FROM candles GROUP BY interval")
        interval_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total candles
        cursor.execute("SELECT COUNT(*) FROM candles")
        total_candles = cursor.fetchone()[0]
        
        # Latest timestamp per interval
        cursor.execute("""
            SELECT interval, MAX(timestamp) as latest_timestamp
            FROM candles 
            GROUP BY interval
        """)
        latest_data = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "status": "success",
            "fetcher_status": {
                "is_processing": is_processing,
                "queue_size": queue_size,
                "active_requests": active_requests
            },
            "database_statistics": {
                "total_candles": total_candles,
                "candles_by_interval": interval_counts,
                "latest_data_by_interval": latest_data
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting fetch status: {e}")
        return {"status": "error", "message": str(e)}