from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query
from typing import List, Optional
from ..services.auth_service import verify_session_jwt, SessionData
from ..services.instrument_service import instrument_service
from ..models.dto import InstrumentDTO, SelectedInstrumentDTO, InstrumentCacheStatusDTO
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

async def require_auth(request: Request):
    data = verify_session_jwt(request.cookies.get("app_session"))
    if not data:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return data

@router.get("/instruments", response_model=List[InstrumentDTO])
async def get_instruments(
    x_upstox_access_token: str = Header(alias="X-Upstox-Access-Token"), 
    session: SessionData = Depends(require_auth),
    search: Optional[str] = Query(None, description="Search by symbol or name"),
    limit: Optional[int] = Query(100, description="Limit number of results")
):
    """Get cached NSE equity instruments with optional search and pagination"""
    instruments = await instrument_service.get_cached_instruments()
    
    # If no cached data, return empty list with instruction to refresh
    if not instruments:
        logger.info("No cached instruments found")
        return []
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        instruments = [
            inst for inst in instruments 
            if search_lower in inst.symbol.lower() or search_lower in inst.name.lower()
        ]
    
    # Apply limit
    if limit:
        instruments = instruments[:limit]
    
    logger.info(f"Returning {len(instruments)} instruments")
    return instruments

@router.post("/instruments/refresh", response_model=InstrumentCacheStatusDTO)
async def refresh_instruments_cache(
    x_upstox_access_token: str = Header(alias="X-Upstox-Access-Token"), 
    session: SessionData = Depends(require_auth)
):
    """Refresh instruments cache from Upstox API"""
    logger.info("Starting instruments cache refresh")
    return await instrument_service.refresh_instruments_cache(x_upstox_access_token)

@router.get("/instruments/cache-status", response_model=InstrumentCacheStatusDTO)
async def get_cache_status(session: SessionData = Depends(require_auth)):
    """Get current cache status"""
    return await instrument_service.get_cache_status()

@router.post("/instruments/select")
async def select_instrument(
    instrument: InstrumentDTO,
    session: SessionData = Depends(require_auth)
):
    """Add an instrument to the selected list"""
    await instrument_service.add_selected_instrument(instrument)
    return {"message": "Instrument added to selection", "instrument_key": instrument.instrument_key}

@router.delete("/instruments/select/{instrument_key}")
async def deselect_instrument(
    instrument_key: str,
    session: SessionData = Depends(require_auth)
):
    """Remove an instrument from the selected list"""
    await instrument_service.remove_selected_instrument(instrument_key)
    return {"message": "Instrument removed from selection", "instrument_key": instrument_key}

@router.get("/instruments/selected", response_model=List[SelectedInstrumentDTO])
async def get_selected_instruments(session: SessionData = Depends(require_auth)):
    """Get list of selected instruments"""
    return await instrument_service.get_selected_instruments()

@router.get("/instruments/selected-keys")
async def get_selected_instrument_keys(session: SessionData = Depends(require_auth)):
    """Get set of selected instrument keys for quick lookup"""
    selected_keys = await instrument_service.get_selected_instrument_keys()
    return {"selected_keys": list(selected_keys)}
