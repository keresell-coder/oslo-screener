import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import validate_tickers


def test_min_days_follows_config(tmp_path, monkeypatch):
    monkeypatch.delenv("MIN_HISTORY_DAYS", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text("min_history_days: 45\n")

    assert validate_tickers.load_min_history_days() == 45


def test_min_days_prefers_env_override(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text("min_history_days: 45\n")
    monkeypatch.setenv("MIN_HISTORY_DAYS", "5")

    assert validate_tickers.load_min_history_days() == 5


def test_min_days_falls_back_when_config_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("MIN_HISTORY_DAYS", raising=False)
    monkeypatch.chdir(tmp_path)

    assert validate_tickers.load_min_history_days() == 30


def test_check_shrink_allows_small_drop():
    previous = [f"T{i}.OL" for i in range(100)]

    assert validate_tickers.check_shrink(previous, previous[5:]) is None


def test_check_shrink_flags_large_drop():
    previous = [f"T{i}.OL" for i in range(100)]

    problem = validate_tickers.check_shrink(previous, previous[20:])

    assert problem is not None
    assert "20.0 %" in problem


def test_check_shrink_ignores_first_run():
    assert validate_tickers.check_shrink([], []) is None
