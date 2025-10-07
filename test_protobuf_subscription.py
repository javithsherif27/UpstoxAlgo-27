"""
Test INFY and GOLDBEES subscription with improved protobuf decoding
"""
import asyncio
import sys
from datetime import datetime
sys.path.append('D:/source-code/UpstoxAlgo-27')

from backend.services.websocket_client import UpstoxWebSocketClient
from backend.models.market_data_dto import SubscriptionRequest

token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"

# Track received data
tick_counts = {}
latest_ticks = {}

def on_tick(tick):
    """Enhanced tick callback"""
    symbol = tick.symbol
    
    if symbol not in tick_counts:
        tick_counts[symbol] = 0
    tick_counts[symbol] += 1
    latest_ticks[symbol] = tick
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 📊 {symbol}: LTP={tick.ltp} | Volume={tick.ltq} | Ticks={tick_counts[symbol]}")

async def test_with_protobuf():
    """Test with improved protobuf handling"""
    print("🔄 Testing INFY & GOLDBEES with Protobuf Decoding")
    print("=" * 60)
    
    ws_client = UpstoxWebSocketClient()
    ws_client.set_tick_callback(on_tick)
    
    try:
        # Connect
        print("1️⃣ Connecting to WebSocket...")
        await ws_client.connect(token)
        await asyncio.sleep(2)
        
        if not ws_client.is_connected:
            print("❌ Connection failed")
            return
        
        print(f"✅ Connected at {ws_client.connection_time}")
        
        # Test different instrument formats and modes
        test_cases = [
            {
                "name": "INFY & GOLDBEES (LTPC mode)",
                "instruments": ["NSE_EQ|INFY-EQ", "NSE_EQ|GOLDBEES-EQ"],
                "mode": "ltpc"
            },
            {
                "name": "INFY & GOLDBEES (Full mode)",
                "instruments": ["NSE_EQ|INFY-EQ", "NSE_EQ|GOLDBEES-EQ"],
                "mode": "full"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n2.{i+1} Testing: {test_case['name']}")
            
            # Subscribe
            subscription = SubscriptionRequest(
                instrument_keys=test_case["instruments"],
                mode=test_case["mode"]
            )
            
            await ws_client.subscribe(subscription)
            print(f"   ✅ Subscribed to {len(test_case['instruments'])} instruments in {test_case['mode']} mode")
            
            # Monitor for 30 seconds
            print("   📡 Monitoring data for 30 seconds...")
            
            start_time = asyncio.get_event_loop().time()
            last_status_time = start_time
            
            while asyncio.get_event_loop().time() - start_time < 30:
                current_time = asyncio.get_event_loop().time()
                
                # Status update every 10 seconds
                if current_time - last_status_time >= 10:
                    total_ticks = sum(tick_counts.values())
                    print(f"   📈 Status: {total_ticks} total ticks | Symbols with data: {list(tick_counts.keys())}")
                    last_status_time = current_time
                
                await asyncio.sleep(1)
            
            # Show results for this test
            print(f"   📋 Results for {test_case['name']}:")
            if tick_counts:
                for symbol, count in tick_counts.items():
                    latest = latest_ticks.get(symbol)
                    if latest:
                        print(f"     {symbol}: {count} ticks, Latest LTP: {latest.ltp}")
            else:
                print("     No ticks received")
            
            # Unsubscribe before next test
            try:
                await ws_client.unsubscribe(test_case["instruments"])
                print(f"   🔄 Unsubscribed from {test_case['name']}")
            except:
                pass
            
            # Clear counters for next test
            tick_counts.clear()
            latest_ticks.clear()
        
        # Final summary
        print(f"\n3️⃣ Final Summary:")
        print(f"   Connection Status: {'✅ Active' if ws_client.is_connected else '❌ Disconnected'}")
        print(f"   Subscribed Instruments: {len(ws_client.subscribed_instruments)}")
        print(f"   Connection Duration: {ws_client.connection_time}")
        print(f"   Last Heartbeat: {ws_client.last_heartbeat}")
        
        # Disconnect
        await ws_client.disconnect()
        print("✅ Disconnected successfully")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(test_with_protobuf())
    except KeyboardInterrupt:
        print("\n⏹️ Test stopped by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")