#!/usr/bin/env python3

import asyncio
import httpx

async def test_historical_endpoint():
    """Test the historical endpoint with query parameters"""
    
    url = "http://localhost:8000/api/market-data/fetch-historical"
    
    # Test with query parameters like user is using
    params = {
        "symbol": "BYKE", 
        "days_back": 30
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, timeout=30)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_historical_endpoint())