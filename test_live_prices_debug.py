#!/usr/bin/env python3
"""Test script to debug live prices endpoint directly"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.services.market_data_service import market_data_service
from backend.services.instrument_service import instrument_service
from backend.models.market_data_dto import CandleInterval

async def test_live_prices():
    print("=== TESTING LIVE PRICES LOGIC ===")
    
    # 1. Check selected instruments
    selected = await instrument_service.get_selected_instruments()
    print(f"Selected instruments: {len(selected)}")
    for inst in selected[:3]:  # Show first 3
        print(f"  - {inst.symbol} ({inst.instrument_key})")
    
    if not selected:
        print("No instruments selected! This is why UI shows empty watchlist.")
        return
        
    # 2. Check latest ticks (should be empty since no WebSocket running)
    instrument_keys = [inst.instrument_key for inst in selected]
    latest_ticks = await market_data_service.get_latest_ticks(instrument_keys)
    print(f"\nLatest ticks: {len(latest_ticks)} instruments")
    
    # 3. Check candle fallback for each selected instrument
    print("\n=== CANDLE FALLBACK TEST ===")
    prices = {}
    
    for instrument in selected:
        print(f"\nTesting {instrument.symbol} ({instrument.instrument_key}):")
        
        # Try each interval in order
        chosen_candle = None
        for interval in (CandleInterval.ONE_MINUTE, CandleInterval.FIVE_MINUTE, CandleInterval.FIFTEEN_MINUTE, CandleInterval.ONE_DAY):
            latest = await market_data_service.get_candles(
                instrument_key=instrument.instrument_key,
                interval=interval,
                limit=1
            )
            if latest:
                chosen_candle = latest[0]
                print(f"  Found {interval.value} candle: O={chosen_candle.open_price} C={chosen_candle.close_price}")
                break
            else:
                print(f"  No {interval.value} candles")
        
        if chosen_candle:
            ltp = chosen_candle.close_price
            open_price = chosen_candle.open_price
            
            # Check for previous daily close
            daily = await market_data_service.get_candles(
                instrument_key=instrument.instrument_key,
                interval=CandleInterval.ONE_DAY,
                limit=2
            )
            prev_close = None
            if daily and len(daily) >= 2:
                prev_close = daily[1].close_price
                print(f"  Previous daily close: {prev_close}")
            
            if prev_close and prev_close > 0:
                change = ltp - prev_close
                change_pct = (change / prev_close) * 100
            else:
                change = ltp - open_price
                change_pct = ((ltp - open_price) / open_price * 100) if open_price > 0 else 0
            
            price_data = {
                "symbol": instrument.symbol,
                "ltp": ltp,
                "open": open_price,
                "high": chosen_candle.high_price,
                "low": chosen_candle.low_price,
                "volume": chosen_candle.volume,
                "change": change,
                "change_percent": change_pct,
                "source": "candle"
            }
            
            prices[instrument.instrument_key] = price_data
            
            print(f"  Final: LTP={ltp}, Change={change} ({change_pct:.2f}%)")
        else:
            print(f"  No candle data found for {instrument.symbol}")
            prices[instrument.instrument_key] = {
                "symbol": instrument.symbol,
                "ltp": 0,
                "open": 0,
                "high": 0,
                "low": 0,
                "volume": 0,
                "change": 0,
                "change_percent": 0,
                "source": "none"
            }
    
    print(f"\n=== FINAL PRICES RESPONSE ===")
    result = {
        "prices": prices,
        "total_instruments": len(selected),
    }
    
    import json
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_live_prices())