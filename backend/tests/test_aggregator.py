from datetime import datetime
from zoneinfo import ZoneInfo

from ..services.aggregator_service import aggregator_service
from ..models.market import Tick


def test_on_tick_basic_rollover():
    ist = ZoneInfo("Asia/Kolkata")
    sym = "RELIANCE"
    # ensure clean state
    aggregator_service.state.clear()

    t1 = Tick(ts=datetime(2025,1,1,9,30,5,tzinfo=ist), ltp=100.0, volCum=None, qty=10, symbol=sym, exch="NSE", seq=None)
    t2 = Tick(ts=datetime(2025,1,1,9,30,40,tzinfo=ist), ltp=101.0, volCum=None, qty=5, symbol=sym, exch="NSE", seq=None)
    t3 = Tick(ts=datetime(2025,1,1,9,31,1,tzinfo=ist), ltp=99.0, volCum=None, qty=3, symbol=sym, exch="NSE", seq=None)

    import asyncio
    asyncio.run(aggregator_service.on_tick(t1))
    asyncio.run(aggregator_service.on_tick(t2))
    asyncio.run(aggregator_service.on_tick(t3))

    candles = aggregator_service.get_candles(sym, "1m", limit=10)
    assert len(candles) >= 2
    assert candles[-2].o == 100.0
    assert candles[-2].h == 101.0
    assert candles[-2].c == 101.0
    assert candles[-2].v == 15
