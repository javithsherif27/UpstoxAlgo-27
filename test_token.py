import requests
import json

# Test WebSocket connection with the provided token
token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"

print("🔧 Testing Upstox WebSocket Connection with Token...")
print("=" * 50)

# Test 1: Start stream with sample symbols
print("\n1. Starting market data stream...")
try:
    response = requests.post(
        "http://localhost:8000/api/stream/start",
        headers={
            "Content-Type": "application/json",
            "X-Upstox-Access-Token": token
        },
        json={
            "symbols": ["NIFTY", "BANKNIFTY"],
            "exchange": "NSE"
        },
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.RequestException as e:
    print(f"❌ Error starting stream: {e}")

# Test 2: Check status
print("\n2. Checking market data status...")
try:
    response = requests.get("http://localhost:8000/api/stream/status", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n📊 Market Data Status:")
        print(f"Overall Status: {data.get('overall_status')}")
        
        market_data = data.get('market_data_service', {})
        print(f"WebSocket Connected: {market_data.get('ws_connected')}")
        print(f"Connection Status: {market_data.get('connection_status')}")
        print(f"Data Collection Active: {market_data.get('is_collecting')}")
        print(f"Total Ticks Received: {market_data.get('total_ticks_received', 0)}")
        print(f"Subscribed Instruments: {market_data.get('subscribed_instruments_count', 0)}")
        print(f"Active Candles: {market_data.get('active_candles', 0)}")
        
        if market_data.get('errors'):
            print(f"Recent Errors: {market_data.get('errors')}")
            
    else:
        print(f"❌ Failed to get status: {response.status_code}")
        print(response.text)
        
except requests.exceptions.RequestException as e:
    print(f"❌ Error checking status: {e}")

print("\n" + "=" * 50)
print("🔍 Test completed. Check above for connection results.")