"""
Quick test to verify the complete market data pipeline with the backend API
"""
import requests
import json

token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"

def test_backend_endpoints():
    """Test backend API endpoints with the token"""
    print("🔧 Testing Backend API Integration")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000"
    headers = {
        "Content-Type": "application/json",
        "X-Upstox-Access-Token": token
    }
    
    try:
        # Test 1: Health check
        print("1️⃣ Testing health endpoint...")
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print(f"   ❌ Backend health check failed: {response.status_code}")
            return
        
        # Test 2: Try simple ping
        print("2️⃣ Testing ping endpoint...")
        try:
            response = requests.post(f"{base_url}/api/stream/ping", timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Ping test: {e}")
        
        # Test 3: Try to start stream (this might have issues due to the server crash we saw earlier)
        print("3️⃣ Testing stream start (if backend is stable)...")
        try:
            response = requests.post(
                f"{base_url}/api/stream/start",
                headers=headers,
                json={"symbols": ["INFY", "GOLDBEES"], "exchange": "NSE"},
                timeout=30
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Stream start successful!")
                print(f"   Response: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   Stream start error: {e}")
        
        print("\n✅ Backend API test completed")
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")

if __name__ == "__main__":
    test_backend_endpoints()