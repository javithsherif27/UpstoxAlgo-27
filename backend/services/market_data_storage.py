import sqlite3
import json
import os
from typing import List, Optional
from datetime import datetime, timedelta
from ..models.market_data_dto import MarketTickDTO, CandleDataDTO, CandleInterval
from ..utils.logging import get_logger

logger = get_logger(__name__)

class MarketDataStorage:
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create ticks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_ticks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument_key TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    ltp REAL NOT NULL,
                    ltt INTEGER NOT NULL,
                    ltq INTEGER NOT NULL,
                    cp REAL NOT NULL,
                    volume INTEGER,
                    oi INTEGER,
                    timestamp TEXT NOT NULL,
                    raw_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create candles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument_key TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume INTEGER NOT NULL DEFAULT 0,
                    open_interest INTEGER,
                    tick_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticks_instrument_time 
                ON market_ticks(instrument_key, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_candles_instrument_interval_time 
                ON candles(instrument_key, interval, timestamp)
            """)
            
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_candles_unique 
                ON candles(instrument_key, interval, timestamp)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    async def store_tick(self, tick: MarketTickDTO) -> bool:
        """Store a market tick in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO market_ticks 
                    (instrument_key, symbol, ltp, ltt, ltq, cp, volume, oi, timestamp, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tick.instrument_key,
                    tick.symbol,
                    tick.ltp,
                    tick.ltt,
                    tick.ltq,
                    tick.cp,
                    tick.volume,
                    tick.oi,
                    tick.timestamp.isoformat(),
                    json.dumps(tick.raw_data) if tick.raw_data else None
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing tick: {e}")
            return False
    
    async def store_candle(self, candle: CandleDataDTO) -> bool:
        """Store or update a candle in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO candles 
                    (instrument_key, symbol, interval, timestamp, open_price, high_price, 
                     low_price, close_price, volume, open_interest, tick_count, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    candle.instrument_key,
                    candle.symbol,
                    candle.interval.value,
                    candle.timestamp.isoformat(),
                    candle.open_price,
                    candle.high_price,
                    candle.low_price,
                    candle.close_price,
                    candle.volume,
                    candle.open_interest,
                    candle.tick_count,
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing candle: {e}")
            return False
    
    async def get_candles(self, instrument_key: str, interval: CandleInterval, 
                         start_time: Optional[datetime] = None, 
                         end_time: Optional[datetime] = None,
                         limit: int = 100) -> List[CandleDataDTO]:
        """Retrieve candles for an instrument and interval"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT instrument_key, symbol, interval, timestamp, open_price, 
                           high_price, low_price, close_price, volume, open_interest, tick_count
                    FROM candles 
                    WHERE instrument_key = ? AND interval = ?
                """
                params = [instrument_key, interval.value]
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                candles = []
                for row in rows:
                    candles.append(CandleDataDTO(
                        instrument_key=row[0],
                        symbol=row[1],
                        interval=CandleInterval(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        open_price=row[4],
                        high_price=row[5],
                        low_price=row[6],
                        close_price=row[7],
                        volume=row[8],
                        open_interest=row[9],
                        tick_count=row[10]
                    ))
                
                return candles
                
        except Exception as e:
            logger.error(f"Error retrieving candles: {e}")
            return []
    
    async def get_latest_candle(self, instrument_key: str, interval: CandleInterval) -> Optional[CandleDataDTO]:
        """Get the latest candle for an instrument and interval"""
        candles = await self.get_candles(instrument_key, interval, limit=1)
        return candles[0] if candles else None
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old tick data to manage database size"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up old ticks
                cursor.execute("""
                    DELETE FROM market_ticks 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_ticks = cursor.rowcount
                
                # Clean up old candles (keep longer)
                old_candle_cutoff = datetime.now() - timedelta(days=days_to_keep * 3)
                cursor.execute("""
                    DELETE FROM candles 
                    WHERE timestamp < ?
                """, (old_candle_cutoff.isoformat(),))
                
                deleted_candles = cursor.rowcount
                
                conn.commit()
                logger.info(f"Cleaned up {deleted_ticks} old ticks and {deleted_candles} old candles")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global instance
market_data_storage = MarketDataStorage()