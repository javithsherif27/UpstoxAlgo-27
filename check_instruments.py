import sqlite3
import sys
import os

# Change to the project directory
os.chdir('D:/source-code/UpstoxAlgo-27')

try:
    # Connect to the database
    conn = sqlite3.connect('market_data.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Available tables:", [table[0] for table in tables])
    
    # Check if selected_instruments table exists
    table_names = [table[0] for table in tables]
    if 'selected_instruments' in table_names:
        cursor.execute("SELECT COUNT(*) FROM selected_instruments")
        count = cursor.fetchone()[0]
        print(f"Selected instruments count: {count}")
        
        # Show first 5 selected instruments if any exist
        if count > 0:
            cursor.execute("SELECT symbol, name, instrument_key FROM selected_instruments LIMIT 5")
            instruments = cursor.fetchall()
            print("Sample selected instruments:")
            for symbol, name, key in instruments:
                print(f"  {symbol}: {name} ({key})")
        else:
            print("No selected instruments found")
    else:
        print("selected_instruments table does not exist")
    
    # Check if there are any cached instruments
    if 'instrument_cache' in table_names:
        cursor.execute("SELECT COUNT(*) FROM instrument_cache")
        cache_count = cursor.fetchone()[0]
        print(f"Cached instruments count: {cache_count}")
        
        if cache_count > 0:
            cursor.execute("SELECT symbol, name, instrument_key FROM instrument_cache WHERE segment='EQ' LIMIT 5")
            cached_instruments = cursor.fetchall()
            print("Sample cached instruments:")
            for symbol, name, key in cached_instruments:
                print(f"  {symbol}: {name} ({key})")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")