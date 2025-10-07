"""
Complete test of market data collection with WebSocket subscription
"""
import asyncio
import sys
sys.path.append('D:/source-code/UpstoxAlgo-27')

from backend.services.websocket_client import UpstoxWebSocketClient
from backend.models.market_data_dto import SubscriptionRequest

token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"

tick_count = 0

def on_tick_received(tick):
    """Callback for when ticks are received"""
    global tick_count
    tick_count += 1
    print(f"📊 Tick #{tick_count}: {tick.symbol} LTP={tick.ltp} at {tick.timestamp}")

async def test_market_data_collection():
    """Test complete market data collection flow"""
    print("🚀 Testing Complete Market Data Collection")
    print("=" * 70)
    
    # Create WebSocket client
    ws_client = UpstoxWebSocketClient()
    ws_client.set_tick_callback(on_tick_received)
    
    try:
        # Step 1: Connect
        print("1. Connecting to WebSocket...")
        await ws_client.connect(token)
        
        if not ws_client.is_connected:
            print("❌ Failed to connect")
            return
            
        print("✅ Connected successfully!")
        
        # Step 2: Subscribe to some instruments
        print("\n2. Subscribing to market data...")
        
        # Common instrument keys (these might need to be adjusted based on actual Upstox format)
        test_instruments = [
            "NSE_INDEX|Nifty 50",           # NIFTY
            "NSE_INDEX|Nifty Bank",         # BANK NIFTY
            "NSE_EQ|RELIANCE-EQ",           # Reliance
            "NSE_EQ|TCS-EQ"                 # TCS
        ]
        
        subscription_request = SubscriptionRequest(
            instrument_keys=test_instruments,
            mode="ltpc"  # Last Traded Price and Close
        )
        
        await ws_client.subscribe(subscription_request)
        print(f"✅ Subscribed to {len(test_instruments)} instruments")
        
        # Step 3: Listen for data
        print("\n3. Listening for market data (30 seconds)...")
        print("   (Market might be closed, so data may be limited)")
        
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < 30:
            await asyncio.sleep(1)
            if tick_count > 0:
                print(f"   Total ticks received so far: {tick_count}")
        
        print(f"\n📈 Data collection summary:")
        print(f"   Total ticks received: {tick_count}")
        print(f"   Connection time: {ws_client.connection_time}")
        print(f"   Last heartbeat: {ws_client.last_heartbeat}")
        
        # Step 4: Disconnect
        print("\n4. Disconnecting...")
        await ws_client.disconnect()
        print("✅ Disconnected successfully")
        
    except Exception as e:
        print(f"❌ Error during market data test: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "=" * 70)
    print("Market data collection test completed.")
    print(f"Final tick count: {tick_count}")

if __name__ == "__main__":
    print("Starting complete market data test...")
    try:
        asyncio.run(test_market_data_collection())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()