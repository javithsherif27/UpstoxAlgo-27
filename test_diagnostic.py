"""
Enhanced diagnostic test for WebSocket subscription
This will help us understand the message format and debug subscription issues
"""
import asyncio
import sys
import json
from datetime import datetime
sys.path.append('D:/source-code/UpstoxAlgo-27')

from backend.services.websocket_client import UpstoxWebSocketClient
from backend.models.market_data_dto import SubscriptionRequest

token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"

# Override message handling to capture raw messages
class DiagnosticWebSocketClient(UpstoxWebSocketClient):
    def __init__(self):
        super().__init__()
        self.raw_messages = []
        self.message_types = {}
        
    async def _handle_message(self, message):
        """Enhanced message handler with detailed logging"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Store raw message
            self.raw_messages.append({
                'timestamp': timestamp,
                'message': message,
                'type': type(message).__name__
            })
            
            print(f"[{timestamp}] 📨 RAW MESSAGE:")
            
            if isinstance(message, bytes):
                print(f"  Type: Binary ({len(message)} bytes)")
                print(f"  Hex: {message[:50].hex()}...")
                
                # Try to decode as text
                try:
                    text = message.decode('utf-8')
                    print(f"  Decoded: {text[:200]}...")
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(text)
                        print(f"  JSON: {json.dumps(data, indent=2)}")
                        await self._handle_json_message(data)
                    except json.JSONDecodeError:
                        print("  Not JSON format")
                        
                except UnicodeDecodeError:
                    print("  Cannot decode as UTF-8")
                    
            elif isinstance(message, str):
                print(f"  Type: Text ({len(message)} chars)")
                print(f"  Content: {message[:500]}...")
                
                try:
                    data = json.loads(message)
                    print(f"  Parsed JSON: {json.dumps(data, indent=2)}")
                    await self._handle_json_message(data)
                except json.JSONDecodeError:
                    print("  Not valid JSON")
            else:
                print(f"  Type: {type(message)}")
                print(f"  Content: {str(message)[:500]}...")
            
            print("-" * 60)
            
        except Exception as e:
            print(f"Error in diagnostic message handler: {e}")
            import traceback
            traceback.print_exc()
            
        # Call parent method for normal processing
        try:
            await super()._handle_message(message)
        except Exception as e:
            print(f"Error in parent message handler: {e}")
    
    async def _handle_json_message(self, data):
        """Enhanced JSON message handler"""
        try:
            msg_type = data.get("type", "unknown")
            self.message_types[msg_type] = self.message_types.get(msg_type, 0) + 1
            
            print(f"🔍 JSON Message Analysis:")
            print(f"  Message Type: {msg_type}")
            print(f"  Keys: {list(data.keys())}")
            
            if msg_type in ["feed", "live_feed", "initial_feed"]:
                feeds = data.get("feeds", {})
                print(f"  Feed Data: {len(feeds)} items")
                for key, feed_data in list(feeds.items())[:3]:  # Show first 3
                    print(f"    {key}: {feed_data}")
            
            # Call parent method
            await super()._handle_json_message(data)
            
        except Exception as e:
            print(f"Error in JSON analysis: {e}")

async def diagnostic_subscription_test():
    """Run diagnostic test with enhanced logging"""
    print("🔍 DIAGNOSTIC WebSocket Subscription Test")
    print("=" * 70)
    
    # Create diagnostic client
    ws_client = DiagnosticWebSocketClient()
    
    def diagnostic_tick_callback(tick):
        print(f"✅ TICK RECEIVED: {tick}")
    
    ws_client.set_tick_callback(diagnostic_tick_callback)
    
    try:
        # Connect
        print("1. Connecting to WebSocket...")
        await ws_client.connect(token)
        await asyncio.sleep(3)
        
        if not ws_client.is_connected:
            print("❌ Failed to connect")
            return
            
        print("✅ Connected successfully")
        
        # Test multiple instrument formats
        instrument_formats = [
            # Format 1: Standard NSE format
            ["NSE_EQ|INFY-EQ", "NSE_EQ|GOLDBEES-EQ"],
            
            # Format 2: Without series
            ["NSE_EQ|INFY", "NSE_EQ|GOLDBEES"],
            
            # Format 3: Different exchange format
            ["NSE|INFY", "NSE|GOLDBEES"],
            
            # Format 4: Index format
            ["NSE_INDEX|NIFTY50", "NSE_INDEX|BANKNIFTY"]
        ]
        
        for i, instruments in enumerate(instrument_formats):
            print(f"\n2.{i+1} Testing instrument format {i+1}: {instruments}")
            
            # Subscribe with different modes
            for mode in ["ltpc", "full", "quote"]:
                print(f"   Testing mode: {mode}")
                
                subscription_request = SubscriptionRequest(
                    instrument_keys=instruments,
                    mode=mode
                )
                
                try:
                    await ws_client.subscribe(subscription_request)
                    print(f"   ✅ Subscription sent for mode {mode}")
                    
                    # Wait for data
                    await asyncio.sleep(10)
                    
                    print(f"   Message types received: {ws_client.message_types}")
                    print(f"   Total messages: {len(ws_client.raw_messages)}")
                    
                    # Check for recent messages
                    recent_messages = ws_client.raw_messages[-5:]
                    if recent_messages:
                        print("   Recent messages:")
                        for msg in recent_messages:
                            print(f"     {msg['timestamp']}: {msg['type']}")
                    
                except Exception as e:
                    print(f"   ❌ Subscription failed for mode {mode}: {e}")
            
            # Unsubscribe before next test
            try:
                await ws_client.unsubscribe(instruments)
                print(f"   Unsubscribed from {instruments}")
            except:
                pass
        
        # Final summary
        print(f"\n3. Final Summary:")
        print(f"   Total messages received: {len(ws_client.raw_messages)}")
        print(f"   Message types: {ws_client.message_types}")
        print(f"   Connection active: {ws_client.is_connected}")
        
        # Save diagnostic data
        try:
            with open('D:/source-code/UpstoxAlgo-27/diagnostic_log.json', 'w') as f:
                json.dump({
                    'message_types': ws_client.message_types,
                    'total_messages': len(ws_client.raw_messages),
                    'sample_messages': [
                        {
                            'timestamp': msg['timestamp'],
                            'type': msg['type'],
                            'content': str(msg['message'])[:500]
                        }
                        for msg in ws_client.raw_messages[:10]
                    ]
                }, f, indent=2)
            print("   📁 Diagnostic data saved to diagnostic_log.json")
        except Exception as e:
            print(f"   ⚠️ Failed to save diagnostic data: {e}")
        
        # Disconnect
        await ws_client.disconnect()
        print("✅ Disconnected")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnostic_subscription_test())