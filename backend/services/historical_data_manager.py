#!/usr/bin/env python3
"""
Enhanced Historical Data Service with Rate Limiting and Multiple Timeframes
Supports 1m, 5m, 15m, and 1d candles with proper Upstox API rate limiting
"""
import asyncio
import sys
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import time

sys.path.append(os.path.dirname(__file__))

from backend.services.upstox_client import upstox_client
from backend.services.instrument_service import instrument_service
from backend.services.market_data_service import market_data_service
from backend.models.market_data_dto import CandleDataDTO, CandleInterval
from backend.models.dto import InstrumentDTO
from backend.utils.logging import get_logger

logger = get_logger(__name__)

class IntervalType(Enum):
    """Supported candle intervals (using V3 API format)"""
    ONE_MINUTE = "1m"        # V3 API: minutes/1
    FIVE_MINUTE = "5m"       # V3 API: minutes/5
    FIFTEEN_MINUTE = "15m"   # V3 API: minutes/15
    ONE_DAY = "1d"          # V3 API: days/1

@dataclass
class FetchRequest:
    """Individual fetch request for rate limiting queue"""
    instrument_key: str
    symbol: str
    interval: IntervalType
    from_date: str
    to_date: str
    priority: int = 1  # Lower number = higher priority

@dataclass
class FetchResult:
    """Result of a fetch operation"""
    instrument_key: str
    symbol: str
    interval: IntervalType
    success: bool
    candles_count: int = 0
    error_message: Optional[str] = None

