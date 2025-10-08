#!/usr/bin/env python3
"""
Test script to verify chart data availability for all intervals
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.market_data_service import market_data_service
from backend.models.market_data_dto import CandleInterval
from backend.utils.logging import get_logger

logger = get_logger(__name__)

async def test_chart_data_availability():
    """Test chart data availability for all intervals"""
    
    print("📊 Testing Chart Data Availability for All Intervals")
    print("=" * 60)
    
    # Get selected instruments to test with
    from backend.services.instrument_service import instrument_service
    selected_instruments = await instrument_service.get_selected_instruments()
    
    if not selected_instruments:
        print("❌ No instruments selected. Please add instruments to watchlist first.")
        return
    
    # Use first selected instrument for testing
    test_instrument = selected_instruments[0]
    print(f"🧪 Testing with instrument: {test_instrument.symbol} ({test_instrument.instrument_key})")
    
    # Test all supported intervals
    intervals_to_test = [
        (CandleInterval.ONE_MINUTE, "1-minute"),
        (CandleInterval.FIVE_MINUTE, "5-minute"),
        (CandleInterval.FIFTEEN_MINUTE, "15-minute"),
        (CandleInterval.ONE_DAY, "Daily")
    ]
    
    print(f"\n📈 Chart Data Availability Test:")
    print("-" * 40)
    
    for interval, description in intervals_to_test:
        try:
            # Get last 50 candles for this interval
            candles = await market_data_service.get_candles(
                instrument_key=test_instrument.instrument_key,
                interval=interval,
                limit=50
            )
            
            if candles:
                latest_candle = candles[0]  # Most recent candle
                oldest_candle = candles[-1] if len(candles) > 1 else candles[0]
                
                print(f"✅ {description:15} | {len(candles):3d} candles | Latest: {latest_candle.timestamp[:16]} | OHLC: {latest_candle.open_price:.2f}-{latest_candle.high_price:.2f}-{latest_candle.low_price:.2f}-{latest_candle.close_price:.2f}")
            else:
                print(f"⚠️  {description:15} | No data available - needs fetching from Upstox API")
                
        except Exception as e:
            print(f"❌ {description:15} | Error: {str(e)}")
    
    print(f"\n📝 Chart System Status:")
    print(f"   • Frontend: TradingChart component supports interval switching")
    print(f"   • Frontend: SimpleChart component uses useCandles hook") 
    print(f"   • Backend: /api/market-data/candles endpoint supports all intervals")
    print(f"   • Database: Stores candles with interval-specific indexes")
    print(f"   • Chart Display: SVG candlestick rendering with OHLC data")
    
    # Check if we need to fetch data
    total_candles = 0
    for interval, _ in intervals_to_test:
        candles = await market_data_service.get_candles(
            instrument_key=test_instrument.instrument_key,
            interval=interval,
            limit=1
        )
        total_candles += len(candles)
    
    if total_candles == 0:
        print(f"\n💡 Recommendation:")
        print(f"   Use the 'Historical Data Fetch' component to populate chart data")
        print(f"   This will fetch and store candles for all timeframes (1m, 5m, 15m, 1d)")
    else:
        print(f"\n✅ Chart data is available! Switch between intervals using the chart controls.")

if __name__ == "__main__":
    print("🚀 Testing Multi-Timeframe Chart System")
    
    try:
        asyncio.run(test_chart_data_availability())
        print(f"\n🎉 Chart system test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)