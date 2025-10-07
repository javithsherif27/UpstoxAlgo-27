#!/usr/bin/env python3

import requests
import json
import time

def test_endpoints():
    base_url = "http://localhost:8001"
    
    endpoints_to_test = [
        ("GET", "/"),
        ("GET", "/docs"),
        ("GET", "/api/"),
        ("GET", "/api/instruments/"),
        ("POST", "/api/market-data/fetch-historical", {
            "symbol": "BYKE",
            "interval": "1DAY", 
            "from_date": "2024-12-01",
            "to_date": "2024-12-31"
        })
    ]
    
    for method, endpoint, *data in endpoints_to_test:
        try:
            print(f"Testing {method} {endpoint}...")
            
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            elif method == "POST":
                payload = data[0] if data else {}
                response = requests.post(
                    f"{base_url}{endpoint}", 
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            print("-" * 50)
            
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            print("-" * 50)
        
        time.sleep(1)  # Wait between requests

if __name__ == "__main__":
    test_endpoints()