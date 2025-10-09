#!/usr/bin/env python3
"""
Migration script from SQLite to PostgreSQL
Run this to migrate existing data from SQLite to PostgreSQL
"""
import asyncio
import sqlite3
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.lib.database import init_database, db_manager
from backend.models.market_data_dto import CandleInterval
from backend.utils.logging import get_logger

logger = get_logger(__name__)


async def migrate_instruments(sqlite_db_path: str) -> int:
    """Migrate instruments from SQLite to PostgreSQL"""
    try:
        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if instruments table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instruments'")
        if not cursor.fetchone():
            logger.info("No instruments table found in SQLite")
            return 0
        
        # Fetch instruments from SQLite
        cursor.execute("SELECT * FROM instruments")
        instruments = cursor.fetchall()
        
        if not instruments:
            logger.info("No instruments data found")
            return 0
        
        # Insert into PostgreSQL
        query = """
        INSERT INTO instruments 
        (instrument_key, symbol, name, exchange, instrument_type, segment, 
         expiry_date, strike_price, option_type, lot_size, tick_size, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        ON CONFLICT (instrument_key) DO UPDATE SET
            symbol = EXCLUDED.symbol,
            name = EXCLUDED.name,
            exchange = EXCLUDED.exchange,
            updated_at = CURRENT_TIMESTAMP
        """
        
        migrated = 0
        async with db_manager.get_connection() as pg_conn:
            for instrument in instruments:
                try:
                    await pg_conn.execute(
                        query,
                        instrument.get('instrument_key'),
                        instrument.get('symbol'),
                        instrument.get('name'),
                        instrument.get('exchange', 'NSE'),
                        instrument.get('instrument_type', 'EQ'),
                        instrument.get('segment', 'EQ'),
                        instrument.get('expiry_date'),
                        instrument.get('strike_price'),
                        instrument.get('option_type'),
                        instrument.get('lot_size', 1),
                        instrument.get('tick_size', 0.01),
                        instrument.get('is_active', True)
                    )
                    migrated += 1
                except Exception as e:
                    logger.error(f"Error migrating instrument {instrument.get('symbol')}: {e}")
        
        conn.close()
        logger.info(f"Migrated {migrated} instruments")
        return migrated
        
    except Exception as e:
        logger.error(f"Error migrating instruments: {e}")
        return 0


async def migrate_market_ticks(sqlite_db_path: str, batch_size: int = 1000) -> int:
    """Migrate market ticks from SQLite to PostgreSQL in batches"""
    try:
        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if market_ticks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_ticks'")
        if not cursor.fetchone():
            logger.info("No market_ticks table found in SQLite")
            return 0
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM market_ticks")
        total_ticks = cursor.fetchone()[0]
        
        if total_ticks == 0:
            logger.info("No tick data found")
            return 0
        
        logger.info(f"Migrating {total_ticks} tick records...")
        
        # PostgreSQL insert query
        query = """
        INSERT INTO market_ticks 
        (instrument_key, symbol, ltp, ltt, ltq, cp, volume, oi, timestamp, raw_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT DO NOTHING
        """
        
        migrated = 0
        offset = 0
        
        while offset < total_ticks:
            # Fetch batch from SQLite
            cursor.execute(
                "SELECT * FROM market_ticks ORDER BY id LIMIT ? OFFSET ?",
                (batch_size, offset)
            )
            batch = cursor.fetchall()
            
            if not batch:
                break
            
            # Prepare batch data for PostgreSQL
            batch_data = []
            for tick in batch:
                try:
                    timestamp = datetime.fromisoformat(tick['timestamp']) if isinstance(tick['timestamp'], str) else tick['timestamp']
                    batch_data.append((
                        tick['instrument_key'],
                        tick['symbol'],
                        tick['ltp'],
                        tick['ltt'],
                        tick['ltq'],
                        tick['cp'],
                        tick.get('volume', 0),
                        tick.get('oi', 0),
                        timestamp,
                        tick.get('raw_data')
                    ))
                except Exception as e:
                    logger.warning(f"Skipping invalid tick record: {e}")
                    continue
            
            # Insert batch into PostgreSQL
            if batch_data:
                async with db_manager.get_connection() as pg_conn:
                    await pg_conn.executemany(query, batch_data)
                
                migrated += len(batch_data)
                logger.info(f"Migrated {migrated}/{total_ticks} ticks ({offset + len(batch)}/{total_ticks} processed)")
            
            offset += batch_size
        
        conn.close()
        logger.info(f"Successfully migrated {migrated} tick records")
        return migrated
        
    except Exception as e:
        logger.error(f"Error migrating market ticks: {e}")
        return 0


