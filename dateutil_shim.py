"""아주 작은 add_months 헬퍼 — dateutil 의존 회피."""
from datetime import datetime
from calendar import monthrange


def add_months(d: datetime, months: int) -> datetime:
    m = d.month - 1 + months
    year = d.year + m // 12
    month = m % 12 + 1
    last_day = monthrange(year, month)[1]
    day = min(d.day, last_day)
    return d.replace(year=year, month=month, day=day)
