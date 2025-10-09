#!/usr/bin/env python3
"""
Test PostgreSQL database operations
Run this to verify the database migration is working correctly
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.lib.database import init_database, close_database, db_manager
from backend.services.postgresql_market_data_storage import market_data_storage
from backend.models.market_data_dto import MarketTickDTO, CandleDataDTO, CandleInterval
from backend.utils.logging import get_logger

logger = get_logger(__name__)


async def test_database_connection():
    """Test basic database connectivity"""
    print("🔌 Testing database connection...")
    try:
        await init_database()
        async with db_manager.get_connection() as conn:
            result = await conn.fetchval('SELECT 1')
            if result == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed")
                return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


async def test_schema_creation():
    """Test that all tables and indexes were created"""
    print("\n📋 Testing schema creation...")
    try:
        async with db_manager.get_connection() as conn:
            # Check tables
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            
            table_names = [row['table_name'] for row in tables]
            expected_tables = ['instruments', 'market_ticks', 'candles']
            
            print(f"📊 Found tables: {table_names}")
            
            for table in expected_tables:
                if table in table_names:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} (missing)")
                    return False
            
            # Check indexes
            indexes = await conn.fetch("""
                SELECT indexname FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname LIKE 'idx_%'
                ORDER BY indexname
            """)
            
            index_names = [row['indexname'] for row in indexes]
            print(f"🗂️ Found {len(index_names)} performance indexes")
            
            return len(table_names) >= 3 and len(index_names) > 0
            
    except Exception as e:
        print(f"❌ Schema test error: {e}")
        return False


async def test_tick_operations():
    """Test tick storage and retrieval"""
    print("\n📈 Testing tick operations...")
    try:
        # Create test tick
        test_tick = MarketTickDTO(
            instrument_key="TEST_INSTRUMENT_1",
            symbol="TEST",
            ltp=100.50,
            ltt=int(datetime.now().timestamp()),
            ltq=100,
            cp=99.75,
            volume=1000,
            oi=500,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Store tick
        result = await market_data_storage.store_tick(test_tick)
        if result:
            print("  ✅ Tick storage successful")
        else:
            print("  ❌ Tick storage failed")
            return False
        
        # Test batch storage
        test_ticks = []
        for i in range(5):
            tick = MarketTickDTO(
                instrument_key=f"TEST_INSTRUMENT_{i+2}",
                symbol=f"TEST{i+2}",
                ltp=100.0 + i,
                ltt=int(datetime.now().timestamp()),
                ltq=100,
                cp=99.75,
                volume=1000,
                timestamp=datetime.now(timezone.utc)
            )
            test_ticks.append(tick)
        
        batch_result = await market_data_storage.store_ticks_batch(test_ticks)
        if batch_result == 5:
            print(f"  ✅ Batch tick storage successful ({batch_result} ticks)")
        else:
            print(f"  ❌ Batch tick storage failed (expected 5, got {batch_result})")
            return False
        
        # Retrieve latest ticks
        latest_ticks = await market_data_storage.get_latest_ticks(['TEST_INSTRUMENT_1'])
        if 'TEST_INSTRUMENT_1' in latest_ticks:
            print("  ✅ Tick retrieval successful")
            print(f"    💰 Latest LTP: {latest_ticks['TEST_INSTRUMENT_1']['ltp']}")
        else:
            print("  ❌ Tick retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Tick operations test error: {e}")
        return False


async def test_candle_operations():
    """Test candle storage and retrieval"""
    print("\n🕯️ Testing candle operations...")
    try:
        # Create test candle
        test_candle = CandleDataDTO(
            instrument_key="TEST_INSTRUMENT_1",
            symbol="TEST",
            interval=CandleInterval.ONE_MINUTE,
            timestamp=datetime.now(timezone.utc).replace(second=0, microsecond=0),
            open_price=100.00,
            high_price=101.50,
            low_price=99.50,
            close_price=100.75,
            volume=5000,
            tick_count=50
        )
        
        # Store candle
        result = await market_data_storage.store_candle(test_candle)
        if result:
            print("  ✅ Candle storage successful")
        else:
            print("  ❌ Candle storage failed")
            return False
        
        # Test batch storage
        test_candles = []
        for i in range(3):
            candle = CandleDataDTO(
                instrument_key="TEST_INSTRUMENT_1",
                symbol="TEST",
                interval=CandleInterval.FIVE_MINUTE,
                timestamp=datetime.now(timezone.utc).replace(second=0, microsecond=0),
                open_price=100.00 + i,
                high_price=101.00 + i,
                low_price=99.00 + i,
                close_price=100.50 + i,
                volume=1000 * (i + 1),
                tick_count=10 * (i + 1)
            )
            test_candles.append(candle)
        
        batch_result = await market_data_storage.store_candles_batch(test_candles)
        if batch_result >= 1:  # At least one should be stored
            print(f"  ✅ Batch candle storage successful ({batch_result} candles)")
        else:
            print(f"  ❌ Batch candle storage failed")
            return False
        
        # Retrieve candles
        candles = await market_data_storage.get_candles(
            "TEST_INSTRUMENT_1", 
            CandleInterval.ONE_MINUTE,
            limit=10
        )
        
        if candles and len(candles) > 0:
            print(f"  ✅ Candle retrieval successful ({len(candles)} candles)")
            print(f"    📊 Latest OHLC: {candles[0].open_price:.2f}/{candles[0].high_price:.2f}/{candles[0].low_price:.2f}/{candles[0].close_price:.2f}")
        else:
            print("  ❌ Candle retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Candle operations test error: {e}")
        return False


async def test_performance_queries():
    """Test performance-optimized queries"""
    print("\n⚡ Testing performance queries...")
    try:
        # Test latest prices view
        async with db_manager.get_connection() as conn:
            start_time = datetime.now()
            
            # Test latest prices view
            latest_prices = await conn.fetch("SELECT * FROM latest_prices LIMIT 5")
            
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            print(f"  ✅ Latest prices query: {query_time:.1f}ms ({len(latest_prices)} results)")
            
            # Test aggregation performance
            start_time = datetime.now()
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_ticks,
                    COUNT(DISTINCT instrument_key) as unique_instruments,
                    MAX(timestamp) as latest_tick
                FROM market_ticks
            """)
            
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            print(f"  ✅ Aggregation query: {query_time:.1f}ms")
            print(f"    📊 Total ticks: {stats['total_ticks']}")
            print(f"    🎯 Unique instruments: {stats['unique_instruments']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Performance queries test error: {e}")
        return False


