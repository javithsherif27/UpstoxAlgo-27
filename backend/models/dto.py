from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProfileDTO(BaseModel):
    name: str
    client_id: str
    kyc_status: str

class InstrumentDTO(BaseModel):
    instrument_key: str
    symbol: str
    name: str
    exchange: str
    segment: Optional[str] = None
    instrument_type: Optional[str] = None
    lot_size: Optional[int] = None

class SelectedInstrumentDTO(BaseModel):
    instrument_key: str
    symbol: str
    name: str
    exchange: str
    selected_at: datetime

class InstrumentCacheStatusDTO(BaseModel):
    total_instruments: int
    nse_equity_count: int
    last_updated: Optional[datetime] = None
    is_refreshing: bool = False
