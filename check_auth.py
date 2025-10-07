"""
Quick test to verify if you're properly logged in and can access the trading interface
Run this AFTER logging in through the frontend
"""

import requests

def check_auth_status():
    """
    This will fail with 401 if you haven't logged in through the frontend yet.
    That's expected - you need to login first at http://localhost:5173/login
    """
    
    print("🔍 Checking Authentication Status...")
    print("=" * 50)
    
    # Test the endpoints that the trading interface uses
    endpoints_to_test = [
        ("/api/market-data/status", "Market Data Status"),
        ("/api/market-data/live-prices", "Live Prices"),
        ("/api/instruments", "Instruments List")
    ]
    
    for endpoint, name in endpoints_to_test:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}")
            if response.status_code == 200:
                print(f"✅ {name}: Working")
            elif response.status_code == 401:
                print(f"🔐 {name}: Needs login (401)")
            else:
                print(f"❌ {name}: Error {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Connection error - {e}")
    
    print("\n📝 Instructions:")
    print("1. If you see 401 errors, go to: http://localhost:5173/login")
    print("2. Enter your Upstox access token")
    print("3. Click 'Login'")
    print("4. Then navigate to: http://localhost:5173/app/trading")
    print("5. Your professional trading platform will work with live data!")

if __name__ == "__main__":
    check_auth_status()