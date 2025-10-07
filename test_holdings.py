#!/usr/bin/env python3
"""
Test script for updated Upstox Holdings API
"""
import asyncio
import sys
import os

# Add the backend path to import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.upstox_portfolio_client import get_holdings, get_positions


async def test_holdings_api():
    """Test the holdings API with a sample token."""
    
    # You'll need to replace this with your actual Upstox access token
    test_token = "YOUR_UPSTOX_ACCESS_TOKEN_HERE"
    
    if test_token == "YOUR_UPSTOX_ACCESS_TOKEN_HERE":
        print("❌ Please update the test_token variable with your actual Upstox access token")
        print("   Get your token from: https://upstox.com/developer/")
        return
        
    try:
        print("🔍 Testing Holdings API...")
        print(f"   Using endpoint: https://api.upstox.com/v2/portfolio/long-term-holdings")
        
        holdings = await get_holdings(test_token)
        
        print(f"✅ Holdings API Response:")
        print(f"   Found {len(holdings)} holdings")
        
        if holdings:
            print(f"\n📊 Sample Holding (first one):")
            sample = holdings[0]
            print(f"   Symbol: {sample.get('trading_symbol', 'N/A')}")
            print(f"   Company: {sample.get('company_name', 'N/A')}")
            print(f"   Quantity: {sample.get('quantity', 'N/A')}")
            print(f"   Average Price: ₹{sample.get('average_price', 'N/A')}")
            print(f"   Last Price: ₹{sample.get('last_price', 'N/A')}")
            print(f"   P&L: ₹{sample.get('pnl', 'N/A')}")
            
            print(f"\n🔍 Full structure of first holding:")
            for key, value in sample.items():
                print(f"   {key}: {value}")
        else:
            print("   No holdings found in your account")
            
        print(f"\n🔍 Testing Positions API...")  
        positions = await get_positions(test_token)
        print(f"✅ Positions API Response:")
        print(f"   Found {len(positions)} positions")
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_holdings_api())