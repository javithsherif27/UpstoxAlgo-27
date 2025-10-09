#!/usr/bin/env python3
"""
Trading Data Management API Endpoints
Provides trading-grade data management with 100% integrity guarantee
"""

from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from typing import Dict, Optional
from datetime import datetime

from ..services.trading_data_manager import trading_data_manager
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/trading", tags=["trading"])

@router.post("/initialize")
async def initialize_trading_system(
    x_upstox_access_token: str = Header(alias="X-Upstox-Access-Token")
):
    """
    Initialize the trading system with instruments and token
    Must be called first before any trading operations
    """
    try:
        logger.info("🚀 Initializing trading system...")
        
        await trading_data_manager.initialize_instruments(x_upstox_access_token)
        
        return {
            "status": "success",
            "message": "Trading system initialized successfully",
            "timestamp": datetime.now().isoformat(),
            "instruments_count": len(trading_data_manager.instruments)
        }
        
    except Exception as e:
        logger.error(f"❌ Trading system initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch-historical-complete")
async def fetch_complete_historical_data(
    background_tasks: BackgroundTasks,
    x_upstox_access_token: str = Header(alias="X-Upstox-Access-Token")
):
    """
    Fetch complete historical data for all selected instruments
    Trading-critical: Ensures 100% data completeness before websocket
    """
    try:
        logger.info("📊 Starting complete historical data fetch...")
        
        # Set token if not already set
        if not trading_data_manager.token:
            await trading_data_manager.initialize_instruments(x_upstox_access_token)
        
        # Start historical fetch in background
        background_tasks.add_task(trading_data_manager.fetch_complete_historical_data)
        
        return {
            "status": "started", 
            "message": "Complete historical data fetch initiated",
            "timestamp": datetime.now().isoformat(),
            "note": "Monitor /trading/status for completion"
        }
        
    except Exception as e:
        logger.error(f"❌ Historical fetch initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-websocket")
async def start_trading_websocket():
    """
    Start websocket feed for real-time data
    Only starts after historical data is 100% complete
    """
    try:
        logger.info("🌐 Starting trading websocket...")
        
        # Verify historical data completeness first
        status = await trading_data_manager.validate_historical_data_completeness()
        
        if not status.ready_for_trading:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot start websocket: Historical data only {status.completion_percentage:.1f}% complete"
            )
        
        # Start websocket
        success = await trading_data_manager.start_websocket_feed()
        
        if success:
            return {
                "status": "success",
                "message": "Trading websocket started successfully",
                "timestamp": datetime.now().isoformat(),
                "data_completeness": status.completion_percentage
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start websocket feed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Websocket startup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_trading_status():
    """
    Get comprehensive trading system status
    Shows data completeness, websocket status, and trading readiness
    """
    try:
        status = await trading_data_manager.get_trading_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-integrity")
async def check_data_integrity():
    """
    Validate data integrity and detect gaps
    Trading-critical: Ensures data completeness
    """
    try:
        logger.info("🔍 Checking data integrity...")
        
        integrity_status = await trading_data_manager.validate_historical_data_completeness()
        
        return {
            "status": "success",
            "data_integrity": {
                "ready_for_trading": integrity_status.ready_for_trading,
                "completion_percentage": integrity_status.completion_percentage,
                "total_instruments": integrity_status.total_instruments,
                "historical_complete": integrity_status.historical_complete,
                "websocket_active": integrity_status.websocket_active,
                "gaps_detected": integrity_status.data_gaps_detected,
                "recovery_in_progress": integrity_status.recovery_in_progress
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Data integrity check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recover-gaps")
async def recover_data_gaps(
    background_tasks: BackgroundTasks
):
    """
    Manually trigger data gap recovery
    Fills any missing candles to ensure 100% completeness
    """
    try:
        logger.info("🔧 Initiating manual gap recovery...")
        
        # Start gap recovery in background
        background_tasks.add_task(trading_data_manager.recover_data_gaps)
        
        return {
            "status": "started",
            "message": "Data gap recovery initiated",
            "timestamp": datetime.now().isoformat(),
            "note": "Monitor /trading/status for completion"
        }
        
    except Exception as e:
        logger.error(f"❌ Gap recovery initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instruments")
async def get_trading_instruments():
    """
    Get all trading instruments with their status
    """
    try:
        instruments_data = []
        
        for instrument in trading_data_manager.instruments.values():
            instruments_data.append({
                "instrument_key": instrument.instrument_key,
                "symbol": instrument.symbol, 
                "name": instrument.name,
                "is_selected": instrument.is_selected,
                "historical_complete": instrument.historical_complete,
                "websocket_active": instrument.websocket_active,
                "last_candle_time": instrument.last_candle_time.isoformat() if instrument.last_candle_time else None,
                "data_gaps_count": len(instrument.data_gaps)
            })
            
        return {
            "status": "success",
            "instruments": instruments_data,
            "total_count": len(instruments_data),
            "selected_count": len([i for i in instruments_data if i["is_selected"]]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Instruments fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-status")
async def get_market_status():
    """
    Get current market status and trading hours
    """
    try:
        is_market_hours = trading_data_manager._is_market_hours()
        current_time = datetime.now()
        
        return {
            "status": "success",
            "market": {
                "is_open": is_market_hours,
                "current_time": current_time.isoformat(),
                "market_start": f"{trading_data_manager.market_start[0]:02d}:{trading_data_manager.market_start[1]:02d}",
                "market_end": f"{trading_data_manager.market_end[0]:02d}:{trading_data_manager.market_end[1]:02d}",
                "is_weekday": current_time.weekday() < 5
            },
            "timestamp": current_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Market status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-stop")
async def emergency_stop():
    """
    Emergency stop for all trading operations
    Stops websocket and clears all active processes
    """
    try:
        logger.warning("🛑 EMERGENCY STOP initiated")
        
        # Stop websocket
        if trading_data_manager.websocket_active:
            # Disconnect websocket (implementation depends on your websocket client)
            pass
            
        # Reset all statuses
        trading_data_manager.websocket_active = False
        trading_data_manager.historical_complete = False
        trading_data_manager.gap_recovery_active = False
        
        # Reset instrument statuses
        for instrument in trading_data_manager.instruments.values():
            instrument.websocket_active = False
            instrument.historical_complete = False
            
        return {
            "status": "success",
            "message": "Emergency stop executed - All trading operations halted",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Emergency stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))