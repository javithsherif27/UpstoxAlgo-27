#!/usr/bin/env python3
"""Final test of the live-prices logic now that we have selected instruments"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.services.market_data_service import market_data_service
from backend.services.instrument_service import instrument_service  
from backend.models.market_data_dto import CandleInterval
import json

async def test_final_live_prices():
    print("=== FINAL LIVE PRICES TEST ===")
    
    # Get selected instruments (should be 3 now)
    selected_instruments = await instrument_service.get_selected_instruments()
    print(f"Selected instruments: {len(selected_instruments)}")
    
    if not selected_instruments:
        print("ERROR: No instruments selected!")
        return
    
    # Get instrument keys
    instrument_keys = [inst.instrument_key for inst in selected_instruments]
    
    # Check for live ticks (should be empty since no WebSocket running)
    latest_ticks = await market_data_service.get_latest_ticks(instrument_keys)
    print(f"Live ticks: {len(latest_ticks)} instruments")
    
    # Since no live ticks, test the candle fallback logic
    print("\n=== CANDLE FALLBACK SIMULATION ===")
    prices = {}
    
    for instrument in selected_instruments:
        print(f"\nProcessing {instrument.symbol}:")
        
        # Try to find candles in order: 1m, 5m, 15m, 1d
        chosen_candle = None
        for interval in (CandleInterval.ONE_MINUTE, CandleInterval.FIVE_MINUTE, CandleInterval.FIFTEEN_MINUTE, CandleInterval.ONE_DAY):
            latest = await market_data_service.get_candles(
                instrument_key=instrument.instrument_key,
                interval=interval,
                limit=1
            )
            if latest:
                chosen_candle = latest[0]
                print(f"  Found {interval.value} candle: C={chosen_candle.close_price}")
                break
            else:
                print(f"  No {interval.value} candles")
        
        if chosen_candle:
            ltp = chosen_candle.close_price
            open_price = chosen_candle.open_price
            high = chosen_candle.high_price
            low = chosen_candle.low_price
            vol = chosen_candle.volume

            # Compute change vs previous close if available
            prev_close = None
            daily = await market_data_service.get_candles(
                instrument_key=instrument.instrument_key,
                interval=CandleInterval.ONE_DAY,
                limit=2
            )
            if daily and len(daily) >= 2:
                prev_close = daily[1].close_price
                print(f"  Previous daily close: {prev_close}")
            
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
            
            print(f"  Final: LTP=₹{ltp}, Change=₹{change:.2f} ({change_pct:.2f}%)")
        else:
            # No candle data available
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
            print(f"  No data available for {instrument.symbol}")
    
    # Simulate the final API response
    result = {
        "prices": prices,
        "total_instruments": len(selected_instruments),
    }
    
    print(f"\n=== FINAL API RESPONSE ===")
    print(json.dumps(result, indent=2, default=str))
    
    # Summary
    non_zero_count = sum(1 for p in prices.values() if p.get("ltp", 0) > 0)
    print(f"\n=== SUMMARY ===")
    print(f"Total instruments: {len(selected_instruments)}")
    print(f"Instruments with data: {non_zero_count}")
    print(f"Instruments needing fetch: {len(selected_instruments) - non_zero_count}")
    
    if non_zero_count > 0:
        print("✅ UI should now show non-zero LTP values for instruments with data!")
    else:
        print("❌ All instruments still show zero - need to fetch historical data")

if __name__ == "__main__":
    asyncio.run(test_final_live_prices())