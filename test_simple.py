import requests

print("Testing backend endpoints...")

try:
    # Test basic health check
    response = requests.get("http://localhost:8000/api/stream/ping", timeout=5)
    print(f"Ping response: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"Ping failed: {e}")

try:
    # Test status endpoint without starting stream
    response = requests.get("http://localhost:8000/api/stream/status", timeout=5)
    print(f"Status response: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        print(f"Status: {response.json()}")
except Exception as e:
    print(f"Status failed: {e}")