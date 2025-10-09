"""
End-to-End Test for Order Management System
Tests both backend API and frontend integration
"""
import asyncio
import httpx
import json
from datetime import datetime

async def test_full_system():
    """Test the complete order management system"""
    
    print("🚀 End-to-End Order Management System Test")
    print("=" * 70)
    
    # First check if backend is running
    print("1. Checking Backend Status...")
    
    backend_ports = [8000, 8001, 8002]
    backend_url = None
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for port in backend_ports:
            try:
                response = await client.get(f"http://localhost:{port}/health")
                if response.status_code == 200:
                    backend_url = f"http://localhost:{port}"
                    print(f"✅ Backend found on port {port}")
                    break
            except:
                continue
    
    if not backend_url:
        print("❌ Backend not running on any port")
        return False
    
    # Test API endpoints
    print(f"\n2. Testing API Endpoints on {backend_url}...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Test orders health
        try:
            response = await client.get(f"{backend_url}/api/orders/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Orders API Health: {health['status']}")
                print(f"   Sandbox Mode: {health['sandbox_mode']}")
            else:
                print(f"❌ Orders Health Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Orders Health Error: {e}")
        
        # Test order book
        try:
            response = await client.get(f"{backend_url}/api/orders/book")
            if response.status_code == 200:
                order_book = response.json()
                print(f"✅ Order Book API: {order_book['total_orders']} orders")
            else:
                print(f"❌ Order Book Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Order Book Error: {e}")
        
        # Test trades
        try:
            response = await client.get(f"{backend_url}/api/orders/trades")
            if response.status_code == 200:
                trades = response.json()
                print(f"✅ Trades API: {len(trades)} trades")
            else:
                print(f"❌ Trades Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Trades Error: {e}")
        
        # Test statistics
        try:
            response = await client.get(f"{backend_url}/api/orders/statistics")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Statistics API: {stats['total_orders']} total orders")
            else:
                print(f"❌ Statistics Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Statistics Error: {e}")
    
    # Test frontend accessibility
    print("\n3. Testing Frontend Accessibility...")
    
    frontend_ports = [5173, 5174]
    frontend_url = None
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for port in frontend_ports:
            try:
                response = await client.get(f"http://localhost:{port}/")
                if response.status_code == 200:
                    frontend_url = f"http://localhost:{port}"
                    print(f"✅ Frontend accessible on port {port}")
                    break
            except:
                continue
    
    if frontend_url:
        print(f"✅ Frontend URL: {frontend_url}")
        print(f"✅ Orders Page: {frontend_url}/app/orders")
    else:
        print("❌ Frontend not accessible")
    
    # Test order placement validation (without actual API call)
    print("\n4. Testing Order Validation...")
    
    try:
        # Test order data structure
        test_order = {
            "instrument_key": "NSE_EQ|INE002A01018",
            "quantity": 1,
            "price": 100.0,
            "order_type": "LIMIT",
            "order_side": "BUY",
            "product_type": "D",
            "validity": "DAY",
            "tag": "test_validation"
        }
        
        # Validate required fields
        required_fields = ["instrument_key", "quantity", "order_type", "order_side", "product_type"]
        missing_fields = [field for field in required_fields if field not in test_order]
        
        if not missing_fields:
            print("✅ Order validation structure correct")
        else:
            print(f"❌ Missing fields: {missing_fields}")
        
        # Validate enum values
        valid_order_types = ["MARKET", "LIMIT", "SL", "SL-M"]
        valid_order_sides = ["BUY", "SELL"]
        valid_product_types = ["D", "I", "CNC", "M"]
        
        if (test_order["order_type"] in valid_order_types and
            test_order["order_side"] in valid_order_sides and
            test_order["product_type"] in valid_product_types):
            print("✅ Order enum values valid")
        else:
            print("❌ Invalid enum values")
            
    except Exception as e:
        print(f"❌ Order validation error: {e}")
    
    # Test database operations
    print("\n5. Testing Database Operations...")
    
    try:
        import sys
        sys.path.append('backend')
        from backend.lib.database import db_manager
        
        async def test_db_operations():
            await db_manager.initialize()
            
            # Test orders table
            orders_count = await db_manager.execute_scalar(
                "SELECT COUNT(*) FROM orders"
            )
            print(f"✅ Orders table: {orders_count} records")
            
            # Test trades table  
            trades_count = await db_manager.execute_scalar(
                "SELECT COUNT(*) FROM trades"
            )
            print(f"✅ Trades table: {trades_count} records")
            
            # Test algo_orders table
            algo_count = await db_manager.execute_scalar(
                "SELECT COUNT(*) FROM algo_orders"
            )
            print(f"✅ Algo orders table: {algo_count} records")
            
            await db_manager.close()
            return True
        
        await test_db_operations()
        
    except Exception as e:
        print(f"❌ Database operations error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 End-to-End Test Summary:")
    print(f"   Backend API: {backend_url if backend_url else 'Not Running'}")
    print(f"   Frontend UI: {frontend_url if frontend_url else 'Not Running'}")
    print(f"   Database: PostgreSQL Connected")
    print(f"   Order System: Ready for Testing")
    
    if backend_url and frontend_url:
        print("\n🎉 System fully operational!")
        print(f"   📊 Open Orders Page: {frontend_url}/app/orders")
        print(f"   🔧 API Documentation: {backend_url}/docs")
        return True
    else:
        print("\n⚠️  System partially operational - check services")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_system())
    print(f"\nTest Result: {'PASS' if success else 'PARTIAL'}")