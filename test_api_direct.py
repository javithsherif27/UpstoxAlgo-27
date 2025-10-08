#!/usr/bin/env python3
"""Test the live-prices API endpoint directly"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.routers.market_data import get_live_prices
from backend.services.auth_service import SessionData

# Mock session data
class MockSession:
    def __init__(self):
        self.user_id = "test_user"

async def test_api_endpoint():
    print("=== TESTING LIVE-PRICES API ENDPOINT ===")
    
    mock_session = MockSession()
    
    try:
        result = await get_live_prices(mock_session)
        print(f"API Response: {result}")
        
        if isinstance(result, dict) and "prices" in result:
            prices = result["prices"]
            print(f"\nFound prices for {len(prices)} instruments:")
            
            for instrument_key, price_data in prices.items():
                symbol = price_data.get("symbol", "Unknown")
                ltp = price_data.get("ltp", 0)
                change = price_data.get("change", 0)
                change_pct = price_data.get("change_percent", 0)
                source = price_data.get("source", "unknown")
                
                print(f"  {symbol}: LTP=₹{ltp:.2f}, Change=₹{change:.2f} ({change_pct:.2f}%) [from {source}]")
        else:
            print(f"Unexpected result format: {result}")
            
    except Exception as e:
        print(f"Error calling API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_endpoint())