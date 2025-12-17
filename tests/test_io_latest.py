import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import io_latest


def test_load_latest_df_skips_comment_lines(tmp_path):
    csv_path = tmp_path / "latest.csv"
    csv_path.write_text(
        "# meta line\n"
        "# columns=ticker,date\n"
        "ticker,date\n"
        "AAA.OL,2025-01-01\n"
        "BBB.OL,2025-01-02\n",
        encoding="utf-8",
    )

    df = io_latest.load_latest_df(csv_path)
    assert list(df.columns) == ["ticker", "date"]
    assert df["ticker"].tolist() == ["AAA.OL", "BBB.OL"]


def test_load_latest_df_strips_rogue_quote(tmp_path):
    csv_path = tmp_path / "latest.csv"
    csv_path.write_text(
        '"# meta line\n'
        "# columns=ticker,date\n"
        "ticker,date\n"
        "AAA.OL,2025-01-01\n",
        encoding="utf-8",
    )

    df = io_latest.load_latest_df(csv_path)
    assert df["ticker"].tolist() == ["AAA.OL"]


def test_load_latest_tickers_is_unique_and_ordered(tmp_path):
    csv_path = tmp_path / "latest.csv"
    csv_path.write_text(
        "# meta\n"
        "# columns=ticker,date\n"
        "ticker,date\n"
        "AAA.OL,2025-01-01\n"
        "BBB.OL,2025-01-02\n"
        "AAA.OL,2025-01-03\n",
        encoding="utf-8",
    )

    tickers = io_latest.load_latest_tickers(csv_path)
    assert tickers == ["AAA.OL", "BBB.OL"]


class DummyResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise RuntimeError("HTTP error")


def test_load_latest_df_from_url(monkeypatch):
    content = (
        "# meta\n"
        "# columns=ticker,date\n"
        "ticker,date\n"
        "AAA.OL,2025-01-01\n"
    )

    def fake_get(url, timeout=30):
        return DummyResponse(content)

    monkeypatch.setattr(io_latest.requests, "get", fake_get)

    df = io_latest.load_latest_df("https://example.com/latest.csv")
    assert df["ticker"].tolist() == ["AAA.OL"]
