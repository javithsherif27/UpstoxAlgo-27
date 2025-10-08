#!/usr/bin/env python3
"""
Fetch real historical data for INFY and MARUTI using Upstox API
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.services.upstox_client import upstox_client
from backend.services.instrument_service import instrument_service
from backend.services.market_data_service import market_data_service
from backend.models.market_data_dto import CandleDataDTO, CandleInterval
from datetime import datetime, timedelta

# Token from test files (might be expired)
token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"

async def fetch_real_historical_data():
    """Fetch real historical data for INFY and MARUTI"""
    
    print("=== FETCHING REAL HISTORICAL DATA ===")
    
    # Calculate date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")
    
    print(f"Date range: {from_date} to {to_date}")
    
    instruments_to_fetch = [
        {
            "symbol": "INFY",
            "instrument_key": "NSE_EQ|INE009A01021"
        },
        {
            "symbol": "MARUTI", 
            "instrument_key": "NSE_EQ|INE467B01029"
        }
    ]
    
    results = []
    
    for inst in instruments_to_fetch:
        print(f"\n🔍 Fetching data for {inst['symbol']} ({inst['instrument_key']})")
        
        try:
            # Try to fetch historical data using the upstox client
            historical_response = await upstox_client.get_historical_candles(
                instrument_key=inst["instrument_key"],
                interval="day",
                from_date=from_date,
                to_date=to_date,
                token=token
            )
            
            # Extract candles from the response
            historical_data = []
            if historical_response and historical_response.get("data") and historical_response["data"].get("candles"):
                candles = historical_response["data"]["candles"]
                
                # Convert to CandleDataDTO format
                for candle in candles:
                    # Upstox candle format: [timestamp, open, high, low, close, volume, open_interest]
                    if len(candle) >= 6:
                        candle_dto = CandleDataDTO(
                            instrument_key=inst["instrument_key"],
                            symbol=inst["symbol"],
                            interval=CandleInterval.ONE_DAY,
                            timestamp=candle[0],
                            open_price=float(candle[1]),
                            high_price=float(candle[2]),
                            low_price=float(candle[3]),
                            close_price=float(candle[4]),
                            volume=int(candle[5]),
                            tick_count=0
                        )
                        historical_data.append(candle_dto)
            
            if historical_data and len(historical_data) > 0:
                print(f"✅ Fetched {len(historical_data)} candles for {inst['symbol']}")
                
                # Save to database
                for candle in historical_data:
                    await market_data_service.store_candle_data(candle)
                
                results.append({
                    "symbol": inst["symbol"],
                    "instrument_key": inst["instrument_key"],
                    "candles_count": len(historical_data),
                    "status": "success"
                })
            else:
                print(f"❌ No data fetched for {inst['symbol']}")
                results.append({
                    "symbol": inst["symbol"],
                    "instrument_key": inst["instrument_key"],
                    "candles_count": 0,
                    "status": "no_data"
                })
                
        except Exception as e:
            print(f"❌ Error fetching data for {inst['symbol']}: {e}")
            results.append({
                "symbol": inst["symbol"],
                "instrument_key": inst["instrument_key"],
                "error": str(e),
                "status": "error"
            })
    
    print("\n=== FETCH SUMMARY ===")
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['symbol']}: {result.get('candles_count', 0)} candles")
        if result["status"] == "error":
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    asyncio.run(fetch_real_historical_data())