"""
PostgreSQL Database Configuration and Connection Management
"""
import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, AsyncIterator
import asyncpg
from asyncpg.pool import Pool
from dotenv import load_dotenv
from ..utils.logging import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)


class DatabaseConfig:
    """Database configuration from environment variables"""
    
    def __init__(self):
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = int(os.getenv('DB_PORT', '5432'))
        self.DB_NAME = os.getenv('DB_NAME', 'trading_db')
        self.DB_USER = os.getenv('DB_USER', 'trading_user')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'trading_password_2024')
        self.DB_POOL_MIN_SIZE = int(os.getenv('DB_POOL_MIN_SIZE', '5'))
        self.DB_POOL_MAX_SIZE = int(os.getenv('DB_POOL_MAX_SIZE', '20'))
        self.DB_TIMEOUT = float(os.getenv('DB_TIMEOUT', '30.0'))
        
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class DatabaseManager:
    """PostgreSQL database manager with connection pooling"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.pool: Optional[Pool] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize database connection pool"""
        if self._initialized:
            return
            
        try:
            logger.info(f"Connecting to PostgreSQL database...")
            self.pool = await asyncpg.create_pool(
                self.config.connection_string,
                min_size=self.config.DB_POOL_MIN_SIZE,
                max_size=self.config.DB_POOL_MAX_SIZE,
                command_timeout=self.config.DB_TIMEOUT,
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
                
            logger.info("Database connection pool initialized successfully")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._initialized = False
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[asyncpg.Connection]:
        """Get a database connection from the pool"""
        if not self._initialized:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            yield conn
    
    async def execute_query(self, query: str, *args) -> Any:
        """Execute a query and return results"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_scalar(self, query: str, *args) -> Any:
        """Execute a query and return single value"""
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_command(self, query: str, *args) -> str:
        """Execute a command (INSERT, UPDATE, DELETE) and return status"""
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)


# Global database manager instance
db_manager = DatabaseManager()


async def init_database_schema():
    """Initialize database schema with optimized tables and indexes"""
    
    schema_sql = """
    -- Enable necessary extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "btree_gin";
    
    -- Instruments table with proper constraints
    CREATE TABLE IF NOT EXISTS instruments (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        instrument_key VARCHAR(100) UNIQUE NOT NULL,
        symbol VARCHAR(50) NOT NULL,
        name VARCHAR(200),
        exchange VARCHAR(20) NOT NULL,
        instrument_type VARCHAR(50),
        segment VARCHAR(20),
        expiry_date DATE,
        strike_price DECIMAL(12,4),
        option_type VARCHAR(10),
        lot_size INTEGER DEFAULT 1,
        tick_size DECIMAL(8,4) DEFAULT 0.01,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Market ticks table optimized for high-frequency inserts
    CREATE TABLE IF NOT EXISTS market_ticks (
        id BIGSERIAL PRIMARY KEY,
        instrument_key VARCHAR(100) NOT NULL,
        symbol VARCHAR(50) NOT NULL,
        ltp DECIMAL(12,4) NOT NULL,
        ltt BIGINT NOT NULL,  -- Last trade time as epoch
        ltq INTEGER NOT NULL, -- Last trade quantity
        cp DECIMAL(12,4) NOT NULL, -- Close price
        volume BIGINT DEFAULT 0,
        oi BIGINT DEFAULT 0, -- Open interest
        bid_price DECIMAL(12,4),
        ask_price DECIMAL(12,4),
        bid_qty INTEGER,
        ask_qty INTEGER,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        raw_data JSONB, -- Store additional metadata
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign key constraint
        CONSTRAINT fk_ticks_instrument 
            FOREIGN KEY (instrument_key) REFERENCES instruments(instrument_key)
            ON DELETE CASCADE
    );
    
    -- Candles table for OHLCV data with proper partitioning support
    CREATE TABLE IF NOT EXISTS candles (
        id BIGSERIAL PRIMARY KEY,
        instrument_key VARCHAR(100) NOT NULL,
        symbol VARCHAR(50) NOT NULL,
        interval VARCHAR(10) NOT NULL, -- 1m, 5m, 15m, 1h, 1d, etc.
        timestamp TIMESTAMPTZ NOT NULL,
        open_price DECIMAL(12,4) NOT NULL,
        high_price DECIMAL(12,4) NOT NULL,
        low_price DECIMAL(12,4) NOT NULL,
        close_price DECIMAL(12,4) NOT NULL,
        volume BIGINT NOT NULL DEFAULT 0,
        open_interest BIGINT DEFAULT 0,
        tick_count INTEGER NOT NULL DEFAULT 0,
        vwap DECIMAL(12,4), -- Volume-weighted average price
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        
        -- Unique constraint to prevent duplicate candles
        CONSTRAINT uk_candles_instrument_interval_time 
            UNIQUE (instrument_key, interval, timestamp),
            
        -- Foreign key constraint
        CONSTRAINT fk_candles_instrument 
            FOREIGN KEY (instrument_key) REFERENCES instruments(instrument_key)
            ON DELETE CASCADE
    );
    
    -- Performance-optimized indexes for trading queries
    
    -- Instruments indexes
    CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);
    CREATE INDEX IF NOT EXISTS idx_instruments_exchange ON instruments(exchange);
    CREATE INDEX IF NOT EXISTS idx_instruments_active ON instruments(is_active);
    CREATE INDEX IF NOT EXISTS idx_instruments_type ON instruments(instrument_type);
    
    -- Market ticks indexes - optimized for high-frequency data
    CREATE INDEX IF NOT EXISTS idx_ticks_instrument_time 
        ON market_ticks(instrument_key, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time 
        ON market_ticks(symbol, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_ticks_ltt 
        ON market_ticks(ltt DESC); -- For latest trade time queries
    CREATE INDEX IF NOT EXISTS idx_ticks_timestamp 
        ON market_ticks(timestamp DESC); -- For time-range queries
    CREATE INDEX IF NOT EXISTS idx_ticks_volume 
        ON market_ticks(volume) WHERE volume > 0; -- For volume analysis
    
    -- Candles indexes - optimized for chart and analysis queries
    CREATE INDEX IF NOT EXISTS idx_candles_instrument_interval_time 
        ON candles(instrument_key, interval, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_candles_symbol_interval_time 
        ON candles(symbol, interval, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_candles_timestamp 
        ON candles(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_candles_interval_time 
        ON candles(interval, timestamp DESC);
    
    -- Composite indexes for complex queries
    CREATE INDEX IF NOT EXISTS idx_ticks_instrument_ltp_time 
        ON market_ticks(instrument_key, ltp, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_candles_price_volume 
        ON candles(close_price, volume) WHERE volume > 0;
    
    -- JSONB indexes for metadata queries
    CREATE INDEX IF NOT EXISTS idx_ticks_raw_data_gin 
        ON market_ticks USING GIN (raw_data);
    
    -- Create updated_at trigger function
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    -- Apply updated_at trigger to relevant tables
    DROP TRIGGER IF EXISTS update_instruments_updated_at ON instruments;
    CREATE TRIGGER update_instruments_updated_at 
        BEFORE UPDATE ON instruments 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_candles_updated_at ON candles;
    CREATE TRIGGER update_candles_updated_at 
        BEFORE UPDATE ON candles 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    -- Orders table for tracking order placements and executions
    CREATE TABLE IF NOT EXISTS orders (
        id BIGSERIAL PRIMARY KEY,
        order_id VARCHAR(100) NOT NULL UNIQUE,
        exchange_order_id VARCHAR(100),
        parent_order_id VARCHAR(100),
        instrument_key VARCHAR(100) NOT NULL,
        symbol VARCHAR(50) NOT NULL,
        product_type VARCHAR(10) NOT NULL, -- D, I, M, CNC
        order_type VARCHAR(20) NOT NULL, -- MARKET, LIMIT, SL, SL-M
        order_side VARCHAR(10) NOT NULL, -- BUY, SELL
        validity VARCHAR(10) NOT NULL DEFAULT 'DAY', -- DAY, IOC, GTT
        quantity INTEGER NOT NULL,
        filled_quantity INTEGER DEFAULT 0,
        pending_quantity INTEGER DEFAULT 0,
        price DECIMAL(12,4),
        trigger_price DECIMAL(12,4),
        average_price DECIMAL(12,4),
        disclosed_quantity INTEGER,
        status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING, OPEN, COMPLETE, CANCELLED, REJECTED
        status_message TEXT,
        order_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        exchange_timestamp TIMESTAMPTZ,
        tag VARCHAR(100),
        error_message TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign key constraint
        CONSTRAINT fk_orders_instrument 
            FOREIGN KEY (instrument_key) REFERENCES instruments(instrument_key)
            ON DELETE RESTRICT
    );
    
    -- Trades table for executed trade details
    CREATE TABLE IF NOT EXISTS trades (
        id BIGSERIAL PRIMARY KEY,
        trade_id VARCHAR(100) NOT NULL UNIQUE,
        order_id VARCHAR(100) NOT NULL,
        exchange_order_id VARCHAR(100),
        instrument_key VARCHAR(100) NOT NULL,
        symbol VARCHAR(50) NOT NULL,
        trade_price DECIMAL(12,4) NOT NULL,
        trade_quantity INTEGER NOT NULL,
        trade_timestamp TIMESTAMPTZ NOT NULL,
        exchange VARCHAR(20) NOT NULL,
        order_side VARCHAR(10) NOT NULL, -- BUY, SELL
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign key constraints
        CONSTRAINT fk_trades_order 
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
            ON DELETE CASCADE,
        CONSTRAINT fk_trades_instrument 
            FOREIGN KEY (instrument_key) REFERENCES instruments(instrument_key)
            ON DELETE RESTRICT
    );
    
    -- Algorithmic orders table for automated trading
    CREATE TABLE IF NOT EXISTS algo_orders (
        id BIGSERIAL PRIMARY KEY,
        order_id VARCHAR(100) NOT NULL,
        strategy_id VARCHAR(100) NOT NULL,
        signal_id VARCHAR(100) NOT NULL,
        instrument_key VARCHAR(100) NOT NULL,
        confidence_score DECIMAL(5,4), -- 0.0000 to 1.0000
        risk_level VARCHAR(20), -- LOW, MEDIUM, HIGH
        execution_status VARCHAR(20) NOT NULL, -- SUCCESS, FAILED, PENDING
        error_message TEXT,
        metadata JSONB, -- Store additional strategy-specific data
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign key constraints
        CONSTRAINT fk_algo_orders_order 
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
            ON DELETE CASCADE,
        CONSTRAINT fk_algo_orders_instrument 
            FOREIGN KEY (instrument_key) REFERENCES instruments(instrument_key)
            ON DELETE RESTRICT
    );
    
    -- Portfolio positions table for tracking holdings
    CREATE TABLE IF NOT EXISTS portfolio_positions (
        id BIGSERIAL PRIMARY KEY,
        instrument_key VARCHAR(100) NOT NULL,
        symbol VARCHAR(50) NOT NULL,
        exchange VARCHAR(20) NOT NULL,
        product_type VARCHAR(10) NOT NULL, -- D, I, CNC
        quantity INTEGER NOT NULL,
        average_price DECIMAL(12,4) NOT NULL,
        last_price DECIMAL(12,4),
        pnl DECIMAL(15,4) DEFAULT 0,
        day_change DECIMAL(15,4) DEFAULT 0,
        day_change_percentage DECIMAL(8,4) DEFAULT 0,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        
        -- Unique constraint to prevent duplicate positions
        CONSTRAINT uk_positions_instrument_product 
            UNIQUE (instrument_key, product_type),
            
        -- Foreign key constraint
        CONSTRAINT fk_positions_instrument 
            FOREIGN KEY (instrument_key) REFERENCES instruments(instrument_key)
            ON DELETE RESTRICT
    );
    
    -- Orders indexes for fast lookups and reporting
    CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
    CREATE INDEX IF NOT EXISTS idx_orders_instrument_key ON orders(instrument_key);
    CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
    CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
    CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(order_timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_orders_side_status ON orders(order_side, status);
    CREATE INDEX IF NOT EXISTS idx_orders_instrument_status ON orders(instrument_key, status);
    CREATE INDEX IF NOT EXISTS idx_orders_tag ON orders(tag) WHERE tag IS NOT NULL;
    
    -- Trades indexes for performance analysis
    CREATE INDEX IF NOT EXISTS idx_trades_trade_id ON trades(trade_id);
    CREATE INDEX IF NOT EXISTS idx_trades_order_id ON trades(order_id);
    CREATE INDEX IF NOT EXISTS idx_trades_instrument_key ON trades(instrument_key);
    CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(trade_timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON trades(symbol, trade_timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_trades_side_time ON trades(order_side, trade_timestamp DESC);
    
    -- Algo orders indexes for strategy analysis
    CREATE INDEX IF NOT EXISTS idx_algo_orders_strategy ON algo_orders(strategy_id);
    CREATE INDEX IF NOT EXISTS idx_algo_orders_signal ON algo_orders(signal_id);
    CREATE INDEX IF NOT EXISTS idx_algo_orders_status ON algo_orders(execution_status);
    CREATE INDEX IF NOT EXISTS idx_algo_orders_instrument ON algo_orders(instrument_key);
    CREATE INDEX IF NOT EXISTS idx_algo_orders_confidence ON algo_orders(confidence_score DESC);
    CREATE INDEX IF NOT EXISTS idx_algo_orders_created ON algo_orders(created_at DESC);
    
    -- Portfolio positions indexes
    CREATE INDEX IF NOT EXISTS idx_positions_instrument ON portfolio_positions(instrument_key);
    CREATE INDEX IF NOT EXISTS idx_positions_symbol ON portfolio_positions(symbol);
    CREATE INDEX IF NOT EXISTS idx_positions_product ON portfolio_positions(product_type);
    CREATE INDEX IF NOT EXISTS idx_positions_pnl ON portfolio_positions(pnl DESC);
    CREATE INDEX IF NOT EXISTS idx_positions_updated ON portfolio_positions(updated_at DESC);
    
    -- Apply updated_at triggers to new tables
    DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
    CREATE TRIGGER update_orders_updated_at 
        BEFORE UPDATE ON orders 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_algo_orders_updated_at ON algo_orders;
    CREATE TRIGGER update_algo_orders_updated_at 
        BEFORE UPDATE ON algo_orders 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_positions_updated_at ON portfolio_positions;
    CREATE TRIGGER update_positions_updated_at 
        BEFORE UPDATE ON portfolio_positions 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    
    try:
        async with db_manager.get_connection() as conn:
            await conn.execute(schema_sql)
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise


async def create_performance_views():
    """Create database views for common performance queries"""
    
    views_sql = """
    -- Latest prices view for quick LTP lookups
    CREATE OR REPLACE VIEW latest_prices AS
    SELECT DISTINCT ON (instrument_key)
        instrument_key,
        symbol,
        ltp,
        volume,
        timestamp,
        ltt
    FROM market_ticks
    ORDER BY instrument_key, timestamp DESC;
    
    -- Daily statistics view
    CREATE OR REPLACE VIEW daily_stats AS
    SELECT 
        c.instrument_key,
        c.symbol,
        c.timestamp::DATE as date,
        c.open_price,
        c.high_price,
        c.low_price,
        c.close_price,
        c.volume,
        c.vwap,
        LAG(c.close_price) OVER (PARTITION BY c.instrument_key ORDER BY c.timestamp) as prev_close,
        (c.close_price - LAG(c.close_price) OVER (PARTITION BY c.instrument_key ORDER BY c.timestamp)) as change,
        ROUND(((c.close_price - LAG(c.close_price) OVER (PARTITION BY c.instrument_key ORDER BY c.timestamp)) / 
               LAG(c.close_price) OVER (PARTITION BY c.instrument_key ORDER BY c.timestamp)) * 100, 2) as change_percent
    FROM candles c
    WHERE c.interval = '1d'
    ORDER BY c.timestamp DESC;
    
    -- Active instruments view
    CREATE OR REPLACE VIEW active_instruments AS
    SELECT i.*
    FROM instruments i
    WHERE i.is_active = TRUE
    AND EXISTS (
        SELECT 1 FROM market_ticks t 
        WHERE t.instrument_key = i.instrument_key 
        AND t.timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 day'
    );
    """
    
    try:
        async with db_manager.get_connection() as conn:
            await conn.execute(views_sql)
        logger.info("Database performance views created successfully")
    except Exception as e:
        logger.error(f"Failed to create database views: {e}")
        raise


# Convenience functions for common database operations

async def get_connection():
    """Get database connection - for backward compatibility"""
    return db_manager.get_connection()


async def init_database():
    """Initialize database with schema and performance optimizations"""
    await db_manager.initialize()
    await init_database_schema()
    await create_performance_views()
    logger.info("PostgreSQL database initialization completed")


async def close_database():
    """Close database connections"""
    await db_manager.close()