from datetime import datetime
from zoneinfo import ZoneInfo

from ..utils.time_service import floor_to_bucket, bucket_end


def test_minute_bucket_ist():
    ist = ZoneInfo("Asia/Kolkata")
    dt = datetime(2025, 1, 1, 9, 31, 42, tzinfo=ist)
    b = floor_to_bucket(dt, "1m")
    assert b.minute == 31 and b.second == 0
    assert bucket_end(b, "1m").minute == 32
