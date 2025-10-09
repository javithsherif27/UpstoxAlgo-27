"""
Test script for Order Management System
Tests all order API endpoints and functionality
"""
import asyncio
import httpx
import json
from datetime import datetime, timezone

BASE_URL = "http://localhost:8002"

async def test_orders_api():
    """Test all orders API endpoints"""
    
    print("🚀 Starting Order Management System API Tests")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Health Check
        print("\n1. Testing Health Check...")
        try:
            response = await client.get(f"{BASE_URL}/api/orders/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health Check: {health_data['status']}")
                print(f"   Sandbox Mode: {health_data['sandbox_mode']}")
                print(f"   Base URL: {health_data['base_url']}")
            else:
                print(f"❌ Health Check Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health Check Error: {e}")
        
        # Test 2: Get Order Book (Empty)
        print("\n2. Testing Order Book (Empty)...")
        try:
            response = await client.get(f"{BASE_URL}/api/orders/book")
            if response.status_code == 200:
                order_book = response.json()
                print(f"✅ Order Book Retrieved")
                print(f"   Total Orders: {order_book['total_orders']}")
                print(f"   Pending: {order_book['pending_orders']}")
                print(f"   Completed: {order_book['completed_orders']}")
            else:
                print(f"❌ Order Book Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Order Book Error: {e}")
        
        # Test 3: Get Trades (Empty)
        print("\n3. Testing Trades List (Empty)...")
        try:
            response = await client.get(f"{BASE_URL}/api/orders/trades")
            if response.status_code == 200:
                trades = response.json()
                print(f"✅ Trades Retrieved: {len(trades)} trades")
            else:
                print(f"❌ Trades Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Trades Error: {e}")
        
        # Test 4: Get Statistics
        print("\n4. Testing Order Statistics...")
        try:
            response = await client.get(f"{BASE_URL}/api/orders/statistics")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Statistics Retrieved")
                print(f"   Period: {stats['period_days']} days")
                print(f"   Total Orders: {stats['total_orders']}")
                print(f"   Success Rate: {stats['success_rate']}%")
            else:
                print(f"❌ Statistics Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Statistics Error: {e}")
        
        # Test 5: Toggle Sandbox Mode
        print("\n5. Testing Sandbox Mode Toggle...")
        try:
            response = await client.post(f"{BASE_URL}/api/orders/sandbox/toggle?enable_sandbox=true")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Sandbox Toggle: {result['mode']}")
                print(f"   Base URL: {result['base_url']}")
            else:
                print(f"❌ Sandbox Toggle Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Sandbox Toggle Error: {e}")
        
        # Test 6: Place Test Order (Will fail without valid token, but tests validation)
        print("\n6. Testing Order Placement (Validation Test)...")
        test_order = {
            "instrument_key": "NSE_EQ|INE002A01018",
            "quantity": 1,
            "price": 100.0,
            "order_type": "LIMIT",
            "order_side": "BUY",
            "product_type": "D",
            "validity": "DAY",
            "tag": "test_order"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/orders/place",
                json=test_order,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                order_result = response.json()
                print(f"✅ Order Placed: {order_result['order_id']}")
            elif response.status_code == 400:
                error_data = response.json()
                print(f"⚠️  Order Validation (Expected): {error_data['detail']}")
            else:
                print(f"❌ Order Placement Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Order Placement Error: {e}")
        
        # Test 7: Test Database Connection
        print("\n7. Testing Database Connection...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Backend Health: {health['status']}")
            else:
                print(f"❌ Backend Health Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Backend Health Error: {e}")

    print("\n" + "=" * 60)
    print("🎯 Order Management System API Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_orders_api())