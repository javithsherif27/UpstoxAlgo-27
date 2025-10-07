"""
Test WebSocket subscription with INFY and GOLDBEES
This will verify the complete market data flow
"""
import asyncio
import sys
import json
from datetime import datetime
sys.path.append('D:/source-code/UpstoxAlgo-27')

from backend.services.websocket_client import UpstoxWebSocketClient
from backend.models.market_data_dto import SubscriptionRequest, MarketTickDTO

token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"

# Global counters and data
tick_data = {}
total_ticks = 0
connection_events = []

def log_event(message):
    """Log events with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    event = f"[{timestamp}] {message}"
    connection_events.append(event)
    print(event)

def on_tick_received(tick):
    """Enhanced tick callback with detailed logging"""
    global total_ticks, tick_data
    total_ticks += 1
    
    # Store tick data
    symbol = tick.symbol if hasattr(tick, 'symbol') else 'UNKNOWN'
    if symbol not in tick_data:
        tick_data[symbol] = []
    
    tick_info = {
        'timestamp': tick.timestamp if hasattr(tick, 'timestamp') else datetime.now(),
        'ltp': tick.ltp if hasattr(tick, 'ltp') else None,
        'volume': tick.ltq if hasattr(tick, 'ltq') else None,
        'instrument_key': tick.instrument_key if hasattr(tick, 'instrument_key') else None
    }
    tick_data[symbol].append(tick_info)
    
    log_event(f"📊 TICK #{total_ticks}: {symbol} LTP={tick_info['ltp']} VOL={tick_info['volume']}")

async def on_connected():
    """Connection established callback"""
    log_event("🟢 WebSocket CONNECTION ESTABLISHED")

async def on_disconnected():
    """Connection lost callback"""
    log_event("🔴 WebSocket CONNECTION LOST")

async def test_infy_goldbees_subscription():
    """Test subscription to INFY and GOLDBEES"""
    log_event("🚀 Starting INFY & GOLDBEES WebSocket Test")
    log_event("=" * 80)
    
    # Create WebSocket client
    ws_client = UpstoxWebSocketClient()
    ws_client.set_tick_callback(on_tick_received)
    ws_client.set_connection_callbacks(
        on_connected=on_connected,
        on_disconnected=on_disconnected
    )
    
    try:
        # Step 1: Get WebSocket URL
        log_event("1️⃣ Getting WebSocket URL from Upstox API...")
        ws_url = await ws_client.get_websocket_url(token)
        log_event(f"✅ WebSocket URL: {ws_url}")
        
        # Step 2: Connect
        log_event("2️⃣ Establishing WebSocket connection...")
        await ws_client.connect(token)
        
        # Wait for connection to establish
        await asyncio.sleep(3)
        
        if not ws_client.is_connected:
            log_event("❌ Failed to establish connection")
            return
            
        log_event(f"✅ Connection established at {ws_client.connection_time}")
        
        # Step 3: Subscribe to INFY and GOLDBEES
        log_event("3️⃣ Subscribing to instruments...")
        
        # Upstox instrument key format: EXCHANGE_SEGMENT|SYMBOL-SERIES
        test_instruments = [
            "NSE_EQ|INFY-EQ",      # Infosys
            "NSE_EQ|GOLDBEES-EQ"   # Gold BeES ETF
        ]
        
        log_event(f"   Instruments to subscribe: {test_instruments}")
        
        subscription_request = SubscriptionRequest(
            instrument_keys=test_instruments,
            mode="full"  # Use 'full' mode to get more complete data
        )
        
        await ws_client.subscribe(subscription_request)
        log_event(f"✅ Subscription request sent for {len(test_instruments)} instruments")
        
        # Step 4: Monitor data for 60 seconds
        log_event("4️⃣ Monitoring market data (60 seconds)...")
        log_event("   Note: Data availability depends on market hours")
        
        start_time = asyncio.get_event_loop().time()
        last_report_time = start_time
        
        while asyncio.get_event_loop().time() - start_time < 60:
            current_time = asyncio.get_event_loop().time()
            
            # Report every 10 seconds
            if current_time - last_report_time >= 10:
                log_event(f"📈 Status Update: {total_ticks} ticks received so far")
                log_event(f"   Subscribed instruments: {len(ws_client.subscribed_instruments)}")
                log_event(f"   Connection active: {ws_client.is_connected}")
                last_report_time = current_time
            
            await asyncio.sleep(1)
        
        # Step 5: Final summary
        log_event("5️⃣ Test Summary")
        log_event("=" * 50)
        log_event(f"Total ticks received: {total_ticks}")
        log_event(f"Unique symbols: {list(tick_data.keys())}")
        log_event(f"Connection duration: {ws_client.connection_time}")
        log_event(f"Last heartbeat: {ws_client.last_heartbeat}")
        
        # Detailed per-symbol analysis
        for symbol, ticks in tick_data.items():
            if ticks:
                latest = ticks[-1]
                log_event(f"📊 {symbol}: {len(ticks)} ticks, Latest LTP: {latest['ltp']}")
        
        # Check if we got any data
        if total_ticks == 0:
            log_event("⚠️  No ticks received - possible reasons:")
            log_event("   • Market may be closed")
            log_event("   • Instruments may be suspended")
            log_event("   • Subscription format might need adjustment")
            log_event("   • Check if token has market data permissions")
        else:
            log_event("✅ Market data successfully received!")
        
        # Step 6: Disconnect
        log_event("6️⃣ Disconnecting...")
        await ws_client.disconnect()
        log_event("✅ Disconnected successfully")
        
    except Exception as e:
        log_event(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    # Save detailed log for analysis
    try:
        with open('D:/source-code/UpstoxAlgo-27/websocket_test_log.txt', 'w') as f:
            f.write("INFY & GOLDBEES WebSocket Test Log\n")
            f.write("=" * 50 + "\n")
            for event in connection_events:
                f.write(event + "\n")
            
            f.write("\nDetailed Tick Data:\n")
            f.write("=" * 30 + "\n")
            for symbol, ticks in tick_data.items():
                f.write(f"\n{symbol} ({len(ticks)} ticks):\n")
                for i, tick in enumerate(ticks[-5:]):  # Last 5 ticks per symbol
                    f.write(f"  {i+1}. {tick['timestamp']} - LTP: {tick['ltp']}, VOL: {tick['volume']}\n")
        
        log_event("📝 Detailed log saved to websocket_test_log.txt")
        
    except Exception as e:
        log_event(f"⚠️  Failed to save log: {e}")
        
    log_event("🏁 Test completed!")
    return total_ticks > 0

if __name__ == "__main__":
    print("Starting INFY & GOLDBEES WebSocket test...")
    try:
        result = asyncio.run(test_infy_goldbees_subscription())
        if result:
            print("\n✅ SUCCESS: Market data was received!")
        else:
            print("\n⚠️  WARNING: No market data received (check log for details)")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()