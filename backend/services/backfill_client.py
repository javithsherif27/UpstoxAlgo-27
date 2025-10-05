from __future__ import annotations

import asyncio
from typing import List
from datetime import datetime

import httpx

from ..models.market import Candle
from ..utils.time_service import IST


BASE_URL = "https://api.upstox.com/v3"


def _auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def _normalize_candle(symbol: str, timeframe: str, row: dict) -> Candle:
    # Upstox candle fields typically: timestamp, open, high, low, close, volume
    ts = datetime.fromisoformat(row["timestamp"]).astimezone(IST)
    # derive end using timeframe duration
    from ..utils.time_service import bucket_end, floor_to_bucket
    start = floor_to_bucket(ts, timeframe)
    end = bucket_end(start, timeframe)
    return Candle(
        start=start,
        end=end,
        o=float(row["open"]),
        h=float(row["high"]),
        l=float(row["low"]),
        c=float(row["close"]),
        v=int(row.get("volume") or 0),
        symbol=symbol,
        timeframe=timeframe,
    )


async def _fetch_with_client(url: str, params: dict, token: str) -> list[dict]:
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0), limits=limits) as client:
        for attempt in range(4):
            try:
                res = await client.get(url, headers=_auth_headers(token), params=params)
                res.raise_for_status()
                data = res.json()
                # Normalizing known envelope shapes; adjust as per actual response
                if isinstance(data, dict):
                    if "data" in data:
                        data = data["data"]
                    if isinstance(data, dict) and "candles" in data:
                        data = data["candles"]
                return data if isinstance(data, list) else []
            except httpx.HTTPError:
                if attempt == 3:
                    raise
                await asyncio.sleep(0.5 * (2 ** attempt))


async def fetch_historical(symbol: str, timeframe: str, from_: datetime, to_: datetime, token: str) -> List[Candle]:
    url = f"{BASE_URL}/historical-candle/{symbol}/{timeframe}"
    params = {"from": from_.astimezone(IST).isoformat(), "to": to_.astimezone(IST).isoformat()}
    rows = await _fetch_with_client(url, params, token)
    return [_normalize_candle(symbol, timeframe, r) for r in rows]


async def fetch_intraday(symbol: str, timeframe: str, from_: datetime, to_: datetime, token: str) -> List[Candle]:
    url = f"{BASE_URL}/intra-day-candle/{symbol}/{timeframe}"
    params = {"from": from_.astimezone(IST).isoformat(), "to": to_.astimezone(IST).isoformat()}
    rows = await _fetch_with_client(url, params, token)
    return [_normalize_candle(symbol, timeframe, r) for r in rows]
