"""
Simple test to verify order management system components
"""
import sys
import os
sys.path.append('backend')

def test_imports():
    """Test that all components can be imported"""
    print("🔧 Testing Component Imports...")
    
    try:
        from backend.models.order_dto import PlaceOrderRequest, OrderDetailsDTO
        print("✅ Order DTOs imported successfully")
    except Exception as e:
        print(f"❌ Order DTOs import failed: {e}")
        return False
    
    try:
        from backend.services.order_service import order_service
        print("✅ Order Service imported successfully")
    except Exception as e:
        print(f"❌ Order Service import failed: {e}")
        return False
    
    try:
        from backend.routers.orders import router
        print("✅ Orders Router imported successfully") 
    except Exception as e:
        print(f"❌ Orders Router import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗃️  Testing Database Connection...")
    
    try:
        import asyncio
        from backend.lib.database import db_manager
        
        async def check_db():
            try:
                await db_manager.initialize()
                result = await db_manager.execute_scalar("SELECT 1")
                await db_manager.close()
                return result == 1
            except Exception as e:
                print(f"Database error: {e}")
                return False
        
        result = asyncio.run(check_db())
        if result:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_order_validation():
    """Test order data validation"""
    print("\n📋 Testing Order Validation...")
    
    try:
        from backend.models.order_dto import PlaceOrderRequest, OrderType, OrderSide, ProductType
        
        # Test valid order
        valid_order = PlaceOrderRequest(
            instrument_key="NSE_EQ|INE002A01018",
            quantity=1,
            price=100.50,
            order_type=OrderType.LIMIT,
            order_side=OrderSide.BUY,
            product_type=ProductType.DELIVERY,
            validity="DAY",
            tag="test_order"
        )
        
        print("✅ Valid order creation successful")
        print(f"   Instrument: {valid_order.instrument_key}")
        print(f"   Side: {valid_order.order_side}")
        print(f"   Quantity: {valid_order.quantity}")
        print(f"   Price: {valid_order.price}")
        
        return True
        
    except Exception as e:
        print(f"❌ Order validation failed: {e}")
        return False

def test_database_schema():
    """Test database schema exists"""
    print("\n🏗️  Testing Database Schema...")
    
    try:
        import asyncio
        from backend.lib.database import db_manager
        
        async def check_tables():
            try:
                await db_manager.initialize()
                
                # Check if orders table exists
                result = await db_manager.execute_scalar("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name IN ('orders', 'trades', 'algo_orders', 'portfolio_positions')
                """)
                
                await db_manager.close()
                return result
                
            except Exception as e:
                print(f"Schema check error: {e}")
                return 0
        
        table_count = asyncio.run(check_tables())
        
        if table_count >= 4:
            print(f"✅ Database schema complete: {table_count} tables found")
            return True
        else:
            print(f"❌ Database schema incomplete: only {table_count} tables found")
            return False
            
    except Exception as e:
        print(f"❌ Schema test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Order Management System - Component Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_database_connection,
        test_order_validation,
        test_database_schema
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Order Management System is ready")
    else:
        print("⚠️  Some tests failed - check configuration")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)