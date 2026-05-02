"""Tests for build_report._enrich closest-trigger calculations."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_report import _enrich


def _row(**kwargs) -> pd.Series:
    defaults = dict(
        ticker="X.OL", signal="NEUTRAL", close=100.0,
        rsi14=50.0, rsi_dir=0.0, macd_hist=0.0,
        pct_above_sma50=0.0, adx14=20.0, rsi6=50.0, mfi14=50.0,
    )
    defaults.update(kwargs)
    return pd.Series(defaults)


class TestClosestTrigger:
    def test_buy_watch_sma_does_not_dominate_when_far_below(self):
        # Price 97% below SMA50 → SMA distance must not collapse to 0.
        r = _row(signal="BUY-watch", rsi14=4.62, macd_hist=-11.34, pct_above_sma50=-97.36)
        e = _enrich(r)
        # MACD (11.34) is much closer to 0 than SMA (97.56)
        assert e["closest"].startswith("MACD→0"), (
            f"Expected MACD closest, got: {e['closest']}"
        )
        assert e["closest_delta"] == pytest.approx(11.34, abs=0.01)

    def test_buy_watch_macd_nearest_small_value(self):
        # MACD almost at 0 beats a barely-oversold RSI and distant SMA
        r = _row(signal="BUY-watch", rsi14=33.77, macd_hist=-0.2131, pct_above_sma50=-3.59)
        e = _enrich(r)
        assert e["closest"].startswith("MACD→0")
        assert e["closest_delta"] == pytest.approx(0.2131, abs=0.001)

    def test_buy_watch_rsi_nearest(self):
        # RSI near 35 threshold beats MACD and SMA
        r = _row(signal="BUY-watch", rsi14=32.13, macd_hist=-3.10, pct_above_sma50=-16.61)
        e = _enrich(r)
        assert e["closest"].startswith("RSI→35")
        assert e["closest_delta"] == pytest.approx(2.87, abs=0.01)

    def test_sell_watch_rsi_near_threshold(self):
        # RSI just above 65 → delta 0.05, beats MACD and SMA
        r = _row(signal="SELL-watch", rsi14=65.05, macd_hist=0.1517, pct_above_sma50=17.80)
        e = _enrich(r)
        assert e["closest"].startswith("RSI→65")
        assert e["closest_delta"] == pytest.approx(0.05, abs=0.001)

    def test_sell_watch_sma_does_not_dominate_when_above(self):
        # Price 18% above SMA50 → SMA distance is 18.2, not 0
        r = _row(signal="SELL-watch", rsi14=65.23, macd_hist=0.1898, pct_above_sma50=4.85)
        e = _enrich(r)
        # MACD (0.19) < RSI (0.23) < SMA (5.05)
        assert e["closest"].startswith("MACD→0")

    def test_sma_delta_zero_when_already_triggered_buy(self):
        # pct_above_sma50 = +5 (price already well above SMA50) → SMA dist = 0
        r = _row(signal="BUY-watch", rsi14=32.0, macd_hist=-1.0, pct_above_sma50=5.0)
        e = _enrich(r)
        sma_dist = max(0.0, 0.2 - 5.0)
        assert sma_dist == 0.0
        # SMA is triggered (dist=0), so SMA should win
        assert e["closest"].startswith("SMA50")
        assert e["closest_delta"] == pytest.approx(0.0, abs=1e-9)

    def test_closest_delta_nan_for_non_watch(self):
        r = _row(signal="BUY", rsi14=20.0, macd_hist=1.0, pct_above_sma50=5.0)
        e = _enrich(r)
        assert np.isnan(e["closest_delta"])
        assert e["closest"] == "—"

    def test_closest_delta_nan_for_neutral(self):
        r = _row(signal="NEUTRAL")
        e = _enrich(r)
        assert np.isnan(e["closest_delta"])
