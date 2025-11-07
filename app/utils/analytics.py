from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Asia/Kolkata")

def now_tz() -> datetime:
    return datetime.now(TZ)

def start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def make_naive(dt: datetime) -> datetime:
    """Converts aware datetime → UTC naive datetime (for TIMESTAMP WITHOUT TIME ZONE)."""
    if dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return dt

def period_ranges():
    now = now_tz()
    today_start = start_of_day(now)
    periods = {}
    periods["yesterday"] = (today_start - timedelta(days=1), end_of_day(today_start - timedelta(days=1)))
    periods["last_week"] = (today_start - timedelta(days=7), end_of_day(today_start - timedelta(days=1)))
    periods["last_30_days"] = (today_start - timedelta(days=30), end_of_day(today_start - timedelta(days=1)))
    periods["last_3_months"] = (today_start - timedelta(days=90), end_of_day(today_start - timedelta(days=1)))
    periods["last_6_months"] = (today_start - timedelta(days=183), end_of_day(today_start - timedelta(days=1)))
    periods["last_year"] = (today_start - timedelta(days=365), end_of_day(today_start - timedelta(days=1)))
    return periods

def range_for_period(period: str):
    """
    returns (start_datetime, end_datetime) in TZ for
    periods: 'yesterday', 'last_week', 'last_month', 'last_6_months', 'last_year'
    """
    now = now_tz()
    today_start = start_of_day(now)
    if period == "yesterday":
        start = today_start - timedelta(days=1)
        end = end_of_day(start)
    elif period == "last_week":
        # last 7 days excluding today
        start = today_start - timedelta(days=7)
        end = end_of_day(today_start - timedelta(days=1))
    elif period == "last_30_days":
        start = today_start - timedelta(days=30)
        end = end_of_day(today_start - timedelta(days=1))
    elif period == "last_6_months":
        # approximate 6 months as 183 days (or you can use relativedelta)
        start = today_start - timedelta(days=183)
        end = end_of_day(today_start - timedelta(days=1))
    elif period == "last_year":
        start = today_start - timedelta(days=365)
        end = end_of_day(today_start - timedelta(days=1))
    else:
        raise ValueError("unsupported period")
    return start, end