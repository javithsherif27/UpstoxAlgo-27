import os
import httpx
from typing import List, Dict, Any
from ..utils.logging import get_logger
from ..models.dto import InstrumentDTO

logger = get_logger(__name__)
BASE_URL = os.getenv("UPSTOX_BASE_URL", "https://api.upstox.com/v2")

_client = httpx.AsyncClient(timeout=30.0)  # Increased timeout for large instrument data

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