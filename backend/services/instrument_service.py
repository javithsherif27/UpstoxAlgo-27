import json
from typing import List, Optional, Set
from datetime import datetime, timezone
from ..services.cache_service import get_cached, put_cached
from ..services.upstox_client import get_raw_instruments, filter_nse_equity_instruments
from ..models.dto import InstrumentDTO, SelectedInstrumentDTO, InstrumentCacheStatusDTO
from ..utils.logging import get_logger

logger = get_logger(__name__)

INSTRUMENTS_CACHE_KEY = "nse_equity_instruments"
INSTRUMENTS_METADATA_KEY = "instruments_metadata"
SELECTED_INSTRUMENTS_KEY = "selected_instruments"
CACHE_TTL_HOURS = 24  # Cache instruments for 24 hours

class InstrumentService:
    def __init__(self):
        self._is_refreshing = False
    
    async def get_cached_instruments(self) -> List[InstrumentDTO]:
        """Get cached NSE equity instruments"""
        cached_data = await get_cached(INSTRUMENTS_CACHE_KEY)
        if not cached_data:
            return []
        
        try:
            instruments_data = json.loads(cached_data)
            return [InstrumentDTO(**item) for item in instruments_data]
        except Exception as e:
            logger.error(f"Error parsing cached instruments: {e}")
            return []
    
    async def refresh_instruments_cache(self, token: str) -> InstrumentCacheStatusDTO:
        """Refresh instruments cache from Upstox API"""
        if self._is_refreshing:
            return await self.get_cache_status()
        
        try:
            self._is_refreshing = True
            logger.info("Starting instruments cache refresh")
            
            # Fetch raw instruments from Upstox
            raw_instruments = await get_raw_instruments(token)
            
            # Filter NSE equity instruments
            nse_equity_instruments = filter_nse_equity_instruments(raw_instruments)
            
            # Serialize and cache
            instruments_json = json.dumps([instrument.dict() for instrument in nse_equity_instruments])
            await put_cached(INSTRUMENTS_CACHE_KEY, instruments_json)
            
            # Update metadata
            metadata = {
                "total_instruments": len(raw_instruments),
                "nse_equity_count": len(nse_equity_instruments),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            await put_cached(INSTRUMENTS_METADATA_KEY, json.dumps(metadata))
            
            logger.info(f"Cached {len(nse_equity_instruments)} NSE equity instruments")
            return await self.get_cache_status()
            
        except Exception as e:
            logger.error(f"Error refreshing instruments cache: {e}")
            raise
        finally:
            self._is_refreshing = False
    
    async def get_cache_status(self) -> InstrumentCacheStatusDTO:
        """Get current cache status"""
        metadata_json = await get_cached(INSTRUMENTS_METADATA_KEY)
        
        if not metadata_json:
            return InstrumentCacheStatusDTO(
                total_instruments=0,
                nse_equity_count=0,
                is_refreshing=self._is_refreshing
            )
        
        try:
            metadata = json.loads(metadata_json)
            return InstrumentCacheStatusDTO(
                total_instruments=metadata.get("total_instruments", 0),
                nse_equity_count=metadata.get("nse_equity_count", 0),
                last_updated=datetime.fromisoformat(metadata["last_updated"]) if metadata.get("last_updated") else None,
                is_refreshing=self._is_refreshing
            )
        except Exception as e:
            logger.error(f"Error parsing cache metadata: {e}")
            return InstrumentCacheStatusDTO(
                total_instruments=0,
                nse_equity_count=0,
                is_refreshing=self._is_refreshing
            )
    
    async def add_selected_instrument(self, instrument: InstrumentDTO) -> None:
        """Add an instrument to the selected list"""
        selected_instruments = await self.get_selected_instruments()
        
        # Check if already selected
        existing_keys = {inst.instrument_key for inst in selected_instruments}
        if instrument.instrument_key not in existing_keys:
            selected_instrument = SelectedInstrumentDTO(
                instrument_key=instrument.instrument_key,
                symbol=instrument.symbol,
                name=instrument.name,
                exchange=instrument.exchange,
                selected_at=datetime.now(timezone.utc)
            )
            selected_instruments.append(selected_instrument)
            
            # Save back to cache (convert datetime to ISO string for JSON serialization)
            selected_data = []
            for inst in selected_instruments:
                inst_dict = inst.dict()
                if 'selected_at' in inst_dict and inst_dict['selected_at']:
                    inst_dict['selected_at'] = inst_dict['selected_at'].isoformat()
                selected_data.append(inst_dict)
            selected_json = json.dumps(selected_data)
            await put_cached(SELECTED_INSTRUMENTS_KEY, selected_json)
            
            logger.info(f"Added instrument to selection: {instrument.symbol}")
    
    async def remove_selected_instrument(self, instrument_key: str) -> None:
        """Remove an instrument from the selected list"""
        selected_instruments = await self.get_selected_instruments()
        
        # Filter out the instrument to remove
        updated_instruments = [inst for inst in selected_instruments if inst.instrument_key != instrument_key]
        
        # Save back to cache (convert datetime to ISO string for JSON serialization)
        selected_data = []
        for inst in updated_instruments:
            inst_dict = inst.dict()
            if 'selected_at' in inst_dict and inst_dict['selected_at']:
                inst_dict['selected_at'] = inst_dict['selected_at'].isoformat()
            selected_data.append(inst_dict)
        selected_json = json.dumps(selected_data)
        await put_cached(SELECTED_INSTRUMENTS_KEY, selected_json)
        
        logger.info(f"Removed instrument from selection: {instrument_key}")
    
    async def get_selected_instruments(self) -> List[SelectedInstrumentDTO]:
        """Get list of selected instruments"""
        cached_data = await get_cached(SELECTED_INSTRUMENTS_KEY)
        if not cached_data:
            return []
        
        try:
            selected_data = json.loads(cached_data)
            instruments = []
            for item in selected_data:
                # Convert ISO string back to datetime
                if 'selected_at' in item and isinstance(item['selected_at'], str):
                    item['selected_at'] = datetime.fromisoformat(item['selected_at'])
                instruments.append(SelectedInstrumentDTO(**item))
            return instruments
        except Exception as e:
            logger.error(f"Error parsing selected instruments: {e}")
            return []
    
    async def get_selected_instrument_keys(self) -> Set[str]:
        """Get set of selected instrument keys"""
        cached_data = await get_cached(SELECTED_INSTRUMENTS_KEY)
        if not cached_data:
            return set()
        
        try:
            selected_data = json.loads(cached_data)
            return {item["instrument_key"] for item in selected_data}
        except Exception as e:
            logger.error(f"Error parsing selected instrument keys: {e}")
            return set()

# Global service instance
instrument_service = InstrumentService()