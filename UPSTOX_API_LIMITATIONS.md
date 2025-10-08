# UPSTOX API INTERVAL LIMITATIONS - CRITICAL UPDATE ⚠️

## Issue Discovered
The Upstox API intraday endpoint **only supports `1minute` and `30minute` intervals**, not the full range we initially implemented.

## API Error Message
```
"Interval accepts one of (1minute,30minute)"
```

## Actual Upstox API Support

### ✅ Supported Intervals
- **1minute** - Intraday endpoint (/v2/historical-candle/intraday/)
- **30minute** - Intraday endpoint (/v2/historical-candle/intraday/)
- **day** - Historical endpoint (/v2/historical-candle/)
- **week** - Historical endpoint (/v2/historical-candle/)
- **month** - Historical endpoint (/v2/historical-candle/)

### ❌ NOT Supported
- **5minute** - Not available in Upstox API
- **15minute** - Not available in Upstox API

## Solutions

### Option 1: Use Available Intervals Only ⭐ RECOMMENDED
Update the system to use only supported intervals:
- **1minute** (for short-term analysis)
- **30minute** (for medium-term analysis)
- **daily** (for long-term analysis)

### Option 2: Calculate Derived Intervals
- Fetch 1-minute data and aggregate to 5-minute/15-minute locally
- More API calls but provides the desired intervals

### Option 3: Mixed Approach
- Use Upstox for 1m, 30m, daily
- Add note that 5m/15m are not available from this data provider

## Immediate Fix Required
Update the IntervalType enum and remove unsupported intervals from UI.