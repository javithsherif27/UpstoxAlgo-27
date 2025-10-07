from __future__ import annotations

import asyncio
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ..models.market import Candle, Tick
from ..utils.time_service import now_ist, floor_to_bucket, bucket_end, IST
from .backfill_client import fetch_historical, fetch_intraday
from .instrument_service import instrument_service
from .websocket_client import upstox_ws_client
from ..utils.logging import get_logger


logger = get_logger(__name__)


TIMEFRAMES = ["1m", "5m", "15m", "1h", "1d"]


@dataclass
class _SeriesState:
    working: Optional[Candle] = None
    closed: "OrderedDict[datetime, Candle]" = None  # keyed by start
    last_processed_ts: Optional[datetime] = None
    last_seen_cum_vol: Optional[int] = None

    def __post_init__(self):
        if self.closed is None:
            self.closed = OrderedDict()


class AggregatorService:
    def __init__(self):
        # state[symbol][timeframe] -> _SeriesState
        self.state: Dict[str, Dict[str, _SeriesState]] = defaultdict(lambda: defaultdict(_SeriesState))
        # token per active stream session (not persisted)
        self._access_token: Optional[str] = None
        self._symbols: List[str] = []
        # Register tick callback bridge from existing ws client
        upstox_ws_client.set_tick_callback(self._on_ws_tick_bridge)
        # Optional reconnect hooks if available
        try:
            upstox_ws_client.set_connection_callbacks(self._on_ws_connected, self._on_ws_disconnected)
        except Exception:
            pass

    # --------------- Public API ---------------
    async def start_stream(self, symbols: List[str], exchange: str, token: str) -> dict:
        self._access_token = token
        self._symbols = symbols

        # Bootstrap history for each symbol
        await asyncio.gather(*(self.bootstrap_symbol(sym, token) for sym in symbols))

        # Resolve to instrument keys and subscribe via existing ws client
        instruments = await instrument_service.search_instruments(symbols)
        instrument_keys = [i.instrument_key for i in instruments if i.instrument_key]
        if not instrument_keys:
            raise ValueError("No instrument keys resolved for symbols")

        await upstox_ws_client.connect(token)
        from ..models.market_data_dto import SubscriptionRequest  # reuse DTO for subscription
        await upstox_ws_client.subscribe(SubscriptionRequest(instrument_keys=instrument_keys, mode="ltpc"))
        return {"ok": True, "subscribed": instrument_keys}

    async def stop_stream(self) -> dict:
        await upstox_ws_client.disconnect()
        self._access_token = None
        self._symbols = []
        return {"ok": True}

    def get_candles(self, symbol: str, timeframe: str, limit: int = 300) -> List[Candle]:
        s = self.state.get(symbol, {}).get(timeframe)
        if not s:
            return []
        items = list(s.closed.values())[-limit:]
        if s.working:
            items.append(s.working)
        # Ensure sorted by start
        return sorted(items, key=lambda c: c.start)

    async def bootstrap_symbol(self, symbol: str, token: str):
        now = now_ist()
        # choose lookback windows per timeframe (free-tier friendly but useful)
        lookbacks = {
            "1m": timedelta(days=2),
            "5m": timedelta(days=5),
            "15m": timedelta(days=10),
            "1h": timedelta(days=45),
            "1d": timedelta(days=365),
        }
        tasks = []
        for tf in TIMEFRAMES:
            frm = now - lookbacks[tf]
            tasks.append(self._backfill_and_merge(symbol, tf, frm, now, token))
        await asyncio.gather(*tasks)

    async def recover_gaps(self, symbol: str, since_ts: datetime):
        if not self._access_token:
            return
        now = now_ist()
        tasks = [self._backfill_and_merge(symbol, tf, since_ts, now, self._access_token) for tf in TIMEFRAMES]
        await asyncio.gather(*tasks)

    # --------------- Internal ---------------
    async def _backfill_and_merge(self, symbol: str, timeframe: str, from_: datetime, to_: datetime, token: str):
        # pick intraday for recent ranges (<= 1 day) else historical
        try:
            delta = to_ - from_
            if delta <= timedelta(days=1):
                candles = await fetch_intraday(symbol, timeframe, from_, to_, token)
            else:
                candles = await fetch_historical(symbol, timeframe, from_, to_, token)
        except Exception as e:
            logger.error(f"Backfill error {symbol} {timeframe}: {e}")
            return

        series = self.state[symbol][timeframe]
        # Merge: replace closed buckets up to the last closed end
        for c in candles:
            # Only store fully closed buckets
            if c.end <= now_ist():
                series.closed[c.start] = c
                # bound memory
                while len(series.closed) > 2000:
                    series.closed.popitem(last=False)

    async def _on_ws_tick_bridge(self, tick_dto):
        """Bridge existing MarketTickDTO to our Tick model and process."""
        try:
            # Convert dto -> Tick
            ts = tick_dto.timestamp.astimezone(IST)
            t = Tick(
                ts=ts,
                ltp=float(tick_dto.ltp),
                volCum=getattr(tick_dto, "volume", None),
                qty=getattr(tick_dto, "ltq", None),
                symbol=str(getattr(tick_dto, "symbol", "")),
                exch="NSE",  # best effort
                seq=None,
            )
            await self.on_tick(t)
        except Exception as e:
            logger.error(f"Tick bridge error: {e}")

    async def on_tick(self, tick: Tick):
        for tf in TIMEFRAMES:
            await self._apply_tick_tf(tick, tf)

    async def _apply_tick_tf(self, tick: Tick, timeframe: str):
        series = self.state[tick.symbol][timeframe]
        bucket_start = floor_to_bucket(tick.ts, timeframe)
        end = bucket_end(bucket_start, timeframe)

        # Determine delta volume
        delta_v = 0
        if tick.qty is not None:
            delta_v = max(int(tick.qty), 0)
        elif tick.volCum is not None:
            last = series.last_seen_cum_vol or 0
            delta_v = max(int(tick.volCum) - last, 0)
            series.last_seen_cum_vol = int(tick.volCum)

        w = series.working
        if w is None or bucket_start > w.start:
            # rollover working -> closed
            if w is not None:
                series.closed[w.start] = w
                while len(series.closed) > 2000:
                    series.closed.popitem(last=False)
            # open new working
            series.working = Candle(
                start=bucket_start,
                end=end,
                o=tick.ltp,
                h=tick.ltp,
                l=tick.ltp,
                c=tick.ltp,
                v=delta_v,
                symbol=tick.symbol,
                timeframe=timeframe,
            )
        else:
            # Update working candle
            w.h = max(w.h, tick.ltp)
            w.l = min(w.l, tick.ltp)
            w.c = tick.ltp
            w.v += delta_v

        series.last_processed_ts = tick.ts

    # Connection hooks
    async def _on_ws_connected(self):
        # On reconnect, backfill gaps from last processed
        if not self._symbols or not self._access_token:
            return
        tasks = []
        for sym in self._symbols:
            # find earliest last_processed among timeframes
            last_ts = None
            for tf in TIMEFRAMES:
                s = self.state.get(sym, {}).get(tf)
                if s and s.last_processed_ts:
                    last_ts = s.last_processed_ts if last_ts is None else min(last_ts, s.last_processed_ts)
            if last_ts:
                tasks.append(self.recover_gaps(sym, last_ts))
        if tasks:
            await asyncio.gather(*tasks)

    async def _on_ws_disconnected(self):
        # nothing required immediately; reconnect logic handled by client
        return
    
    def get_status(self) -> dict:
        """Get current status of the aggregator service"""
        return {
            "is_streaming": self._streaming,
            "symbols": list(self._symbols),
            "symbol_count": len(self._symbols),
            "ws_connected": upstox_ws_client.is_connected,
            "total_candles": sum(len(candles) for candles in self.candles.values()),
            "timeframes": TIMEFRAMES,
            "last_tick_time": getattr(self, '_last_tick_time', None),
        }


aggregator_service = AggregatorService()
