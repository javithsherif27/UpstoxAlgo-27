#!/usr/bin/env python3
"""
Simple test to check live prices API
"""

import requests
import json

def test_apis():
    print("🧪 Testing Live Prices API")
    print("=" * 50)
    
    # Test 1: Backend health
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        print(f"✅ Backend Health: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend not running: {e}")
        return
    
    # Test 2: Live prices (will need auth)
    try:
        response = requests.get('http://localhost:8000/api/market-data/live-prices', timeout=5)
        print(f"\n📊 Live Prices: {response.status_code}")
        if response.status_code == 401:
            print("   ⚠️ Authentication required (normal)")
        elif response.status_code == 200:
            data = response.json()
            print(f"   Data: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"❌ Live prices test failed: {e}")
    
    print("\n💡 To fix LTP showing 0:")
    print("1. Login to the frontend")
    print("2. Select instruments on Instruments page") 
    print("3. Start market data collection")
    print("4. Check Trading workspace")

if __name__ == "__main__":
    test_apis()