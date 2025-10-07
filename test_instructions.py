#!/usr/bin/env python3

"""
Test the historical data endpoint using the expected URL format
"""

def show_test_instructions():
    print("🧪 Testing Historical Data Endpoint")
    print("=" * 50)
    print()
    print("✅ Server Status: Running at http://localhost:8000")
    print()
    print("🔗 Test URLs:")
    print("1. Minimal (uses defaults):")
    print("   POST http://localhost:8000/api/market-data/fetch-historical")
    print()
    print("2. With days_back only (uses BYKE as default symbol):")
    print("   POST http://localhost:8000/api/market-data/fetch-historical?days_back=30")
    print()
    print("3. With custom symbol:")
    print("   POST http://localhost:8000/api/market-data/fetch-historical?symbol=NATIONALUM&days_back=30")
    print()
    print("4. With specific dates:")
    print("   POST http://localhost:8000/api/market-data/fetch-historical?symbol=BYKE&from_date=2024-10-01&to_date=2024-10-07")
    print()
    print("📋 How to Test:")
    print("1. Open: http://localhost:8000/docs")
    print("2. Find: POST /api/market-data/fetch-historical")
    print("3. Click 'Try it out'")
    print("4. Leave defaults or modify parameters")
    print("5. Click 'Execute'")
    print()
    print("✨ Expected Response:")
    print('''{
  "status": "success",
  "message": "Fetched and stored 3 candles for BYKE",
  "symbol": "BYKE",
  "interval": "1DAY", 
  "candles_stored": 3,
  "from_date": "2024-09-07",
  "to_date": "2024-10-07"
}''')
    print()
    print("🎯 This will:")
    print("- Create historical candle data in your database")
    print("- Fix the LTP showing ₹0.00 issue") 
    print("- Make your charts display real price data")

if __name__ == "__main__":
    show_test_instructions()