#!/usr/bin/env python3
"""
Quick test to verify the updated live-prices endpoint with WebSocket data
"""

import requests
import json

def test_live_prices_endpoint():
    """Test the updated live-prices endpoint"""
    try:
        # Test the backend API endpoint
        async with aiohttp.ClientSession() as session:
            
            # First check if backend is running
            async with session.get('http://localhost:8000/health') as response:
                if response.status == 200:
                    print("✅ Backend is running")
                else:
                    print(f"❌ Backend health check failed: {response.status}")
                    return
            
            # Test the live-prices endpoint (without auth for now)
            try:
                async with session.get('http://localhost:8000/api/market-data/live-prices') as response:
                    print(f"\n📊 Live Prices Endpoint Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Live prices data received:")
                        print(f"   Total instruments: {data.get('total_instruments', 0)}")
                        print(f"   Prices available: {len(data.get('prices', {}))}")
                        
                        # Show sample price data
                        if data.get('prices'):
                            for instrument_key, price_data in list(data['prices'].items())[:2]:
                                print(f"\n   📈 {price_data.get('symbol', instrument_key)}:")
                                print(f"      LTP: {price_data.get('ltp', 0)}")
                                print(f"      Open: {price_data.get('open', 0)}")
                                print(f"      High: {price_data.get('high', 0)}")
                                print(f"      Low: {price_data.get('low', 0)}")
                                print(f"      Volume: {price_data.get('volume', 0)}")
                                print(f"      Source: {price_data.get('source', 'unknown')}")
                        else:
                            print("   ⚠️ No price data available")
                    
                    elif response.status == 401:
                        print("   ⚠️ Authentication required - this is expected")
                        print("   The endpoint is working but needs session token")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Error: {error_text}")
                        
            except Exception as e:
                print(f"❌ Error testing live-prices endpoint: {e}")
            
            # Test market data collection status
            try:
                async with session.get('http://localhost:8000/api/market-data/collection-status') as response:
                    print(f"\n🔌 Collection Status Endpoint: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"   Is collecting: {data.get('is_collecting', False)}")
                        print(f"   Is connected: {data.get('is_connected', False)}")
                        print(f"   Subscribed instruments: {data.get('subscribed_instruments_count', 0)}")
                        print(f"   Total ticks received: {data.get('total_ticks_received', 0)}")
                    elif response.status == 401:
                        print("   ⚠️ Authentication required")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Error: {error_text}")
                        
            except Exception as e:
                print(f"❌ Error testing collection-status endpoint: {e}")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing updated live-prices endpoint...")
    asyncio.run(test_live_prices_endpoint())
    print("\n✨ Test completed!")