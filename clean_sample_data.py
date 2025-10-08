import sqlite3

# Connect to database
conn = sqlite3.connect('market_data.db')
cursor = conn.cursor()

# Delete fake sample data for INFY and MARUTI (recognizable by the identical microsecond timestamps)
cursor.execute("""
    DELETE FROM candles 
    WHERE instrument_key IN ('NSE_EQ|INE009A01021', 'NSE_EQ|INE467B01029')
    AND timestamp LIKE '%.358981'
""")

deleted = cursor.rowcount
print(f"Deleted {deleted} fake sample data rows for INFY and MARUTI")

# Check remaining data
cursor.execute("""
    SELECT instrument_key, symbol, COUNT(*) as count, MIN(timestamp) as earliest, MAX(timestamp) as latest 
    FROM candles 
    GROUP BY instrument_key, symbol 
    ORDER BY symbol
""")
data = cursor.fetchall()

print("\n=== REMAINING INSTRUMENTS WITH DATA ===")
for row in data:
    print(f"{row[1]} ({row[0]}): {row[2]} candles from {row[3]} to {row[4]}")

conn.commit()
conn.close()
print("\nDatabase cleaned successfully!")