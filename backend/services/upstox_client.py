import os
import httpx
from typing import List, Dict, Any
from ..utils.logging import get_logger
from ..models.dto import InstrumentDTO

logger = get_logger(__name__)
BASE_URL = os.getenv("UPSTOX_BASE_URL", "https://api.upstox.com/v2")

_client = httpx.AsyncClient(timeout=30.0)  # Increased timeout for large instrument data

class UpstoxClient:
    """Upstox API client with methods for historical data"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.client = _client
    
    async def _request(self, path: str, token: str = None):
        """Make authenticated request to Upstox API"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            resp = await self.client.get(self.base_url + path, headers=headers)
            if resp.status_code >= 400:
                logger.warning("Upstox error %s %s", resp.status_code, resp.text[:200])
                resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("Upstox request failed: %s", e)
            raise
    
    async def get_historical_candles(self, instrument_key: str, interval: str, from_date: str, to_date: str, token: str = None):
        """
        Fetch historical candle data from Upstox API V3
        
        Args:
            instrument_key: Upstox instrument key (e.g., "NSE_EQ|INE009A01021")
            interval: Candle interval - supports 1m, 5m, 15m, 1d formats
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
            token: Access token (optional for testing)
        
        Returns:
            Historical candle data
        """
        logger.info(f"Fetching {interval} candles for {instrument_key} from {from_date} to {to_date}")
        
        # For testing without token, return mock data with realistic structure
        if not token:
            logger.warning("No token provided, returning mock historical data")
            return {
                "status": "success",
                "data": {
                    "candles": [
                        ["2024-10-07T00:00:00+05:30", 94.25, 95.50, 93.80, 94.15, 125000, 0],
                        ["2024-10-06T00:00:00+05:30", 93.80, 94.60, 93.20, 94.25, 110000, 0],
                        ["2024-10-05T00:00:00+05:30", 94.10, 94.80, 93.50, 93.80, 98000, 0],
                    ]
                }
            }
        
        # Validate dates - no future dates allowed
        from datetime import datetime, timedelta
        today = datetime.now().date()
        to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
        from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
        
        if to_date_obj > today:
            # Adjust to yesterday at latest
            to_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            logger.warning(f"Adjusted to_date from future date to: {to_date}")
        
        if from_date_obj > today:
            # Adjust from_date if it's also in future
            from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            logger.warning(f"Adjusted from_date from future date to: {from_date}")
        
        # Map intervals to V3 API format: /{unit}/{interval_value}
        # Based on documentation: minutes supports 1,2,3,...,300 and days supports 1
        interval_mapping = {
            "1m": ("minutes", "1"),      # 1-minute interval
            "5m": ("minutes", "5"),      # 5-minute interval  
            "15m": ("minutes", "15"),    # 15-minute interval
            "1d": ("days", "1"),         # Daily interval
        }
        
        if interval not in interval_mapping:
            raise ValueError(f"Unsupported interval: {interval}. Supported intervals: 1m, 5m, 15m, 1d")
        
        unit, interval_value = interval_mapping[interval]
        
        # V3 API format: /v3/historical-candle/{instrument_key}/{unit}/{interval}/{to_date}/{from_date}
        # Note: We need to change the base URL to v3 for this endpoint
        v3_base_url = self.base_url.replace('/v2', '/v3')
        path = f"/historical-candle/{instrument_key}/{unit}/{interval_value}/{to_date}/{from_date}"
        
        logger.info(f"Using V3 API endpoint: {v3_base_url}{path}")
        
        # Make direct request with V3 URL
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            resp = await self.client.get(v3_base_url + path, headers=headers)
            if resp.status_code >= 400:
                logger.warning("Upstox V3 API error %s %s", resp.status_code, resp.text[:200])
                resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("Upstox V3 request failed: %s", e)
            raise
    
    async def get_intraday_candles(self, instrument_key: str, interval: str, from_date: str, to_date: str, token: str = None):
        """
        Fetch intraday candle data from Upstox API v2
        
        Args:
            instrument_key: Upstox instrument key
            interval: Candle interval (1minute, 5minute, 15minute, 30minute, 60minute)
            from_date: Start date in YYYY-MM-DD format  
            to_date: End date in YYYY-MM-DD format
            token: Access token (optional for testing)
        
        Returns:
            Intraday candle data
        """
        logger.info(f"Fetching intraday candles for {instrument_key}")
        
        # For testing without token, return mock data
        if not token:
            logger.warning("No token provided, returning mock intraday data")
            return {
                "status": "success", 
                "data": {
                    "candles": [
                        ["2024-10-07T09:15:00+05:30", 94.00, 94.25, 93.95, 94.15, 5000, 0],
                        ["2024-10-07T09:16:00+05:30", 94.15, 94.30, 94.10, 94.20, 3500, 0],
                    ]
                }
            }
        
        path = f"/historical-candle/intraday/{instrument_key}/{interval}"
        return await self._request(path, token)

