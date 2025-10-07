#!/usr/bin/env python3

import asyncio

async def test_upstox_client():
    """Test the upstox_client import and mock data"""
    try:
        from backend.services.upstox_client import upstox_client
        print("✅ Successfully imported upstox_client")
        
        # Test historical candles without token (should return mock data)
        result = await upstox_client.get_historical_candles(
            instrument_key="NSE_EQ|INE009A01021", 
            interval="day",
            from_date="2024-09-07",
            to_date="2024-10-07"
        )
        
        print("✅ Historical candles test successful:")
        print(f"   Status: {result.get('status')}")
        print(f"   Candles: {len(result.get('data', {}).get('candles', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_upstox_client())