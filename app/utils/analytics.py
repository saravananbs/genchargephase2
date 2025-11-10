from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Asia/Kolkata")

def now_tz() -> datetime:
    """
    Return the current datetime localized to the application's timezone.

    Returns:
        datetime: Timezone-aware datetime in `Asia/Kolkata`.
    """
    return datetime.now(TZ)

def start_of_day(dt: datetime) -> datetime:
    """
    Compute the start of the day (00:00:00) for a given datetime.

    Args:
        dt (datetime): A timezone-aware or naive datetime.

    Returns:
        datetime: Datetime set to the start of the same day.
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def end_of_day(dt: datetime) -> datetime:
    """
    Compute the end of the day (23:59:59.999999) for a given datetime.

    Args:
        dt (datetime): A timezone-aware or naive datetime.

    Returns:
        datetime: Datetime set to the end of the same day.
    """
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def make_naive(dt: datetime) -> datetime:
    """
    Convert a timezone-aware datetime to a naive UTC datetime.

    This is useful when persisting values into databases that expect
    TIMESTAMP WITHOUT TIME ZONE.

    Args:
        dt (datetime): Input datetime which may be timezone-aware or naive.

    Returns:
        datetime: Naive UTC datetime if input was aware, otherwise the original dt.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return dt

def period_ranges():
    """
    Build a mapping of common period names to (start, end) datetimes.

    Periods returned are timezone-aware in the application's timezone and
    typically end at the end of the previous day (exclude today).

    Returns:
        dict: Mapping from period name to a (start_datetime, end_datetime) tuple.
    """
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