# Create a singleton instance
upstox_client = UpstoxClient()

async def _request(path: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = await _client.get(BASE_URL + path, headers=headers)
        if resp.status_code >= 400:
            logger.warning("Upstox error %s %s", resp.status_code, resp.text[:200])
            resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.exception("Upstox request failed: %s", e)
        raise

async def get_raw_instruments(token: str):
    """Get raw instruments data from Upstox assets (downloadable JSON files)"""
    import gzip
    import json
    
    # Upstox provides instruments data as downloadable JSON files, not API endpoints
    instruments_urls = [
        "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz",  # NSE only (smaller file)
        "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz",  # All exchanges (larger file)
    ]
    
    for url in instruments_urls:
        try:
            logger.info(f"Fetching instruments from: {url}")
            # Don't need authorization for these public asset URLs
            resp = await _client.get(url, timeout=60.0)  # Longer timeout for large files
            if resp.status_code >= 400:
                logger.warning(f"Failed to fetch from {url}: {resp.status_code}")
                continue
                
            # Decompress gzipped content
            content = gzip.decompress(resp.content).decode('utf-8')
            instruments_data = json.loads(content)
            
            logger.info(f"Successfully fetched {len(instruments_data)} instruments from {url}")
            return instruments_data
            
        except Exception as e:
            logger.warning(f"Failed to fetch from {url}: {e}")
            continue
    
    # If all URLs fail, return empty list and log the issue
    logger.error("All instrument URLs failed, returning empty list")
    return []

def filter_nse_equity_instruments(instruments_data: List[Dict[str, Any]]) -> List[InstrumentDTO]:
    """Filter instruments to only include NSE Equity instruments"""
    filtered_instruments = []
    
    for instrument in instruments_data:
        # Filter for NSE exchange and EQ (Equity) segment
        # Based on Upstox documentation: segment="NSE_EQ" and instrument_type="EQ"
        if (instrument.get('exchange') == 'NSE' and 
            instrument.get('segment') == 'NSE_EQ' and
            instrument.get('instrument_type') == 'EQ'):
            
            # Use trading_symbol as the primary symbol field (as per Upstox docs)
            trading_symbol = instrument.get('trading_symbol', instrument.get('tradingsymbol', ''))
            
            filtered_instruments.append(InstrumentDTO(
                instrument_key=instrument.get('instrument_key', ''),
                symbol=trading_symbol,
                name=instrument.get('name', trading_symbol),
                exchange=instrument.get('exchange', ''),
                segment=instrument.get('segment', ''),
                instrument_type=instrument.get('instrument_type', ''),
                lot_size=instrument.get('lot_size', 1)
            ))
    
    logger.info(f"Filtered {len(filtered_instruments)} NSE equity instruments from {len(instruments_data)} total")
    return filtered_instruments

async def get_instruments(token: str) -> List[InstrumentDTO]:
    """Get filtered NSE equity instruments from Upstox API"""
    try:
        raw_instruments = await get_raw_instruments(token)
        return filter_nse_equity_instruments(raw_instruments)
    except Exception as e:
        logger.error(f"Failed to fetch and filter instruments: {e}")
        return []

async def get_profile(token: str):
    """Get user profile from Upstox API"""
    response = await _request("/user/profile", token)
    
    # Handle both nested and direct response formats
    if 'data' in response:
        profile_data = response['data']
    else:
        profile_data = response
    
    # Extract fields with fallback handling
    user_name = profile_data.get('user_name') or profile_data.get('name', '')
    client_id = profile_data.get('user_id') or profile_data.get('client_id', '')
    
    # Handle KYC status - check various possible field names
    kyc_status = (
        profile_data.get('is_kyc_done') or 
        profile_data.get('kyc_status') or 
        profile_data.get('kyc_complete', False)
    )
    
    # Convert kyc_status to string as expected by ProfileDTO
    kyc_status_str = "ACTIVE" if kyc_status else "INACTIVE"
    
    return {
        "name": user_name,  # ProfileDTO expects 'name', not 'user_name'
        "client_id": client_id,
        "kyc_status": kyc_status_str  # ProfileDTO expects string, not boolean
    }

async def get_holdings(token: str):
    """Get holdings from Upstox API"""
    return await _request("/portfolio/long-term-holdings", token)

async def get_positions(token: str):
    """Get positions from Upstox API"""
    return await _request("/portfolio/short-term-positions", token)

# Standalone functions for backward compatibility
async def get_historical_candles(instrument_key: str, interval: str, from_date: str, to_date: str, token: str = None):
    """Backward compatibility function - delegates to upstox_client"""
    return await upstox_client.get_historical_candles(instrument_key, interval, from_date, to_date, token)

async def get_intraday_candles(instrument_key: str, interval: str, from_date: str, to_date: str, token: str = None):
    """Backward compatibility function - delegates to upstox_client"""
    return await upstox_client.get_intraday_candles(instrument_key, interval, from_date, to_date, token)