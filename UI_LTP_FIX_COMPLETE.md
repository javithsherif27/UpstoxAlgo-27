# UI LTP Fix - Complete Resolution

## Problem Summary
The UI watchlist was showing LTP = ₹0.00 and invalid values even after successful historical data fetch.

## Root Cause Analysis
1. **Empty Selected Instruments**: The selected instruments list was empty due to cache persistence issues
2. **Cache Not Persisting**: The local cache was using in-memory storage that reset between process runs
3. **Missing Data Pipeline**: No instruments were selected → no live-prices data → empty watchlist

## Complete Fix Applied

### 1. Fixed Cache Persistence (`backend/services/cache_service.py`)
**Problem**: In-memory cache (`_local_cache = {}`) was reset on every new Python process
**Solution**: Added file-based persistence using `local_cache.json`

```python
# Before: Lost data between runs
_local_cache: dict[str, Any] = {}

# After: Persistent file-based cache
def _load_local_cache():
    if os.path.exists(_cache_file):
        with open(_cache_file, 'r') as f:
            _local_cache = json.load(f)

def _save_local_cache():
    with open(_cache_file, 'w') as f:
        json.dump(_local_cache, f, indent=2)
```

### 2. Enhanced Live-Prices Fallback (`backend/routers/market_data.py`)
**Problem**: LTP calculation from candles wasn't robust
**Solution**: Improved change calculation using previous daily close

```python
# Better change calculation
if len(daily_candles) >= 2:
    prev_close = daily_candles[1].close_price
    change = ltp - prev_close  # vs previous day close
    change_pct = (change / prev_close) * 100
else:
    change = ltp - open_price  # vs same day open
    change_pct = ((ltp - open_price) / open_price * 100) if open_price > 0 else 0
```

### 3. Updated Batch Historical Fetch
**Problem**: Fetch-historical only worked for single instruments
**Solution**: Made symbol optional to fetch for all selected instruments

```python
# Now supports both:
POST /api/market-data/fetch-historical?symbol=BYKE&days_back=30  # Single instrument
POST /api/market-data/fetch-historical?days_back=30              # All selected instruments
```

### 4. Pre-populated Default Instruments
**Problem**: Users had empty watchlist with no data to see
**Solution**: Added script to populate popular instruments

```python
# Popular instruments auto-added
default_instruments = [
    {"instrument_key": "NSE_EQ|INE319B01014", "symbol": "BYKE", ...},
    {"instrument_key": "NSE_EQ|INE009A01021", "symbol": "INFY", ...},
    {"instrument_key": "NSE_EQ|INE467B01029", "symbol": "MARUTI", ...}
]
```

## Current Status ✅

### Backend API Working
- **Selected Instruments**: 3 instruments (BYKE, INFY, MARUTI)
- **Live Prices**: Returns real data from database
- **BYKE Data**: LTP=₹62.5, Change=-₹2.32 (-3.58%) ✅
- **Cache**: Persists between server restarts ✅

### Expected UI Behavior
1. **Watchlist Shows**: 3 instruments (BYKE, INFY, MARUTI)
2. **BYKE Shows**: Non-zero LTP and change values from database
3. **INFY/MARUTI Show**: Zero values with "fetch required" (need historical data)
4. **Fetch Button**: "Fetch Historical Data (30 days)" will populate INFY/MARUTI

## API Response Example
```json
{
  "prices": {
    "NSE_EQ|INE319B01014": {
      "symbol": "BYKE",
      "ltp": 62.5,
      "change": -2.32,
      "change_percent": -3.58,
      "open": 67.0,
      "high": 67.0,
      "low": 61.56,
      "volume": 128912,
      "source": "candle"
    }
  },
  "total_instruments": 3
}
```

## Testing Instructions

### 1. Verify Backend
```bash
# Check selected instruments
curl http://localhost:8000/api/instruments/selected

# Check live prices (with valid session cookie)
curl http://localhost:8000/api/market-data/live-prices
```

### 2. Verify Frontend
1. Open http://localhost:3000
2. Login with Upstox token
3. Navigate to trading workspace
4. **Watchlist should show**: BYKE with LTP ₹62.5, Change -₹2.32 (-3.58%)
5. **Fetch Historical**: Click button to populate INFY and MARUTI data

### 3. Add More Instruments
1. Use search bar to find instruments (e.g., "TCS", "RELIANCE")
2. Add to watchlist
3. Click "Fetch Historical Data (30 days)"
4. All selected instruments will get real price data

## Files Modified
1. `backend/services/cache_service.py` - Added file-based cache persistence
2. `backend/routers/market_data.py` - Enhanced live-prices and batch fetch-historical
3. `setup_default_watchlist.py` - Script to populate default instruments

## Summary
- ✅ **Fixed**: Cache persistence issue (root cause)
- ✅ **Enhanced**: Live-prices candle fallback logic
- ✅ **Added**: Batch historical fetch for all selected instruments  
- ✅ **Populated**: Default watchlist with sample data
- ✅ **Verified**: BYKE shows real LTP ₹62.5 from database

The UI should now display **non-zero LTP values** for instruments with historical data in the database.