#!/usr/bin/env python3
"""
Database Schema Optimizer for Multi-Timeframe Historical Data
"""
import sqlite3
import sys
import os

def optimize_database_schema():
    """Check and optimize database schema for multi-timeframe queries"""
    
    print("=== DATABASE SCHEMA OPTIMIZATION ===")
    
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute('PRAGMA table_info(candles)')
    columns = cursor.fetchall()
    
    print("Current columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check existing indexes
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='candles'")
    indexes = cursor.fetchall()
    
    print("\nCurrent indexes:")
    if indexes:
        for idx in indexes:
            print(f"  {idx[0]}: {idx[1] or 'PRIMARY KEY'}")
    else:
        print("  No custom indexes")
    
    # Create optimized indexes for multi-timeframe queries
    print("\n=== CREATING OPTIMIZED INDEXES ===")
    
    indexes_to_create = [
        # Composite index for instrument + interval + time range queries
        ("idx_candles_instrument_interval_time", 
         "CREATE INDEX IF NOT EXISTS idx_candles_instrument_interval_time ON candles(instrument_key, interval, timestamp DESC)"),
        
        # Index for symbol-based queries
        ("idx_candles_symbol_interval", 
         "CREATE INDEX IF NOT EXISTS idx_candles_symbol_interval ON candles(symbol, interval, timestamp DESC)"),
        
        # Index for time-based queries across all instruments
        ("idx_candles_timestamp_interval", 
         "CREATE INDEX IF NOT EXISTS idx_candles_timestamp_interval ON candles(timestamp DESC, interval)"),
        
        # Index for latest data queries
        ("idx_candles_latest", 
         "CREATE INDEX IF NOT EXISTS idx_candles_latest ON candles(instrument_key, interval, timestamp DESC, close_price)")
    ]
    
    for idx_name, idx_sql in indexes_to_create:
        try:
            cursor.execute(idx_sql)
            print(f"✅ Created index: {idx_name}")
        except Exception as e:
            print(f"❌ Failed to create {idx_name}: {e}")
    
    # Analyze table for query optimization
    print("\n=== ANALYZING TABLE FOR QUERY OPTIMIZATION ===")
    try:
        cursor.execute("ANALYZE candles")
        print("✅ Table analysis complete")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
    
    # Check data distribution
    print("\n=== DATA DISTRIBUTION ===")
    
    # Count by interval
    cursor.execute("SELECT interval, COUNT(*) as count FROM candles GROUP BY interval ORDER BY count DESC")
    interval_counts = cursor.fetchall()
    
    print("Candles by interval:")
    for interval, count in interval_counts:
        print(f"  {interval}: {count:,} candles")
    
    # Count by instrument
    cursor.execute("SELECT symbol, COUNT(*) as count FROM candles GROUP BY symbol ORDER BY count DESC")
    symbol_counts = cursor.fetchall()
    
    print("\nCandles by instrument:")
    for symbol, count in symbol_counts:
        print(f"  {symbol}: {count:,} candles")
    
    # Check date range
    cursor.execute("SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest FROM candles")
    date_range = cursor.fetchone()
    
    print(f"\nDate range: {date_range[0]} to {date_range[1]}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n✅ Database schema optimization complete!")
    
    # Provide query performance tips
    print("\n=== QUERY PERFORMANCE TIPS ===")
    print("📊 Optimized for these query patterns:")
    print("  • Get candles by instrument + interval + time range")
    print("  • Get latest candles for multiple timeframes")
    print("  • Get candles by symbol across different intervals")
    print("  • Time-series analysis across instruments")
    
    print("\n🚀 Database ready for multi-timeframe historical data!")

if __name__ == "__main__":
    optimize_database_schema()