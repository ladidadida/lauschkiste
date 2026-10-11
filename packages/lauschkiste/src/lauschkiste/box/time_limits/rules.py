"""The rules of the time limits, without clocks or threads: quiet hours and the allowance of a day."""

from datetime import datetime, time, timedelta
from typing import Dict, Optional, Tuple

DAYS = {'every day': range(7), 'weekdays': range(5), 'weekends': range(5, 7)}


def parse_time(text: str) -> time:
    hours, _, minutes = text.strip().partition(':')
    return time(int(hours), int(minutes or 0))


def applies(days: str, when: datetime) -> bool:
    return when.weekday() in DAYS.get(days, DAYS['every day'])


def quiet_until(ranges: Dict[str, Tuple[str, str, str]], now: datetime) -> Optional[datetime]:
    """When the quiet hours that cover ``now`` end, or None. A range that runs past midnight belongs to the day it
    starts on: 19:30-07:00 on weekdays covers Friday evening until Saturday morning."""
    for start_text, end_text, days in ranges.values():
        start, end = parse_time(start_text), parse_time(end_text)
        today = now.date()
        if start < end:
            if applies(days, now) and start <= now.time() < end:
                return datetime.combine(today, end)
        elif start > end:
            if applies(days, now) and now.time() >= start:
                return datetime.combine(today + timedelta(days=1), end)
            if applies(days, now - timedelta(days=1)) and now.time() < end:
                return datetime.combine(today, end)
    return None


def limit_seconds(weekday_minutes: int, weekend_minutes: Optional[int], now: datetime) -> Optional[int]:
    """The listening time of the day in seconds; None for no limit."""
    minutes = weekend_minutes if weekend_minutes is not None and now.weekday() >= 5 else weekday_minutes
    return minutes * 60 if minutes else None
