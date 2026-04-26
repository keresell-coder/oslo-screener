"""Norwegian trading calendar utilities.

Provides the list of Oslo Stock Exchange (OSE) public holidays and a
helper that returns the last OSE trading day relative to a given moment.
"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

_OSLO_TZ = ZoneInfo("Europe/Oslo")


def _easter_sunday(year: int) -> dt.date:
    """Anonymous Gregorian algorithm — returns Easter Sunday for *year*."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return dt.date(year, month, day)


def norwegian_public_holidays(year: int) -> frozenset[dt.date]:
    """Return OSE-closing Norwegian public holidays for *year*."""
    easter = _easter_sunday(year)
    return frozenset({
        dt.date(year, 1, 1),                        # New Year's Day
        easter - dt.timedelta(days=3),              # Maundy Thursday
        easter - dt.timedelta(days=2),              # Good Friday
        easter,                                     # Easter Sunday
        easter + dt.timedelta(days=1),              # Easter Monday
        dt.date(year, 5, 1),                        # Labour Day
        dt.date(year, 5, 17),                       # Constitution Day
        easter + dt.timedelta(days=39),             # Ascension Day
        easter + dt.timedelta(days=49),             # Whit Sunday
        easter + dt.timedelta(days=50),             # Whit Monday
        dt.date(year, 12, 25),                      # Christmas Day
        dt.date(year, 12, 26),                      # Boxing Day
    })


def is_ose_trading_day(date: dt.date) -> bool:
    """Return True if OSE trades on *date* (weekday and not a public holiday)."""
    if date.weekday() >= 5:
        return False
    return date not in norwegian_public_holidays(date.year)


def last_ose_trading_day(today: dt.date | dt.datetime | None = None) -> dt.date:
    """Return the most recent OSE trading day relative to *today*.

    If *today* is None, the current Oslo wall-clock time is used.
    On a trading day before 09:15 Oslo time, returns the previous trading day
    (closing prices are not yet available for the current day).
    """
    if today is None:
        now = dt.datetime.now(_OSLO_TZ)
    elif isinstance(today, dt.datetime):
        now = today.astimezone(_OSLO_TZ) if today.tzinfo else today.replace(tzinfo=_OSLO_TZ)
    else:
        # Treat bare dates as noon so they are never rolled back by the cutoff.
        now = dt.datetime.combine(today, dt.time(hour=12), tzinfo=_OSLO_TZ)

    d = now.date()

    # Roll back past weekends and public holidays.
    while not is_ose_trading_day(d):
        d -= dt.timedelta(days=1)

    # Before closing prices are normally available (~09:15), use the previous day.
    cutoff = dt.time(hour=9, minute=15)
    if now.date() == d and now.time() < cutoff:
        d -= dt.timedelta(days=1)
        while not is_ose_trading_day(d):
            d -= dt.timedelta(days=1)

    return d