class RateLimitedFetcher:
    """Rate-limited historical data fetcher for Upstox API"""
    
    def __init__(self, requests_per_minute: int = 25, burst_limit: int = 5):
        """
        Initialize rate limiter
        Args:
            requests_per_minute: Maximum API calls per minute (Upstox limit ~25-30)
            burst_limit: Maximum concurrent requests
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.active_requests = 0
        self.last_request_times: List[float] = []
        self.is_processing = False
        
    async def add_fetch_request(self, request: FetchRequest):
        """Add a fetch request to the queue"""
        await self.request_queue.put(request)
        logger.info(f"Added fetch request: {request.symbol} {request.interval.value}")
        
    async def start_processing(self, token: str) -> List[FetchResult]:
        """Start processing the request queue with rate limiting"""
        if self.is_processing:
            logger.warning("Fetch processing already in progress")
            return []
            
        self.is_processing = True
        results = []
        
        try:
            logger.info(f"Starting rate-limited fetch processing (queue size: {self.request_queue.qsize()})")
            
            while not self.request_queue.empty():
                # Check if we need to wait for rate limiting
                await self._wait_for_rate_limit()
                
                # Get next request
                request = await self.request_queue.get()
                
                # Process the request
                result = await self._process_single_request(request, token)
                results.append(result)
                
                # Update rate limiting tracking
                self.last_request_times.append(time.time())
                
                # Log progress
                remaining = self.request_queue.qsize()
                status_icon = "✅" if result.success else "❌"
                logger.info(f"{status_icon} {result.symbol} {result.interval.value}: {result.candles_count} candles (remaining: {remaining})")
                
        except Exception as e:
            logger.error(f"Error during fetch processing: {e}")
        finally:
            self.is_processing = False
            
        return results
    
    async def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        now = time.time()
        
        # Remove old timestamps (older than 1 minute)
        cutoff = now - 60
        self.last_request_times = [t for t in self.last_request_times if t > cutoff]
        
        # Check if we need to wait
        if len(self.last_request_times) >= self.requests_per_minute:
            # Wait until the oldest request is more than 1 minute old
            oldest = min(self.last_request_times)
            wait_time = 60 - (now - oldest) + 1  # Add 1 second buffer
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
    
    async def _process_single_request(self, request: FetchRequest, token: str) -> FetchResult:
        """Process a single fetch request"""
        try:
            # Fetch historical data from Upstox
            response = await upstox_client.get_historical_candles(
                instrument_key=request.instrument_key,
                interval=request.interval.value,
                from_date=request.from_date,
                to_date=request.to_date,
                token=token
            )
            
            # Convert to CandleDataDTO format
            candles = []
            if response and response.get("data") and response["data"].get("candles"):
                raw_candles = response["data"]["candles"]
                
                # Convert interval to CandleInterval enum
                interval_map = {
                    IntervalType.ONE_MINUTE: CandleInterval.ONE_MINUTE,
                    IntervalType.FIVE_MINUTE: CandleInterval.FIVE_MINUTE,
                    IntervalType.FIFTEEN_MINUTE: CandleInterval.FIFTEEN_MINUTE,
                    IntervalType.ONE_DAY: CandleInterval.ONE_DAY
                }
                candle_interval = interval_map[request.interval]
                
                for candle in raw_candles:
                    if len(candle) >= 6:
                        candle_dto = CandleDataDTO(
                            instrument_key=request.instrument_key,
                            symbol=request.symbol,
                            interval=candle_interval,
                            timestamp=candle[0],
                            open_price=float(candle[1]),
                            high_price=float(candle[2]),
                            low_price=float(candle[3]),
                            close_price=float(candle[4]),
                            volume=int(candle[5]),
                            tick_count=0
                        )
                        candles.append(candle_dto)
            
            # Save to database
            saved_count = 0
            for candle in candles:
                await market_data_service.store_candle_data(candle)
                saved_count += 1
            
            return FetchResult(
                instrument_key=request.instrument_key,
                symbol=request.symbol,
                interval=request.interval,
                success=True,
                candles_count=saved_count
            )
            
        except Exception as e:
            logger.error(f"Error fetching {request.symbol} {request.interval.value}: {e}")
            return FetchResult(
                instrument_key=request.instrument_key,
                symbol=request.symbol,
                interval=request.interval,
                success=False,
                error_message=str(e)
            )

class HistoricalDataManager:
    """Main manager for historical data operations"""
    
    def __init__(self):
        self.fetcher = RateLimitedFetcher()
        
    async def fetch_all_timeframes(self, token: str, days_back: int = 30) -> Dict[str, List[FetchResult]]:
        """
        Fetch all timeframes for all selected instruments
        
        Args:
            token: Upstox access token
            days_back: Number of days to fetch
            
        Returns:
            Dictionary with results grouped by interval
        """
        logger.info("Starting comprehensive historical data fetch")
        
        # Get selected instruments
        selected = await instrument_service.get_selected_instruments()
        if not selected:
            logger.warning("No instruments selected")
            return {}
        
        # Calculate date range (use yesterday as end date to avoid future date errors)
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days_back)
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        logger.info(f"Fetching data for {len(selected)} instruments from {from_date} to {to_date}")
        
        # Define fetch priorities (1d first, then intraday from largest to smallest interval)
        intervals_with_priority = [
            (IntervalType.ONE_DAY, 1),        # Most efficient, least API calls
            (IntervalType.FIFTEEN_MINUTE, 2), # Larger intraday interval 
            (IntervalType.FIVE_MINUTE, 3),    # Medium intraday interval
            (IntervalType.ONE_MINUTE, 4)      # Highest resolution, most API intensive
        ]
        
        # Queue all requests
        total_requests = 0
        for instrument in selected:
            for interval, priority in intervals_with_priority:
                request = FetchRequest(
                    instrument_key=instrument.instrument_key,
                    symbol=instrument.symbol,
                    interval=interval,
                    from_date=from_date,
                    to_date=to_date,
                    priority=priority
                )
                await self.fetcher.add_fetch_request(request)
                total_requests += 1
        
        logger.info(f"Queued {total_requests} fetch requests")
        
        # Process all requests
        results = await self.fetcher.start_processing(token)
        
        # Group results by interval
        grouped_results = {}
        for result in results:
            interval_name = result.interval.value
            if interval_name not in grouped_results:
                grouped_results[interval_name] = []
            grouped_results[interval_name].append(result)
        
        # Log summary
        logger.info("=== FETCH SUMMARY ===")
        for interval_name, interval_results in grouped_results.items():
            successful = len([r for r in interval_results if r.success])
            total = len(interval_results)
            total_candles = sum(r.candles_count for r in interval_results if r.success)
            logger.info(f"{interval_name}: {successful}/{total} instruments, {total_candles} candles")
        
        return grouped_results
    
    async def fetch_single_interval(self, token: str, interval: IntervalType, days_back: int = 30) -> List[FetchResult]:
        """
        Fetch single interval for all selected instruments
        
        Args:
            token: Upstox access token
            interval: Specific interval to fetch
            days_back: Number of days to fetch
            
        Returns:
            List of fetch results
        """
        logger.info(f"Fetching {interval.value} data for all selected instruments")
        
        # Get selected instruments
        selected = await instrument_service.get_selected_instruments()
        if not selected:
            logger.warning("No instruments selected")
            return []
        
        # Calculate date range (use yesterday as end date to avoid future date errors)
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days_back)
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        # Queue requests for this interval only
        for instrument in selected:
            request = FetchRequest(
                instrument_key=instrument.instrument_key,
                symbol=instrument.symbol,
                interval=interval,
                from_date=from_date,
                to_date=to_date,
                priority=1
            )
            await self.fetcher.add_fetch_request(request)
        
        # Process requests
        results = await self.fetcher.start_processing(token)
        
        # Log summary
        successful = len([r for r in results if r.success])
        total_candles = sum(r.candles_count for r in results if r.success)
        logger.info(f"Completed {interval.value}: {successful}/{len(results)} instruments, {total_candles} candles")
        
        return results

# Create singleton instance
historical_data_manager = HistoricalDataManager()

# Test script functionality
async def test_historical_fetch():
    """Test the historical data fetching system"""
    
    # Token from test files (replace with actual token)
    token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"
    
    print("🚀 Testing Historical Data Manager")
    print("=" * 50)
    
    # Test single interval fetch
    print("\n📊 Testing 1-day candles fetch...")
    results = await historical_data_manager.fetch_single_interval(token, IntervalType.ONE_DAY, days_back=7)
    
    for result in results:
        status = "✅" if result.success else "❌"
        print(f"{status} {result.symbol}: {result.candles_count} candles")
    
    # Could test all timeframes (commented out to avoid rate limiting)
    # print("\n📈 Testing all timeframes fetch...")
    # all_results = await historical_data_manager.fetch_all_timeframes(token, days_back=7)

if __name__ == "__main__":
    asyncio.run(test_historical_fetch())