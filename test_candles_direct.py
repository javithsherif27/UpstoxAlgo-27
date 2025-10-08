#!/usr/bin/env python3
"""Test the candles endpoint directly without authentication"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.services.market_data_service import market_data_service
from backend.models.market_data_dto import CandleInterval
import json

async def test_candles_endpoint():
    """Test what the candles endpoint should return"""
    
    print("=== TESTING CANDLES ENDPOINT LOGIC ===")
    
    # Test BYKE candles
    instrument_key = "NSE_EQ|INE319B01014"
    
    print(f"Fetching candles for {instrument_key}")
    
    candles = await market_data_service.get_candles(
        instrument_key=instrument_key,
        interval=CandleInterval.ONE_DAY,
        limit=5
    )
    
    print(f"Found {len(candles)} candles")
    
    # Convert to the format expected by frontend
    candles_json = []
    for candle in candles:
        candles_json.append({
            "instrument_key": candle.instrument_key,
            "symbol": candle.symbol,
            "interval": candle.interval.value,
            "timestamp": candle.timestamp.isoformat(),
            "open_price": candle.open_price,
            "high_price": candle.high_price,
            "low_price": candle.low_price,
            "close_price": candle.close_price,
            "volume": candle.volume,
            "tick_count": candle.tick_count
        })
    
    print("Candles in API format:")
    print(json.dumps(candles_json, indent=2))
    
    # Test what happens with wrong format
    print(f"\n=== TESTING WITH 1m INTERVAL ===")
    candles_1m = await market_data_service.get_candles(
        instrument_key=instrument_key,
        interval=CandleInterval.ONE_MINUTE,
        limit=5
    )
    print(f"1m candles: {len(candles_1m)}")

if __name__ == "__main__":
    asyncio.run(test_candles_endpoint())