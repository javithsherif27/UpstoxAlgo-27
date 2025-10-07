#!/usr/bin/env python3

import requests

def test_minimal():
    try:
        print("Testing minimal server...")
        response = requests.get("http://127.0.0.1:8002/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Minimal test failed: {e}")
        return False

if __name__ == "__main__":
    test_minimal()