#!/usr/bin/env python3

import sys
import asyncio
import traceback
import json

async def test_historical_endpoint():
    try:
        # Import our backend components
        sys.path.append('.')
        from backend.routers.market_data import fetch_historical_data
        from backend.models.market_data_dto import FetchHistoricalRequest
        
        print("✅ Imported historical endpoint function")
        
        # Create a test request
        request = FetchHistoricalRequest(
            symbol="BYKE",
            interval="1DAY", 
            from_date="2024-12-01",
            to_date="2024-12-31"
        )
        
        print(f"✅ Created request: {request}")
        
        # Try to call the function directly
        result = await fetch_historical_data(request)
        print(f"✅ Success! Result: {result}")
        
    except Exception as e:
        print(f"❌ Error in historical endpoint:")
        print(f"Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_historical_endpoint())