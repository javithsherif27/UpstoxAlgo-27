import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from ..models.market_data_dto import (
    MarketTickDTO, CandleDataDTO, CandleInterval, SubscriptionRequest
)
from ..services.market_data_storage import market_data_storage
from ..services.websocket_client import upstox_ws_client
from ..services.instrument_service import instrument_service
from ..utils.logging import get_logger
from ..services.backfill_client import fetch_intraday, fetch_historical

logger = get_logger(__name__)

class CandleManager:
    """Manages candle formation from ticks"""
    
    def __init__(self):
        # Store current candles being formed
        # Format: {instrument_key: {interval: CandleDataDTO}}
        self.active_candles: Dict[str, Dict[CandleInterval, CandleDataDTO]] = defaultdict(dict)
        self.candle_intervals = [
            CandleInterval.ONE_MINUTE,
            CandleInterval.FIVE_MINUTE, 
            CandleInterval.FIFTEEN_MINUTE
        ]
    
    def _get_candle_start_time(self, timestamp: datetime, interval: CandleInterval) -> datetime:
        """Get the start time of the candle for a given timestamp and interval"""
        # Normalize to minute boundary
        normalized = timestamp.replace(second=0, microsecond=0)
        
        if interval == CandleInterval.ONE_MINUTE:
            return normalized
        elif interval == CandleInterval.FIVE_MINUTE:
            # Round down to nearest 5-minute boundary
            minute = (normalized.minute // 5) * 5
            return normalized.replace(minute=minute)
        elif interval == CandleInterval.FIFTEEN_MINUTE:
            # Round down to nearest 15-minute boundary  
            minute = (normalized.minute // 15) * 15
            return normalized.replace(minute=minute)
        
        return normalized
    
    def _should_close_candle(self, candle: CandleDataDTO, current_time: datetime) -> bool:
        """Check if a candle should be closed based on current time"""
        if candle.interval == CandleInterval.ONE_MINUTE:
            return current_time >= candle.timestamp + timedelta(minutes=1)
        elif candle.interval == CandleInterval.FIVE_MINUTE:
            return current_time >= candle.timestamp + timedelta(minutes=5)
        elif candle.interval == CandleInterval.FIFTEEN_MINUTE:
            return current_time >= candle.timestamp + timedelta(minutes=15)
        
        return False
    
    async def process_tick(self, tick: MarketTickDTO):
        """Process a tick and update/create candles"""
        try:
            instrument_key = tick.instrument_key
            
            for interval in self.candle_intervals:
                candle_start_time = self._get_candle_start_time(tick.timestamp, interval)
                
                # Get or create current candle
                if interval not in self.active_candles[instrument_key]:
                    # Create new candle
                    candle = CandleDataDTO(
                        instrument_key=instrument_key,
                        symbol=tick.symbol,
                        interval=interval,
                        timestamp=candle_start_time,
                        open_price=tick.ltp,
                        high_price=tick.ltp,
                        low_price=tick.ltp,
                        close_price=tick.ltp,
                        volume=tick.ltq or 0,
                        tick_count=1
                    )
                    self.active_candles[instrument_key][interval] = candle
                    logger.debug(f"Created new {interval.value} candle for {tick.symbol}")
                    
                else:
                    candle = self.active_candles[instrument_key][interval]
                    
                    # Check if we need to close the current candle and start a new one
                    if self._should_close_candle(candle, tick.timestamp):
                        # Store the completed candle
                        await market_data_storage.store_candle(candle)
                        logger.info(f"Closed {interval.value} candle for {tick.symbol}: O={candle.open_price} H={candle.high_price} L={candle.low_price} C={candle.close_price} V={candle.volume}")
                        
                        # Start new candle
                        new_candle_start = self._get_candle_start_time(tick.timestamp, interval)
                        candle = CandleDataDTO(
                            instrument_key=instrument_key,
                            symbol=tick.symbol,
                            interval=interval,
                            timestamp=new_candle_start,
                            open_price=tick.ltp,
                            high_price=tick.ltp,
                            low_price=tick.ltp,
                            close_price=tick.ltp,
                            volume=tick.ltq or 0,
                            tick_count=1
                        )
                        self.active_candles[instrument_key][interval] = candle
                        logger.debug(f"Started new {interval.value} candle for {tick.symbol}")
                        
                    else:
                        # Update existing candle with new tick
                        candle.high_price = max(candle.high_price, tick.ltp)
                        candle.low_price = min(candle.low_price, tick.ltp)
                        candle.close_price = tick.ltp
                        candle.volume += tick.ltq or 0
                        candle.tick_count += 1
                        
                        # Periodically save active candles (every 10 ticks)
                        if candle.tick_count % 10 == 0:
                            await market_data_storage.store_candle(candle)
                            
        except Exception as e:
            logger.error(f"Error processing tick for candles: {e}")

class MarketDataService:
    """Main service for managing market data collection and processing"""
    
    def __init__(self):
        self.candle_manager = CandleManager()
        self.is_collecting = False
        self.total_ticks_received = 0
        self.errors: List[str] = []
        self.connection_status = "disconnected"
        
        # Set up tick processing callback
        upstox_ws_client.set_tick_callback(self.process_tick)
        
        # Set up connection status callbacks
        upstox_ws_client.set_connection_callbacks(
            on_connected=self._on_ws_connected,
            on_disconnected=self._on_ws_disconnected
        )
        
    async def _on_ws_connected(self):
        """Called when WebSocket connects successfully"""
        logger.info("WebSocket connected successfully")
        self.connection_status = "connected"
        
    async def _on_ws_disconnected(self):
        """Called when WebSocket disconnects"""
        logger.warning("WebSocket disconnected")
        self.connection_status = "disconnected"
    
    async def process_tick(self, tick: MarketTickDTO):
        """Process incoming tick data"""
        try:
            # Increment tick counter
            self.total_ticks_received += 1
            
            # Store raw tick
            await market_data_storage.store_tick(tick)
            
            # Update candles
            await self.candle_manager.process_tick(tick)
            
            logger.debug(f"Processed tick for {tick.symbol}: LTP={tick.ltp}")
            
        except Exception as e:
            error_msg = f"Error processing tick: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            # Keep only last 50 errors
            if len(self.errors) > 50:
                self.errors = self.errors[-50:]
    
    async def start_data_collection(self, access_token: str) -> bool:
        """Start WebSocket connection and data collection"""
        try:
            if self.is_collecting:
                logger.warning("Data collection already started")
                return True
            
            # Get selected instruments
            selected_instruments = await instrument_service.get_selected_instruments()
            
            if not selected_instruments:
                raise Exception("No instruments selected for data collection")
            
            # Bootstrap recent history (last 1 day) into SQLite so UI has LTP off-market
            logger.info(f"Backfilling recent history for {len(selected_instruments)} instruments...")
            await self._backfill_recent_history(selected_instruments, access_token)

            # Connect WebSocket (after backfill to avoid immediate write contention)
            logger.info("Connecting to Upstox WebSocket...")
            await upstox_ws_client.connect(access_token)
            
            # Wait for connection to establish
            await asyncio.sleep(2)
            
            # Subscribe to selected instruments
            instrument_keys = [inst.instrument_key for inst in selected_instruments]
            
            if upstox_ws_client.is_connected:
                logger.info(f"Subscribing to {len(instrument_keys)} instruments...")
                subscription_request = SubscriptionRequest(
                    instrument_keys=instrument_keys,
                    mode="ltpc"  # Start with LTPC mode for basic price data
                )
                
                await upstox_ws_client.subscribe(subscription_request)
                self.is_collecting = True
                logger.info(f"✅ Started data collection for {len(instrument_keys)} instruments")
                return True
            else:
                raise Exception("WebSocket connection failed - unable to subscribe to instruments")
            
        except Exception as e:
            logger.error(f"Error starting data collection: {e}")
            return False
    
    async def stop_data_collection(self) -> bool:
        """Stop data collection and WebSocket connection"""
        try:
            # Close any active candles
            await self._close_all_active_candles()
            
            # Disconnect WebSocket
            await upstox_ws_client.disconnect()
            
            self.is_collecting = False
            logger.info("Stopped data collection")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping data collection: {e}")
            return False
    
    async def _close_all_active_candles(self):
        """Close and save all active candles"""
        try:
            for instrument_key, candles in self.candle_manager.active_candles.items():
                for interval, candle in candles.items():
                    await market_data_storage.store_candle(candle)
                    logger.info(f"Saved final candle for {candle.symbol} ({interval.value})")
            
            # Clear active candles
            self.candle_manager.active_candles.clear()
            
        except Exception as e:
            logger.error(f"Error closing active candles: {e}")

    async def _backfill_recent_history(self, selected_instruments, access_token: str):
        """Backfill last 1 day of 1m/5m/15m candles for selected instruments into SQLite."""
        try:
            now = datetime.now(timezone.utc)
            since = now - timedelta(days=1)
            intervals = [
                CandleInterval.ONE_MINUTE,
                CandleInterval.FIVE_MINUTE,
                CandleInterval.FIFTEEN_MINUTE,
            ]

            async def backfill_one(inst, interval: CandleInterval):
                symbol = inst.symbol
                try:
                    # Prefer intraday for recent ranges
                    candles = await fetch_intraday(symbol, interval.value, since, now, access_token)
                except Exception as e:
                    logger.warning(f"Intraday backfill failed for {symbol} {interval.value}: {e}; trying historical")
                    candles = []
                    try:
                        candles = await fetch_historical(symbol, interval.value, since, now, access_token)
                    except Exception as e2:
                        logger.error(f"Historical backfill failed for {symbol} {interval.value}: {e2}")
                        return

                # Store into SQLite as CandleDataDTO
                for c in candles:
                    dto = CandleDataDTO(
                        instrument_key=inst.instrument_key,
                        symbol=inst.symbol,
                        interval=interval,
                        timestamp=c.start,
                        open_price=c.o,
                        high_price=c.h,
                        low_price=c.l,
                        close_price=c.c,
                        volume=c.v,
                        tick_count=0,
                    )
                    await market_data_storage.store_candle(dto)

            tasks: List = []
            for inst in selected_instruments:
                for itv in intervals:
                    tasks.append(backfill_one(inst, itv))
            # Run with limited concurrency to avoid overloading
            # Chunk tasks in small batches
            batch_size = 10
            for i in range(0, len(tasks), batch_size):
                await asyncio.gather(*tasks[i:i+batch_size])

            logger.info("Backfill complete for selected instruments (last 1 day)")
        except Exception as e:
            logger.error(f"Backfill error: {e}")
    
    async def add_instruments_to_collection(self, instrument_keys: List[str]):
        """Add instruments to active data collection"""
        try:
            if not self.is_collecting:
                raise Exception("Data collection not started")
            
            subscription_request = SubscriptionRequest(
                instrument_keys=instrument_keys,
                mode="ltpc"
            )
            
            await upstox_ws_client.subscribe(subscription_request)
            logger.info(f"Added {len(instrument_keys)} instruments to data collection")
            
        except Exception as e:
            logger.error(f"Error adding instruments: {e}")
            raise
    
    async def remove_instruments_from_collection(self, instrument_keys: List[str]):
        """Remove instruments from active data collection"""
        try:
            if not self.is_collecting:
                return
            
            await upstox_ws_client.unsubscribe(instrument_keys)
            
            # Close active candles for removed instruments
            for instrument_key in instrument_keys:
                if instrument_key in self.candle_manager.active_candles:
                    candles = self.candle_manager.active_candles[instrument_key]
                    for candle in candles.values():
                        await market_data_storage.store_candle(candle)
                    del self.candle_manager.active_candles[instrument_key]
            
            logger.info(f"Removed {len(instrument_keys)} instruments from data collection")
            
        except Exception as e:
            logger.error(f"Error removing instruments: {e}")
            raise
    
    async def get_candles(self, instrument_key: str, interval: CandleInterval,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 100) -> List[CandleDataDTO]:
        """Get historical candle data"""
        return await market_data_storage.get_candles(
            instrument_key, interval, start_time, end_time, limit
        )
    
    def get_websocket_status(self):
        """Get WebSocket connection status"""
        return upstox_ws_client.get_status()
    
    def is_data_collection_active(self) -> bool:
        """Check if data collection is currently active"""
        return self.is_collecting and upstox_ws_client.is_connected
    
    async def get_latest_ticks(self, instrument_keys: List[str] = None) -> dict:
        """Get latest tick data for specified instruments or all instruments"""
        return await market_data_storage.get_latest_ticks(instrument_keys)
    
    async def store_candle_data(self, candle: CandleDataDTO):
        """Store a single candle data record"""
        return await market_data_storage.store_candle(candle)
    
    def get_status(self) -> Dict:
        """Get current status of market data collection"""
        try:
            # Safely get WebSocket client status
            ws_connected = getattr(upstox_ws_client, 'is_connected', False)
            subscribed_count = len(getattr(upstox_ws_client, 'subscribed_instruments', {}))
            
            # Safely get connection time
            connection_time = None
            if hasattr(upstox_ws_client, 'connection_time') and upstox_ws_client.connection_time:
                try:
                    connection_time = upstox_ws_client.connection_time.isoformat()
                except:
                    connection_time = str(upstox_ws_client.connection_time)
            
            # Safely get heartbeat time
            heartbeat_time = None
            if hasattr(upstox_ws_client, 'last_heartbeat') and upstox_ws_client.last_heartbeat:
                try:
                    heartbeat_time = upstox_ws_client.last_heartbeat.isoformat()
                except:
                    heartbeat_time = str(upstox_ws_client.last_heartbeat)
            
            return {
                "is_collecting": self.is_collecting,
                "is_connected": ws_connected,  # Frontend expects this field
                "total_ticks_received": self.total_ticks_received,
                "subscribed_instruments_count": subscribed_count,
                "connection_status": self.connection_status,
                "last_heartbeat": heartbeat_time,
                "errors": self.errors[-10:] if self.errors else [],  # Last 10 errors
                "active_candles": sum(len(candles) for candles in self.candle_manager.active_candles.values()),
                "message": "Ready to start data collection" if not self.is_collecting else "Data collection active"
            }
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            return {
                "is_collecting": False,
                "is_connected": False,
                "total_ticks_received": 0,
                "subscribed_instruments_count": 0,
                "connection_status": "ready",
                "last_heartbeat": None,
                "errors": [],
                "active_candles": 0,
                "message": "Service ready - login to start data collection"
            }

# Global service instance
market_data_service = MarketDataService()