async def migrate_candles(sqlite_db_path: str, batch_size: int = 1000) -> int:
    """Migrate candles from SQLite to PostgreSQL in batches"""
    try:
        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if candles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candles'")
        if not cursor.fetchone():
            logger.info("No candles table found in SQLite")
            return 0
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM candles")
        total_candles = cursor.fetchone()[0]
        
        if total_candles == 0:
            logger.info("No candle data found")
            return 0
        
        logger.info(f"Migrating {total_candles} candle records...")
        
        # PostgreSQL insert query
        query = """
        INSERT INTO candles 
        (instrument_key, symbol, interval, timestamp, open_price, high_price, 
         low_price, close_price, volume, open_interest, tick_count)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT (instrument_key, interval, timestamp) DO UPDATE SET
            high_price = GREATEST(candles.high_price, EXCLUDED.high_price),
            low_price = LEAST(candles.low_price, EXCLUDED.low_price),
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume,
            updated_at = CURRENT_TIMESTAMP
        """
        
        migrated = 0
        offset = 0
        
        while offset < total_candles:
            # Fetch batch from SQLite
            cursor.execute(
                "SELECT * FROM candles ORDER BY id LIMIT ? OFFSET ?",
                (batch_size, offset)
            )
            batch = cursor.fetchall()
            
            if not batch:
                break
            
            # Prepare batch data for PostgreSQL
            batch_data = []
            for candle in batch:
                try:
                    timestamp = datetime.fromisoformat(candle['timestamp']) if isinstance(candle['timestamp'], str) else candle['timestamp']
                    batch_data.append((
                        candle['instrument_key'],
                        candle['symbol'],
                        candle['interval'],
                        timestamp,
                        candle['open_price'],
                        candle['high_price'],
                        candle['low_price'],
                        candle['close_price'],
                        candle.get('volume', 0),
                        candle.get('open_interest', 0),
                        candle.get('tick_count', 0)
                    ))
                except Exception as e:
                    logger.warning(f"Skipping invalid candle record: {e}")
                    continue
            
            # Insert batch into PostgreSQL
            if batch_data:
                async with db_manager.get_connection() as pg_conn:
                    await pg_conn.executemany(query, batch_data)
                
                migrated += len(batch_data)
                logger.info(f"Migrated {migrated}/{total_candles} candles ({offset + len(batch)}/{total_candles} processed)")
            
            offset += batch_size
        
        conn.close()
        logger.info(f"Successfully migrated {migrated} candle records")
        return migrated
        
    except Exception as e:
        logger.error(f"Error migrating candles: {e}")
        return 0


async def main():
    """Main migration function"""
    sqlite_db_path = "market_data.db"
    
    if not os.path.exists(sqlite_db_path):
        logger.error(f"SQLite database not found: {sqlite_db_path}")
        return
    
    print("🚀 Starting migration from SQLite to PostgreSQL...")
    print("=" * 60)
    
    try:
        # Initialize PostgreSQL database
        print("📊 Initializing PostgreSQL database...")
        await init_database()
        
        # Migrate data
        print("\n📦 Migrating instruments...")
        instruments_migrated = await migrate_instruments(sqlite_db_path)
        
        print("\n📈 Migrating market ticks...")
        ticks_migrated = await migrate_market_ticks(sqlite_db_path)
        
        print("\n🕯️ Migrating candles...")
        candles_migrated = await migrate_candles(sqlite_db_path)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print(f"📊 Instruments migrated: {instruments_migrated}")
        print(f"📈 Ticks migrated: {ticks_migrated}")
        print(f"🕯️ Candles migrated: {candles_migrated}")
        print("\n💡 You can now update your services to use PostgreSQL")
        print("💡 Consider backing up the SQLite database before removing it")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"\n❌ Migration failed: {e}")
    finally:
        from backend.lib.database import close_database
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())