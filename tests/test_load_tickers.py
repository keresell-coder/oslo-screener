import importlib

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def reload_screener():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import screener

    return importlib.reload(screener)


def test_load_tickers_prefers_valid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "valid_tickers.txt").write_text("AAA.OL\nBBB.OL\n")
    (tmp_path / "tickers.txt").write_text("OLD.OL\n")

    screener = reload_screener()

    assert screener.load_tickers() == ["AAA.OL", "BBB.OL"]


def test_load_tickers_falls_back_to_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tickers.txt").write_text("ONLY.OL\n")

    screener = reload_screener()

    assert screener.load_tickers() == ["ONLY.OL"]


def test_load_tickers_raises_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    screener = reload_screener()

    with pytest.raises(FileNotFoundError):
        screener.load_tickers()