async def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        async with db_manager.get_connection() as conn:
            # Delete test data
            await conn.execute("DELETE FROM market_ticks WHERE instrument_key LIKE 'TEST_INSTRUMENT_%'")
            await conn.execute("DELETE FROM candles WHERE instrument_key LIKE 'TEST_INSTRUMENT_%'")
            await conn.execute("DELETE FROM instruments WHERE instrument_key LIKE 'TEST_INSTRUMENT_%'")
            
        print("  ✅ Test data cleaned up")
        return True
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return False


async def main():
    """Main test function"""
    print("🧪 PostgreSQL Database Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 6
    
    try:
        # Run all tests
        if await test_database_connection():
            tests_passed += 1
        
        if await test_schema_creation():
            tests_passed += 1
            
        if await test_tick_operations():
            tests_passed += 1
            
        if await test_candle_operations():
            tests_passed += 1
            
        if await test_performance_queries():
            tests_passed += 1
            
        if await cleanup_test_data():
            tests_passed += 1
        
        # Results
        print("\n" + "=" * 50)
        if tests_passed == total_tests:
            print("🎉 All tests passed! PostgreSQL is working correctly.")
            print("\n💡 Next steps:")
            print("   1. Set DATABASE_URL in your .env file")
            print("   2. Run migration script if you have existing SQLite data")
            print("   3. Restart your application")
            print("   4. Monitor performance in production")
        else:
            print(f"⚠️ {tests_passed}/{total_tests} tests passed")
            print("Please check the errors above and fix configuration issues")
            
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())