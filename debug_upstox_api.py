#!/usr/bin/env python3
"""
Fix Upstox API 400 Bad Request errors for historical candle fetching
Issues identified:
1. Wrong interval format for 15minute (should use intraday endpoint)
2. Date range validation needed
3. Different endpoints for historical vs intraday data
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(__file__))

async def debug_upstox_api():
    """Debug and test Upstox API calls"""
    
    print("🔍 DEBUGGING UPSTOX API CALLS")
    print("=" * 50)
    
    # Test token from earlier
    token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI0M0NNNjQiLCJqdGkiOiI2OGUzNTY5ZGM4ZWNjMjY4MTk3NDY5NjEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzU5NzI5MzA5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NTk3ODgwMDB9.GeEjXnGWqjpOwz6zZlu6kptnD5Wt3U9NtF5cX68dBMo"
    
    print("\n📊 Upstox API Endpoint Analysis:")
    print("Current failing URL: https://api.upstox.com/v2/historical-candle/NSE_EQ|INE319B01014/15minute/2025-10-08/2025-10-01")
    
    print("\n❌ Issues Identified:")
    print("1. 15minute interval may not be supported in historical endpoint")
    print("2. Date range may be invalid (requesting future dates)")
    print("3. Should use intraday endpoint for minute-level data")
    
    print("\n🔧 Upstox API Endpoints:")
    print("Historical (day/week/month): /v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}")
    print("Intraday (minute intervals): /v2/historical-candle/intraday/{instrument_key}/{interval}")
    
    # Check current date
    today = datetime.now()
    print(f"\n📅 Date Analysis:")
    print(f"Today: {today.strftime('%Y-%m-%d')}")
    print(f"Requested range: 2025-10-01 to 2025-10-08")
    print(f"Issue: Requesting data from future dates!")
    
    print("\n✅ Correct API Usage:")
    
    # Calculate proper date range (last 7 days)
    end_date = today - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=7)  # 7 days ago
    
    correct_from = start_date.strftime("%Y-%m-%d")
    correct_to = end_date.strftime("%Y-%m-%d")
    
    print(f"Corrected date range: {correct_from} to {correct_to}")
    
    print(f"\n🔧 Fixed API Calls:")
    print(f"1. Daily data: /v2/historical-candle/NSE_EQ|INE319B01014/day/{correct_to}/{correct_from}")
    print(f"2. 15min data: /v2/historical-candle/intraday/NSE_EQ|INE319B01014/15minute")
    print(f"3. 5min data: /v2/historical-candle/intraday/NSE_EQ|INE319B01014/5minute")
    print(f"4. 1min data: /v2/historical-candle/intraday/NSE_EQ|INE319B01014/1minute")
    
    print(f"\n📋 Upstox API Rules:")
    print(f"• Historical endpoint: Only 'day', 'week', 'month' intervals")
    print(f"• Intraday endpoint: '1minute', '5minute', '15minute', '30minute', '60minute'") 
    print(f"• No future dates allowed")
    print(f"• Intraday data limited to recent days (typically 1-7 days)")
    print(f"• Historical data can go back months/years")

if __name__ == "__main__":
    asyncio.run(debug_upstox_api())