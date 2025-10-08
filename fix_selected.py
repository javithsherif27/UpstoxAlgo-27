#!/usr/bin/env python3
"""Manually add BYKE to selected instruments"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.services.instrument_service import instrument_service
from backend.models.dto import InstrumentDTO, SelectedInstrumentDTO
from datetime import datetime, timezone
import json

async def add_byke_manually():
    print("=== MANUALLY ADDING BYKE TO SELECTED INSTRUMENTS ===")
    
    # Create BYKE instrument manually since cache is empty
    byke_instrument = InstrumentDTO(
        instrument_key="NSE_EQ|INE319B01014",
        symbol="BYKE",
        name="THE BYKE HOSPITALITY LTD",
        exchange="NSE_EQ"
    )
    
    print(f"Adding {byke_instrument.symbol} ({byke_instrument.instrument_key})")
    
    # Add to selected instruments
    await instrument_service.add_selected_instrument(byke_instrument)
    
    # Verify
    selected = await instrument_service.get_selected_instruments()
    print(f"Selected instruments: {len(selected)}")
    for inst in selected:
        print(f"  - {inst.symbol} ({inst.instrument_key})")
    
    print("\nNow test live prices again...")
    
    # Import and test live prices logic
    from backend.services.market_data_service import market_data_service
    from backend.models.market_data_dto import CandleInterval
    
    if selected:
        instrument = selected[0]  # BYKE
        print(f"\nTesting live prices for {instrument.symbol}:")
        
        # Get candles
        daily_candles = await market_data_service.get_candles(
            instrument_key=instrument.instrument_key,
            interval=CandleInterval.ONE_DAY,
            limit=2
        )
        
        if daily_candles:
            latest_candle = daily_candles[0]
            print(f"Latest daily candle: O={latest_candle.open_price} H={latest_candle.high_price} L={latest_candle.low_price} C={latest_candle.close_price}")
            
            ltp = latest_candle.close_price
            
            # Calculate change
            if len(daily_candles) >= 2:
                prev_close = daily_candles[1].close_price
                change = ltp - prev_close
                change_pct = (change / prev_close) * 100
                print(f"Change vs prev close ({prev_close}): {change} ({change_pct:.2f}%)")
            else:
                change = ltp - latest_candle.open_price
                change_pct = ((ltp - latest_candle.open_price) / latest_candle.open_price * 100) if latest_candle.open_price > 0 else 0
                print(f"Change vs open ({latest_candle.open_price}): {change} ({change_pct:.2f}%)")
            
            price_data = {
                "symbol": instrument.symbol,
                "ltp": ltp,
                "open": latest_candle.open_price,
                "high": latest_candle.high_price,
                "low": latest_candle.low_price,
                "volume": latest_candle.volume,
                "change": change,
                "change_percent": change_pct,
                "source": "candle"
            }
            
            print(f"Final price data: {json.dumps(price_data, indent=2, default=str)}")
        else:
            print("No candles found!")

if __name__ == "__main__":
    asyncio.run(add_byke_manually())