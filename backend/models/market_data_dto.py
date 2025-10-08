from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CandleInterval(str, Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTE = "5m"          # Supported by Upstox V3 API: minutes/5
    FIFTEEN_MINUTE = "15m"      # Supported by Upstox V3 API: minutes/15
    ONE_DAY = "1d"             # Supported by Upstox V3 API: days/1

class MarketTickDTO(BaseModel):
    """Raw tick data from WebSocket"""
    instrument_key: str
    symbol: str
    ltp: float  # Last traded price
    ltt: int    # Last traded time (timestamp)
    ltq: int    # Last traded quantity
    cp: float   # Close price
    volume: Optional[int] = None
    oi: Optional[int] = None  # Open interest
    timestamp: datetime
    raw_data: Optional[Dict[str, Any]] = None

class CandleDataDTO(BaseModel):
    """OHLCV candle data"""
    instrument_key: str
    symbol: str
    interval: CandleInterval
    timestamp: datetime  # Candle start time
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    open_interest: Optional[int] = None
    tick_count: int  # Number of ticks that formed this candle
    
class WebSocketStatusDTO(BaseModel):
    """WebSocket connection status"""
    is_connected: bool
    subscribed_instruments: List[str]
    last_heartbeat: Optional[datetime] = None
    connection_time: Optional[datetime] = None
    total_ticks_received: int = 0
    errors: List[str] = []

class MarketDataFeedRequest(BaseModel):
    """Request to subscribe/unsubscribe from market data"""
    guid: str
    method: str  # "sub", "unsub", "change_mode"
    data: Dict[str, Any]

class SubscriptionRequest(BaseModel):
    """Request to start market data collection"""
    instrument_keys: List[str]
    mode: str = "ltpc"  # "ltpc", "full", "option_greeks", "full_d30"
    intervals: List[CandleInterval] = [CandleInterval.ONE_MINUTE, CandleInterval.FIVE_MINUTE, CandleInterval.FIFTEEN_MINUTE]

class FetchHistoricalRequest(BaseModel):
    """Request to fetch historical data from Upstox API"""
    symbol: str
    interval: str  # "1DAY", "1MINUTE", etc.
    from_date: str  # "2024-12-01" 
    to_date: str    # "2024-12-31"