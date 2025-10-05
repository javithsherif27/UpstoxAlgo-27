from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Candle:
    start: datetime
    end: datetime
    o: float
    h: float
    l: float
    c: float
    v: int
    symbol: str
    timeframe: str  # "1m","5m","15m","1h","1d"


@dataclass
class Tick:
    ts: datetime
    ltp: float
    volCum: Optional[int]
    qty: Optional[int]
    symbol: str
    exch: str
    seq: Optional[int]
