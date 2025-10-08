#!/usr/bin/env python3
"""Add default instruments to selected list for immediate testing"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.services.instrument_service import instrument_service
from backend.models.dto import InstrumentDTO

async def add_default_instruments():
    """Add some popular instruments so users have data to see immediately"""
    
    # Popular instruments that users typically track
    default_instruments = [
        {
            "instrument_key": "NSE_EQ|INE319B01014",  # BYKE (we have data for this)
            "symbol": "BYKE",
            "name": "THE BYKE HOSPITALITY LTD",
            "exchange": "NSE_EQ"
        },
        {
            "instrument_key": "NSE_EQ|INE009A01021",  # INFY
            "symbol": "INFY", 
            "name": "INFOSYS LIMITED",
            "exchange": "NSE_EQ"
        },
        {
            "instrument_key": "NSE_EQ|INE467B01029",  # MARUTI
            "symbol": "MARUTI",
            "name": "MARUTI SUZUKI INDIA LIMITED", 
            "exchange": "NSE_EQ"
        }
    ]
    
    print("=== ADDING DEFAULT INSTRUMENTS TO SELECTED LIST ===")
    
    # Check current selected instruments
    current_selected = await instrument_service.get_selected_instruments()
    current_symbols = {inst.symbol for inst in current_selected}
    
    print(f"Currently selected: {len(current_selected)} instruments")
    
    for inst_data in default_instruments:
        if inst_data["symbol"] not in current_symbols:
            instrument = InstrumentDTO(**inst_data)
            await instrument_service.add_selected_instrument(instrument)
            print(f"Added {instrument.symbol} to selected instruments")
        else:
            print(f"{inst_data['symbol']} already selected")
    
    # Verify final state
    final_selected = await instrument_service.get_selected_instruments()
    print(f"\nFinal selected instruments: {len(final_selected)}")
    for inst in final_selected:
        print(f"  - {inst.symbol} ({inst.instrument_key})")

if __name__ == "__main__":
    asyncio.run(add_default_instruments())