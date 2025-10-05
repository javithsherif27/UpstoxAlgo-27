from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def now_ist() -> datetime:
    """Return current time in IST as timezone-aware datetime."""
    return datetime.now(tz=IST)


def _floor_minutes(dt: datetime, minutes: int) -> datetime:
    if minutes <= 0:
        return dt
    minute = (dt.minute // minutes) * minutes
    return dt.replace(minute=minute, second=0, microsecond=0)


def floor_to_bucket(ts_ist: datetime, timeframe: str) -> datetime:
    """Floor a tz-aware IST timestamp to the start of its candle bucket.

    timeframe: one of {"1m","5m","15m","1h","1d"}
    """
    if ts_ist.tzinfo is None:
        raise ValueError("ts_ist must be timezone-aware (IST)")
    ts_ist = ts_ist.astimezone(IST)

    if timeframe == "1m":
        return ts_ist.replace(second=0, microsecond=0)
    if timeframe == "5m":
        return _floor_minutes(ts_ist, 5)
    if timeframe == "15m":
        return _floor_minutes(ts_ist, 15)
    if timeframe == "1h":
        return ts_ist.replace(minute=0, second=0, microsecond=0)
    if timeframe == "1d":
        # Start of calendar day in IST
        return ts_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unsupported timeframe: {timeframe}")


def bucket_end(start: datetime, timeframe: str) -> datetime:
    """Return the exclusive end time for a bucket that starts at 'start'."""
    if start.tzinfo is None:
        raise ValueError("start must be timezone-aware (IST)")
    if timeframe == "1m":
        return start + timedelta(minutes=1)
    if timeframe == "5m":
        return start + timedelta(minutes=5)
    if timeframe == "15m":
        return start + timedelta(minutes=15)
    if timeframe == "1h":
        return start + timedelta(hours=1)
    if timeframe == "1d":
        return start + timedelta(days=1)
    raise ValueError(f"Unsupported timeframe: {timeframe}")
