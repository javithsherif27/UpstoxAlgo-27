#!/usr/bin/env python3
"""
Test script to verify historical data fetching from Upstox works correctly
"""

import requests
import json

def test_historical_data_fetch():
    """Test the historical data fetch endpoint"""
    
    print("🔍 Testing Historical Data Fetch")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check backend health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Backend Health: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend not available: {e}")
        return
    
    # Test 2: Try to fetch historical data (will need auth)
    try:
        response = requests.post(
            f"{base_url}/api/market-data/fetch-historical",
            params={"days_back": 7},
            timeout=30
        )
        
        print(f"\n📊 Historical Data Fetch: {response.status_code}")
        
        if response.status_code == 401:
            print("   ⚠️ Authentication required (expected)")
            print("   📝 To test properly:")
            print("   1. Login through the frontend")
            print("   2. Select instruments on Instruments page")
            print("   3. Use 'Fetch Historical Data' button in Trading workspace")
            
        elif response.status_code == 400:
            data = response.json()
            print(f"   ❌ {data.get('detail', 'Bad Request')}")
            
        elif response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('message', 'Data fetched')}")
            print(f"   📈 Results: {len(data.get('results', []))}")
            
        else:
            print(f"   ❓ Unexpected status: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Historical data test failed: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Next Steps:")
    print("1. Login to the frontend")
    print("2. Go to Instruments page and select stocks")
    print("3. Go to Trading workspace")
    print("4. Click 'Fetch Historical Data' button")
    print("5. LTP should show real historical prices instead of 0")

if __name__ == "__main__":
    test_historical_data_fetch()