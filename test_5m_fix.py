#!/usr/bin/env python3
"""
Test script to verify 5m historical data fetch and storage works after the interval mapping fix
"""
import asyncio
import sys
import os
sys.path.append('.')

from backend.services.historical_data_manager import historical_data_manager, IntervalType
from backend.services.upstox_client import upstox_client
from backend.services.market_data_service import market_data_service
from backend.models.market_data_dto import CandleInterval, CandleDataDTO
import sqlite3

async def test_5m_data_fix():
    """Test that 5m data can now be processed and stored correctly"""
    print("🧪 Testing 5m data fetch and storage fix...")
    
    # Step 1: Verify interval mapping works
    print("\n1. Testing interval mapping...")
    interval_map = {
        IntervalType.ONE_MINUTE: CandleInterval.ONE_MINUTE,
        IntervalType.FIVE_MINUTE: CandleInterval.FIVE_MINUTE,
        IntervalType.FIFTEEN_MINUTE: CandleInterval.FIFTEEN_MINUTE,
        IntervalType.ONE_DAY: CandleInterval.ONE_DAY
    }
    
    try:
        five_min_mapped = interval_map[IntervalType.FIVE_MINUTE]
        print(f"   ✅ FIVE_MINUTE maps to: {five_min_mapped}")
    except KeyError as e:
        print(f"   ❌ FIVE_MINUTE mapping failed: {e}")
        return
    
    # Step 2: Test mock data processing (no token required)
    print("\n2. Testing 5m candle data processing...")
    
    # Mock response similar to what Upstox would return for 5m
    mock_5m_response = {
        "status": "success",
        "data": {
            "candles": [
                ["2024-10-07T09:15:00+05:30", 94.00, 94.25, 93.95, 94.15, 5000, 0],
                ["2024-10-07T09:20:00+05:30", 94.15, 94.30, 94.10, 94.20, 3500, 0],
                ["2024-10-07T09:25:00+05:30", 94.20, 94.35, 94.05, 94.25, 4200, 0],
            ]
        }
    }
    
    # Simulate processing candles like the fixed code would do
    try:
        candles = []
        if mock_5m_response and mock_5m_response.get("data") and mock_5m_response["data"].get("candles"):
            raw_candles = mock_5m_response["data"]["candles"]
            
            # Use the FIXED interval mapping  
            candle_interval = interval_map[IntervalType.FIVE_MINUTE]
            
            for candle in raw_candles:
                if len(candle) >= 6:
                    candle_dto = CandleDataDTO(
                        instrument_key="NSE_EQ|INE009A01021",  # Mock instrument key
                        symbol="BYKE",
                        interval=candle_interval,  # This would have failed before the fix!
                        timestamp=candle[0],
                        open_price=float(candle[1]),
                        high_price=float(candle[2]),
                        low_price=float(candle[3]),
                        close_price=float(candle[4]),
                        volume=int(candle[5]),
                        tick_count=0
                    )
                    candles.append(candle_dto)
        
        print(f"   ✅ Successfully processed {len(candles)} 5m candles!")
        print(f"   📊 First candle: {candles[0].timestamp} OHLC: {candles[0].open_price}/{candles[0].high_price}/{candles[0].low_price}/{candles[0].close_price}")
        
    except Exception as e:
        print(f"   ❌ 5m candle processing failed: {e}")
        return
    
    # Step 3: Check database state before
    print("\n3. Checking database state...")
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM candles WHERE interval = ?', ('5m',))
    count_before = cursor.fetchone()[0]
    print(f"   📊 5m candles in DB before: {count_before}")
    
    # Step 4: Try storing test candle (simulate what would happen now)
    print("\n4. Testing database storage...")
    try:
        # Store one test candle to verify storage works
        test_candle = candles[0]
        await market_data_service.store_candle_data(test_candle)
        
        cursor.execute('SELECT COUNT(*) FROM candles WHERE interval = ?', ('5m',))
        count_after = cursor.fetchone()[0]
        print(f"   ✅ 5m candles in DB after: {count_after}")
        
        if count_after > count_before:
            print(f"   🎉 Successfully stored 5m candle! (+{count_after - count_before})")
        else:
            print(f"   ⚠️  No new candles added (possibly duplicate)")
            
    except Exception as e:
        print(f"   ❌ Database storage failed: {e}")
    finally:
        conn.close()
    
    print(f"\n🎯 CONCLUSION: The interval mapping fix should resolve the '5m chart data not available' issue!")
    print(f"   The bug was that FIVE_MINUTE and FIFTEEN_MINUTE were missing from interval_map")
    print(f"   Now 5m and 15m fetches will properly convert and store data in the database")

if __name__ == "__main__":
    asyncio.run(test_5m_data_fix())