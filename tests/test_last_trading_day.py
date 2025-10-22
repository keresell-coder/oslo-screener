import ast
import datetime as dt
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo


def load_last_ose_trading_day():
    path = Path("scripts/build_v231_report.py")
    module_ast = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    func_node = next(
        node for node in module_ast.body
        if isinstance(node, ast.FunctionDef) and node.name == "last_ose_trading_day"
    )
    module_ns = {"dt": dt, "ZoneInfo": ZoneInfo}
    code = compile(ast.Module(body=[func_node], type_ignores=[]), str(path), "exec")
    exec(code, module_ns)
    return module_ns["last_ose_trading_day"]


last_ose_trading_day = load_last_ose_trading_day()


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


if __name__ == "__main__":
    unittest.main()
