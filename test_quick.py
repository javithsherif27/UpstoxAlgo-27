import requests
import time

print("Testing with a quick status check...")

try:
    # Just test a simple GET to status
    print("Making request to status endpoint...")
    response = requests.get("http://127.0.0.1:8000/api/stream/status", timeout=3)
    print(f"Response received: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Status endpoint working!")
        print(f"Overall status: {data.get('overall_status')}")
    else:
        print(f"❌ Status endpoint error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Request failed: {e}")

print("Test complete.")