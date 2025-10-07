#!/usr/bin/env python3

import requests
import json

def test_health():
    try:
        print("Testing health endpoint...")
        response = requests.get("http://localhost:8001/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Health test failed: {e}")
        return False

def test_historical_data():
    try:
        print("Testing historical data endpoint...")
        payload = {
            "symbol": "BYKE",
            "interval": "1DAY",
            "from_date": "2024-12-01", 
            "to_date": "2024-12-31"
        }
        
        response = requests.post(
            "http://localhost:8001/api/market-data/fetch-historical",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"Historical data test failed: {e}")
        return False

if __name__ == "__main__":
    if test_health():
        print("\n" + "="*50)
        test_historical_data()