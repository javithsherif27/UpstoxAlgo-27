"""
PostgreSQL-based Market Data Storage Service
Optimized for high-frequency trading data with async operations
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from ..lib.database import db_manager, get_connection
from ..models.market_data_dto import MarketTickDTO, CandleDataDTO, CandleInterval
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PostgreSQLMarketDataStorage:
    """PostgreSQL-based market data storage with optimized performance"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    async def ensure_initialized(self):
        """Ensure database is initialized"""
        if not self.db_manager._initialized:
            await self.db_manager.initialize()
    
    async def store_tick(self, tick: MarketTickDTO) -> bool:
        """Store a market tick in PostgreSQL with high performance"""
        try:
            await self.ensure_initialized()
            
            query = """
            INSERT INTO market_ticks 
            (instrument_key, symbol, ltp, ltt, ltq, cp, volume, oi, 
             bid_price, ask_price, bid_qty, ask_qty, timestamp, raw_data)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """
            
            async with self.db_manager.get_connection() as conn:
                await conn.execute(
                    query,
                    tick.instrument_key,
                    tick.symbol,
                    tick.ltp,
                    tick.ltt,
                    tick.ltq,
                    tick.cp,
                    tick.volume or 0,
                    tick.oi or 0,
                    getattr(tick, 'bid_price', None),
                    getattr(tick, 'ask_price', None),
                    getattr(tick, 'bid_qty', None),
                    getattr(tick, 'ask_qty', None),
                    tick.timestamp,
                    json.dumps(tick.raw_data) if tick.raw_data else None
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing tick for {tick.instrument_key}: {e}")
            return False
    
    async def store_ticks_batch(self, ticks: List[MarketTickDTO]) -> int:
        """Store multiple ticks in a single batch operation for better performance"""
        if not ticks:
            return 0
            
        try:
            await self.ensure_initialized()
            
            query = """
            INSERT INTO market_ticks 
            (instrument_key, symbol, ltp, ltt, ltq, cp, volume, oi, 
             bid_price, ask_price, bid_qty, ask_qty, timestamp, raw_data)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """
            
            batch_data = []
            for tick in ticks:
                batch_data.append((
                    tick.instrument_key,
                    tick.symbol,
                    tick.ltp,
                    tick.ltt,
                    tick.ltq,
                    tick.cp,
                    tick.volume or 0,
                    tick.oi or 0,
                    getattr(tick, 'bid_price', None),
                    getattr(tick, 'ask_price', None),
                    getattr(tick, 'bid_qty', None),
                    getattr(tick, 'ask_qty', None),
                    tick.timestamp,
                    json.dumps(tick.raw_data) if tick.raw_data else None
                ))
            
            async with self.db_manager.get_connection() as conn:
                await conn.executemany(query, batch_data)
            
            logger.debug(f"Stored {len(ticks)} ticks in batch")
            return len(ticks)
            
        except Exception as e:
            logger.error(f"Error storing tick batch: {e}")
            return 0
    
    async def store_candle(self, candle: CandleDataDTO) -> bool:
        """Store or update a candle with UPSERT for better performance"""
        try:
            await self.ensure_initialized()
            
            query = """
            INSERT INTO candles 
            (instrument_key, symbol, interval, timestamp, open_price, high_price, 
             low_price, close_price, volume, open_interest, tick_count, vwap, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, CURRENT_TIMESTAMP)
            ON CONFLICT (instrument_key, interval, timestamp) 
            DO UPDATE SET
                high_price = GREATEST(candles.high_price, EXCLUDED.high_price),
                low_price = LEAST(candles.low_price, EXCLUDED.low_price),
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                open_interest = EXCLUDED.open_interest,
                tick_count = EXCLUDED.tick_count,
                vwap = EXCLUDED.vwap,
                updated_at = CURRENT_TIMESTAMP
            """
            
            async with self.db_manager.get_connection() as conn:
                await conn.execute(
                    query,
                    candle.instrument_key,
                    candle.symbol,
                    candle.interval.value,
                    candle.timestamp,
                    candle.open_price,
                    candle.high_price,
                    candle.low_price,
                    candle.close_price,
                    candle.volume,
                    candle.open_interest,
                    candle.tick_count,
                    getattr(candle, 'vwap', None)
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing candle for {candle.instrument_key}: {e}")
            return False
    
    async def store_candles_batch(self, candles: List[CandleDataDTO]) -> int:
        """Store multiple candles in batch with conflict resolution"""
        if not candles:
            return 0
            
        try:
            await self.ensure_initialized()
            
            # Group candles by unique key to handle conflicts
            candle_dict = {}
            for candle in candles:
                key = (candle.instrument_key, candle.interval.value, candle.timestamp)
                candle_dict[key] = candle  # Latest candle wins
            
            query = """
            INSERT INTO candles 
            (instrument_key, symbol, interval, timestamp, open_price, high_price, 
             low_price, close_price, volume, open_interest, tick_count, vwap, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, CURRENT_TIMESTAMP)
            ON CONFLICT (instrument_key, interval, timestamp) 
            DO UPDATE SET
                high_price = GREATEST(candles.high_price, EXCLUDED.high_price),
                low_price = LEAST(candles.low_price, EXCLUDED.low_price),
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                open_interest = EXCLUDED.open_interest,
                tick_count = EXCLUDED.tick_count,
                vwap = EXCLUDED.vwap,
                updated_at = CURRENT_TIMESTAMP
            """
            
            batch_data = []
            for candle in candle_dict.values():
                batch_data.append((
                    candle.instrument_key,
                    candle.symbol,
                    candle.interval.value,
                    candle.timestamp,
                    candle.open_price,
                    candle.high_price,
                    candle.low_price,
                    candle.close_price,
                    candle.volume,
                    candle.open_interest,
                    candle.tick_count,
                    getattr(candle, 'vwap', None)
                ))
            
            async with self.db_manager.get_connection() as conn:
                await conn.executemany(query, batch_data)
            
            logger.debug(f"Stored {len(batch_data)} candles in batch")
            return len(batch_data)
            
        except Exception as e:
            logger.error(f"Error storing candle batch: {e}")
            return 0
    
    async def get_candles(self, instrument_key: str, interval: CandleInterval, 
                         start_time: Optional[datetime] = None, 
                         end_time: Optional[datetime] = None,
                         limit: int = 100) -> List[CandleDataDTO]:
        """Retrieve candles with optimized query performance"""
        try:
            await self.ensure_initialized()
            
            query = """
            SELECT instrument_key, symbol, interval, timestamp, open_price, 
                   high_price, low_price, close_price, volume, open_interest, 
                   tick_count, vwap
            FROM candles 
            WHERE instrument_key = $1 AND interval = $2
            """
            params = [instrument_key, interval.value]
            param_count = 3
            
            if start_time:
                query += f" AND timestamp >= ${param_count}"
                params.append(start_time)
                param_count += 1
            
            if end_time:
                query += f" AND timestamp <= ${param_count}"
                params.append(end_time)
                param_count += 1
            
            query += f" ORDER BY timestamp DESC LIMIT ${param_count}"
            params.append(limit)
            
            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch(query, *params)
            
            candles = []
            for row in rows:
                candles.append(CandleDataDTO(
                    instrument_key=row['instrument_key'],
                    symbol=row['symbol'],
                    interval=CandleInterval(row['interval']),
                    timestamp=row['timestamp'],
                    open_price=float(row['open_price']),
                    high_price=float(row['high_price']),
                    low_price=float(row['low_price']),
                    close_price=float(row['close_price']),
                    volume=row['volume'],
                    open_interest=row['open_interest'],
                    tick_count=row['tick_count']
                ))
            
            # Reverse to get chronological order
            return candles[::-1]
            
        except Exception as e:
            logger.error(f"Error retrieving candles for {instrument_key}: {e}")
            return []
    
    async def get_latest_candle(self, instrument_key: str, interval: CandleInterval) -> Optional[CandleDataDTO]:
        """Get the latest candle for an instrument and interval"""
        candles = await self.get_candles(instrument_key, interval, limit=1)
        return candles[0] if candles else None
    
    async def get_latest_ticks(self, instrument_keys: List[str] = None, limit: int = 1000) -> Dict[str, Dict[str, Any]]:
        """Get latest tick data using optimized query with window functions"""
        try:
            await self.ensure_initialized()
            
            if instrument_keys:
                # Get latest tick for specified instruments
                query = """
                SELECT DISTINCT ON (instrument_key)
                    instrument_key, symbol, ltp, ltt, ltq, cp, volume, oi,
                    bid_price, ask_price, bid_qty, ask_qty, timestamp
                FROM market_ticks 
                WHERE instrument_key = ANY($1)
                ORDER BY instrument_key, timestamp DESC
                """
                params = [instrument_keys]
            else:
                # Get latest tick for all instruments (with limit)
                query = """
                SELECT DISTINCT ON (instrument_key)
                    instrument_key, symbol, ltp, ltt, ltq, cp, volume, oi,
                    bid_price, ask_price, bid_qty, ask_qty, timestamp
                FROM market_ticks 
                ORDER BY instrument_key, timestamp DESC
                LIMIT $1
                """
                params = [limit]
            
            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch(query, *params)
            
            result = {}
            for row in rows:
                result[row['instrument_key']] = {
                    'symbol': row['symbol'],
                    'ltp': float(row['ltp']) if row['ltp'] else None,
                    'ltt': row['ltt'],
                    'ltq': row['ltq'],
                    'cp': float(row['cp']) if row['cp'] else None,
                    'volume': row['volume'],
                    'oi': row['oi'],
                    'bid_price': float(row['bid_price']) if row['bid_price'] else None,
                    'ask_price': float(row['ask_price']) if row['ask_price'] else None,
                    'bid_qty': row['bid_qty'],
                    'ask_qty': row['ask_qty'],
                    'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving latest ticks: {e}")
            return {}
    
    async def get_tick_statistics(self, instrument_key: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get tick statistics for performance analysis"""
        try:
            await self.ensure_initialized()
            
            query = """
            SELECT 
                COUNT(*) as tick_count,
                MIN(ltp) as min_price,
                MAX(ltp) as max_price,
                AVG(ltp) as avg_price,
                SUM(volume) as total_volume,
                MIN(timestamp) as first_tick,
                MAX(timestamp) as last_tick
            FROM market_ticks 
            WHERE instrument_key = $1 
            AND timestamp BETWEEN $2 AND $3
            """
            
            async with self.db_manager.get_connection() as conn:
                row = await conn.fetchrow(query, instrument_key, start_time, end_time)
            
            if row:
                return {
                    'tick_count': row['tick_count'],
                    'min_price': float(row['min_price']) if row['min_price'] else None,
                    'max_price': float(row['max_price']) if row['max_price'] else None,
                    'avg_price': float(row['avg_price']) if row['avg_price'] else None,
                    'total_volume': row['total_volume'],
                    'first_tick': row['first_tick'].isoformat() if row['first_tick'] else None,
                    'last_tick': row['last_tick'].isoformat() if row['last_tick'] else None
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting tick statistics: {e}")
            return {}
    
    async def cleanup_old_ticks(self, days_to_keep: int = 7) -> int:
        """Clean up old tick data to manage database size"""
        try:
            await self.ensure_initialized()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            query = "DELETE FROM market_ticks WHERE timestamp < $1"
            
            async with self.db_manager.get_connection() as conn:
                result = await conn.execute(query, cutoff_date)
            
            # Parse deleted count from result string
            deleted_count = int(result.split()[-1])
            logger.info(f"Cleaned up {deleted_count} old tick records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old ticks: {e}")
            return 0


# Global instance
market_data_storage = PostgreSQLMarketDataStorage()