import datetime as dt
import unittest
from zoneinfo import ZoneInfo

from scripts.trading_calendar import last_ose_trading_day


class LastOseTradingDayTests(unittest.TestCase):
    tz = ZoneInfo("Europe/Oslo")

    def test_weekend_rolls_back_to_friday(self):
        sunday = dt.datetime(2025, 8, 17, 10, 0, tzinfo=self.tz)
        self.assertEqual(last_ose_trading_day(sunday), dt.date(2025, 8, 15))

    def test_monday_morning_uses_previous_friday(self):
        monday_morning = dt.datetime(2025, 8, 18, 8, 0, tzinfo=self.tz)
        self.assertEqual(last_ose_trading_day(monday_morning), dt.date(2025, 8, 15))

    def test_weekday_before_cutoff_uses_previous_day(self):
        tuesday_early = dt.datetime(2025, 8, 19, 8, 59, tzinfo=self.tz)
        self.assertEqual(last_ose_trading_day(tuesday_early), dt.date(2025, 8, 18))

    def test_weekday_after_cutoff_returns_same_day(self):
        tuesday_late = dt.datetime(2025, 8, 19, 9, 30, tzinfo=self.tz)
        self.assertEqual(last_ose_trading_day(tuesday_late), dt.date(2025, 8, 19))

    def test_naive_date_treated_as_same_day(self):
        naive_date = dt.date(2025, 8, 20)
        self.assertEqual(last_ose_trading_day(naive_date), dt.date(2025, 8, 20))

    def test_naive_datetime_before_cutoff_rolls_back(self):
        naive_dt = dt.datetime(2025, 8, 19, 8, 45)
        self.assertEqual(last_ose_trading_day(naive_dt), dt.date(2025, 8, 18))

    def test_naive_datetime_after_cutoff_stays_same_day(self):
        naive_dt = dt.datetime(2025, 8, 19, 9, 30)
        self.assertEqual(last_ose_trading_day(naive_dt), dt.date(2025, 8, 19))

    # Holiday-aware tests
    def test_maundy_thursday_rolls_back_to_wednesday(self):
        # Maundy Thursday 2026 = April 2; before cutoff → rolls to previous trading day
        maundy_thursday_morning = dt.datetime(2026, 4, 2, 8, 0, tzinfo=self.tz)
        self.assertEqual(last_ose_trading_day(maundy_thursday_morning), dt.date(2026, 4, 1))

    def test_good_friday_rolls_back_to_wednesday(self):
        # Good Friday 2026 = April 3; noon → rolls back past Maundy Thursday to April 1
        good_friday = dt.date(2026, 4, 3)
        self.assertEqual(last_ose_trading_day(good_friday), dt.date(2026, 4, 1))

    def test_easter_monday_rolls_back_to_wednesday(self):
        # Easter Monday 2026 = April 6; noon → rolls back to April 1
        easter_monday = dt.date(2026, 4, 6)
        self.assertEqual(last_ose_trading_day(easter_monday), dt.date(2026, 4, 1))

    def test_constitution_day_rolls_back(self):
        # May 17 2026 is a Sunday so it's already a weekend; previous trading day is May 15 (Friday)
        constitution_day = dt.date(2026, 5, 17)
        self.assertEqual(last_ose_trading_day(constitution_day), dt.date(2026, 5, 15))

    def test_ascension_day_rolls_back(self):
        # Ascension Day 2026 = May 14 (Thursday); noon → rolls back to May 13 (Wednesday)
        ascension = dt.date(2026, 5, 14)
        self.assertEqual(last_ose_trading_day(ascension), dt.date(2026, 5, 13))


if __name__ == "__main__":
    unittest.main()
