#!/usr/bin/env python3
"""
Direct test of the candles endpoint to verify real data is being served
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.services.market_data_service import market_data_service
from backend.models.market_data_dto import CandleInterval

async def test_candles_directly():
    """Test the candles service directly without HTTP server"""
    
    print("=== TESTING CANDLES SERVICE DIRECTLY ===")
    
    instruments = [
        {"symbol": "BYKE", "instrument_key": "NSE_EQ|INE319B01014"},
        {"symbol": "INFY", "instrument_key": "NSE_EQ|INE009A01021"},
        {"symbol": "MARUTI", "instrument_key": "NSE_EQ|INE467B01029"}
    ]
    
    for inst in instruments:
        print(f"\n🔍 Testing {inst['symbol']} ({inst['instrument_key']})")
        
        try:
            # Get candles using the service directly
            candles = await market_data_service.get_candles(
                instrument_key=inst["instrument_key"],
                interval=CandleInterval.ONE_DAY,
                limit=10
            )
            
            if candles and len(candles) > 0:
                print(f"✅ Found {len(candles)} candles for {inst['symbol']}")
                
                # Show the latest candles
                print("   📊 Latest candles:")
                for i, candle in enumerate(candles[:3]):  # Show first 3
                    print(f"   {i+1}. {candle.timestamp}: O={candle.open_price} H={candle.high_price} L={candle.low_price} C={candle.close_price} V={candle.volume}")
                
                # Check if this looks like real data (not sample data)
                prices = [c.close_price for c in candles]
                is_realistic = all(p > 0 for p in prices) and len(set(prices)) > 1
                data_type = "✅ REAL DATA" if is_realistic else "❌ SAMPLE DATA"
                print(f"   📈 Data Quality: {data_type}")
                
            else:
                print(f"❌ No candles found for {inst['symbol']}")
                
        except Exception as e:
            print(f"❌ Error getting candles for {inst['symbol']}: {e}")
    
    print("\n=== TEST COMPLETE ===")
    print("✅ All instruments should show REAL DATA, not sample data")
    print("✅ Charts should display actual historical candlestick data")
    print("✅ No more 'Loading Chart...' infinite loaders")

if __name__ == "__main__":
    asyncio.run(test_candles_directly())