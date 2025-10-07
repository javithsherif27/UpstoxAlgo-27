"""
Direct test of WebSocket connection with Upstox token
This bypasses the FastAPI server to test the core WebSocket functionality
"""
import asyncio
import sys
import os
sys.path.append('D:/source-code/UpstoxAlgo-27')

from backend.services.websocket_client import UpstoxWebSocketClient
from backend.services.instrument_service import InstrumentService

token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"

async def test_websocket_connection():
    """Test WebSocket connection directly"""
    print("🔧 Testing WebSocket Connection with Upstox Token")
    print("=" * 60)
    
    # Create WebSocket client
    ws_client = UpstoxWebSocketClient()
    
    try:
        # Test 1: Get WebSocket URL
        print("1. Getting WebSocket URL from Upstox API v2...")
        ws_url = await ws_client.get_websocket_url(token)
        print(f"✅ WebSocket URL obtained: {ws_url}")
        
        # Test 2: Try to connect (briefly)
        print("\n2. Testing WebSocket connection...")
        await ws_client.connect(token)
        
        # Wait a few seconds to see if connection establishes
        print("   Waiting for connection to establish...")
        await asyncio.sleep(5)
        
        if ws_client.is_connected:
            print("✅ WebSocket connected successfully!")
            print(f"   Connection time: {ws_client.connection_time}")
            print(f"   Subscribed instruments: {len(ws_client.subscribed_instruments)}")
        else:
            print("❌ WebSocket failed to connect")
            if ws_client.errors:
                print(f"   Errors: {ws_client.errors}")
        
        # Test 3: Disconnect
        print("\n3. Disconnecting...")
        await ws_client.disconnect()
        print("✅ Disconnected successfully")
        
    except Exception as e:
        print(f"❌ Error during WebSocket test: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "=" * 60)
    print("WebSocket test completed.")

if __name__ == "__main__":
    print("Starting WebSocket test...")
    try:
        asyncio.run(test_websocket_connection())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()