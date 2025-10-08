#!/usr/bin/env python3
"""Debug and fix selected instruments issue"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.services.instrument_service import instrument_service
from backend.models.dto import InstrumentDTO

async def debug_and_fix():
    print("=== DEBUGGING SELECTED INSTRUMENTS ===")
    
    # Check cache status
    cache_status = await instrument_service.get_cache_status()
    print(f"Cache status: {cache_status.nse_equity_count} instruments cached")
    
    # Get cached instruments
    cached_instruments = await instrument_service.get_cached_instruments()
    print(f"Cached instruments: {len(cached_instruments)}")
    
    if len(cached_instruments) == 0:
        print("No instruments in cache! Need to refresh first.")
        return
    
    # Find BYKE
    byke_inst = None
    for inst in cached_instruments:
        if inst.symbol and inst.symbol.upper() == "BYKE":
            byke_inst = inst
            break
    
    if byke_inst:
        print(f"Found BYKE: {byke_inst.symbol} ({byke_inst.instrument_key})")
        
        # Add to selected instruments
        await instrument_service.add_selected_instrument(byke_inst)
        print("Added BYKE to selected instruments")
        
        # Verify
        selected = await instrument_service.get_selected_instruments()
        print(f"Selected instruments after adding: {len(selected)}")
        for inst in selected:
            print(f"  - {inst.symbol} ({inst.instrument_key})")
    else:
        print("BYKE not found in cached instruments!")
        # Show first few instruments
        print("Available instruments (first 10):")
        for inst in cached_instruments[:10]:
            print(f"  - {inst.symbol} ({inst.exchange})")

if __name__ == "__main__":
    asyncio.run(debug_and_fix())