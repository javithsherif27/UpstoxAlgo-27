#!/usr/bin/env python3

import requests
import json
import time

def test_health_only():
    try:
        print("Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Health test failed: {e}")
        return False

if __name__ == "__main__":
    test_health_only()