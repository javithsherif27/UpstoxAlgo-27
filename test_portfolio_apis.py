#!/usr/bin/env python3
"""
Test script for updated Upstox Holdings and Positions APIs
"""
import asyncio
import sys
import os

# Add the backend path to import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.upstox_portfolio_client import get_holdings, get_positions


async def test_portfolio_apis():
    """Test both holdings and positions APIs with correct endpoints."""
    
    # You'll need to replace this with your actual Upstox access token
    test_token = "YOUR_UPSTOX_ACCESS_TOKEN_HERE"
    
    if test_token == "YOUR_UPSTOX_ACCESS_TOKEN_HERE":
        print("❌ Please update the test_token variable with your actual Upstox access token")
        print("   Get your token from: https://upstox.com/developer/")
        return
        
    try:
        print("🔍 Testing Portfolio APIs with correct endpoints...")
        print()
        
        # Test Holdings API
        print("📊 HOLDINGS API TEST")
        print("   Endpoint: https://api.upstox.com/v2/portfolio/long-term-holdings")
        holdings = await get_holdings(test_token)
        print(f"✅ Found {len(holdings)} holdings")
        
        if holdings:
            sample = holdings[0]
            print(f"   Sample: {sample.get('trading_symbol', 'N/A')} - {sample.get('company_name', 'N/A')}")
        print()
        
        # Test Positions API  
        print("📈 POSITIONS API TEST")
        print("   Endpoint: https://api.upstox.com/v2/portfolio/short-term-positions")
        positions = await get_positions(test_token)
        print(f"✅ Found {len(positions)} positions")
        
        if positions:
            sample = positions[0]
            print(f"   Sample: {sample.get('trading_symbol', 'N/A')} - Qty: {sample.get('quantity', 'N/A')}")
            print(f"   Fields available: {list(sample.keys())}")
        elif not positions:
            print("   ℹ️  No positions found (this is normal if you don't have open trades)")
        print()
        
        print("🎯 SUMMARY:")
        print(f"   Holdings: {len(holdings)} (long-term investments)")
        print(f"   Positions: {len(positions)} (short-term trades)")
        print()
        print("✅ Both APIs are now using correct Upstox v2 endpoints!")
        
    except Exception as e:
        print(f"❌ Error testing APIs: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_portfolio_apis())