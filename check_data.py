#!/usr/bin/env python3
import sqlite3
import json

print('=== SELECTED INSTRUMENTS FROM CACHE ===')
try:
    with open('local_cache.json', 'r') as f:
        cache = json.load(f)
    
    selected_raw = cache.get('selected_instruments', '[]')
    if isinstance(selected_raw, str):
        selected_list = json.loads(selected_raw)
    else:
        selected_list = selected_raw
    
    print(f'Found {len(selected_list)} selected instruments:')
    for inst in selected_list:
        print(f'  {inst["symbol"]} - {inst["instrument_key"]}')
except Exception as e:
    print(f'Cache read error: {e}')

print('\n=== CANDLES IN DATABASE ===')
conn = sqlite3.connect('market_data.db')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT symbol, instrument_key FROM candles ORDER BY symbol')
rows = cursor.fetchall()
print(f'Found candles for {len(rows)} instruments:')
for row in rows:
    cursor.execute('SELECT interval, COUNT(*) FROM candles WHERE symbol = ? GROUP BY interval', (row[0],))
    intervals = cursor.fetchall()
    interval_info = ', '.join([f'{i[0]}:{i[1]}' for i in intervals])
    print(f'  {row[0]} ({row[1]}) - {interval_info}')
conn.close()