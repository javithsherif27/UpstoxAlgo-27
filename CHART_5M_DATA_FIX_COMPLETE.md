# Chart 5m/15m Data Fix - Complete Resolution

## Problem Summary
User reported: "No 5m chart data available" despite successful Historical Data Fetch completion.

## Root Cause Analysis
Through systematic investigation, discovered the issue was in `backend/services/historical_data_manager.py`:

### The Bug
In the `_process_single_request` method (lines 146-152), the `interval_map` was missing mappings for 5m and 15m intervals:

```python
# BROKEN CODE (before fix):
interval_map = {
    IntervalType.ONE_MINUTE: CandleInterval.ONE_MINUTE,
    IntervalType.THIRTY_MINUTE: CandleInterval.THIRTY_MINUTE,  # Non-existent enum!
    IntervalType.ONE_DAY: CandleInterval.ONE_DAY
    # Missing: FIVE_MINUTE and FIFTEEN_MINUTE!
}
```

### Impact
- When 5m or 15m data was fetched from Upstox API successfully
- The conversion `candle_interval = interval_map[request.interval]` would throw KeyError
- This caused the entire fetch request to fail silently
- No 5m/15m data was ever stored in the database
- Chart showed "No 5m chart data available" because database was empty

### Database Verification
```sql
SELECT DISTINCT interval FROM candles ORDER BY interval;
-- Result: Only ('1d',) - no 5m or 15m data
```

## The Fix
Updated `interval_map` in `backend/services/historical_data_manager.py` line 146:

```python
# FIXED CODE:
interval_map = {
    IntervalType.ONE_MINUTE: CandleInterval.ONE_MINUTE,
    IntervalType.FIVE_MINUTE: CandleInterval.FIVE_MINUTE,      # ✅ Added
    IntervalType.FIFTEEN_MINUTE: CandleInterval.FIFTEEN_MINUTE, # ✅ Added  
    IntervalType.ONE_DAY: CandleInterval.ONE_DAY
}
```

Also removed outdated comment suggesting 5m/15m aren't supported (they are in V3 API).

## Verification Testing
Created `test_5m_fix.py` which confirmed:
- ✅ Interval mapping now works for FIVE_MINUTE and FIFTEEN_MINUTE
- ✅ 5m candle data processing works correctly
- ✅ Database storage successfully stores 5m candles  
- ✅ Test went from 0 to 1 5m candles in database

## Next Steps for User
1. **Re-fetch Historical Data**: Use the "Historical Data Fetch" component to fetch 5m and 15m data again
   - Previous fetch attempts failed silently due to this bug
   - The UI may have shown "success" but no data was actually stored
   
2. **Verify Chart Display**: After re-fetching, the chart should now show:
   - 1M interval data ✅ (should work)
   - 5M interval data ✅ (now fixed) 
   - 15M interval data ✅ (now fixed)
   - 1D interval data ✅ (should work)

## Files Modified
- `backend/services/historical_data_manager.py`: Fixed interval_map with missing FIVE_MINUTE and FIFTEEN_MINUTE mappings

## Status
🎉 **RESOLVED** - The "No 5m chart data available" issue is fixed. User needs to re-fetch 5m/15m data since previous attempts failed due to the mapping bug.