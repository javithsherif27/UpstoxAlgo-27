"""
Startup verification script - ensures both backend and frontend start gracefully
without requiring upfront token configuration
"""

import requests
import time
import sys

def test_backend_startup():
    """Test that backend starts without token issues"""
    print("🔍 Testing Backend Startup (No Token Required)")
    print("=" * 50)
    
    # Test health endpoint (should always work)
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: Working")
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   Message: {health_data.get('message')}")
        else:
            print(f"❌ Health endpoint: Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint: Connection failed - {e}")
        return False
    
    # Test protected endpoints (should return 401, which is correct)
    protected_endpoints = [
        "/api/market-data/status",
        "/api/market-data/live-prices",
        "/api/instruments"
    ]
    
    print("\n🔒 Testing Protected Endpoints (Should Return 401)")
    for endpoint in protected_endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 401:
                print(f"✅ {endpoint}: Properly protected (401)")
            else:
                print(f"⚠️  {endpoint}: Unexpected status {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Connection error - {e}")
    
    return True

def test_frontend_startup():
    """Test that frontend is accessible"""
    print("\n🌐 Testing Frontend Startup")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:5173", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend: Accessible")
            return True
        else:
            print(f"❌ Frontend: Error {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend: Connection failed - {e}")
        print("   Make sure frontend is running with: npm run dev")
        return False

def main():
    print("🚀 Startup Verification - Token-Free Build")
    print("=" * 60)
    
    backend_ok = test_backend_startup()
    frontend_ok = test_frontend_startup()
    
    print("\n" + "=" * 60)
    
    if backend_ok and frontend_ok:
        print("🎉 SUCCESS: Both backend and frontend started successfully!")
        print("\n📋 Next Steps:")
        print("1. Navigate to: http://localhost:5173")
        print("2. Go to Login page")
        print("3. Enter your Upstox access token")
        print("4. Start using the professional trading platform!")
        print("\n✨ The application is ready to receive your token!")
    else:
        print("❌ STARTUP ISSUES DETECTED")
        if not backend_ok:
            print("   • Backend problems - check server logs")
        if not frontend_ok:
            print("   • Frontend problems - ensure npm run dev is running")
    
    return backend_ok and frontend_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)