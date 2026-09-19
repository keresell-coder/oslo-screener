"""Fetch complete Yahoo daily observations without inventing missing prices.

Yahoo sometimes omits closes in a long query while serving a complete candle
for the same day alone. Retry those sessions, then validate the entire window
and apply Yahoo's own adjustment factors. Never use intraday reconstruction.
"""
from __future__ import annotations

import datetime as dt
import time

import numpy as np
import pandas as pd
import yfinance as yf
from yfinance.exceptions import YFRateLimitError

from market_health import is_ose_trading_day

PRICES = ["Open", "High", "Low", "Close", "Adj Close"]
COLUMNS = PRICES + ["Volume"]


class HistoryUnavailable(ValueError):
    pass


def valid_bars(frame: pd.DataFrame) -> pd.Series:
    """Require real, finite OHLCV and a possible candle, allowing float noise."""
    values = frame.reindex(columns=COLUMNS).apply(pd.to_numeric, errors="coerce")
    valid = pd.Series(np.isfinite(values).all(axis=1), index=frame.index)
    valid &= (values[PRICES] > 0).all(axis=1) & (values.Volume >= 0)
    tolerance = values[["Open", "High", "Low", "Close"]].abs().max(axis=1) * 1e-6
    valid &= values.High + tolerance >= values[["Open", "Low", "Close"]].max(axis=1)
    valid &= values.Low - tolerance <= values[["Open", "High", "Close"]].min(axis=1)
    return valid


class YahooHistoryFetcher:
    def __init__(self, expected_session: dt.date, pause=0.6, tries=3,
                 max_session_retries=8, ticker_factory=None, sleep=None):
        self.expected = expected_session
        self.pause = max(0.0, float(pause))
        self.tries = max(1, tries)
        self.max_session_retries = max_session_retries
        self.ticker_factory = ticker_factory or yf.Ticker
        self.sleep = sleep or time.sleep
        self.rate_limited = False
        self.requests = 0
        self.diagnostics = []

    def _request(self, ticker, start, end):
        if self.rate_limited:
            raise HistoryUnavailable("yahoo_rate_limited: waiting for next scheduled attempt")
        last_error = "empty_response"
        for attempt in range(self.tries):
            try:
                self.requests += 1
                frame = ticker.history(
                    start=start.isoformat(), end=end.isoformat(), interval="1d",
                    auto_adjust=False, repair=False, actions=True, keepna=True,
                    timeout=15, raise_errors=True,
                )
                if frame is not None and not frame.empty:
                    frame = frame.copy()
                    index = pd.DatetimeIndex(frame.index)
                    if index.tz is not None:
                        index = index.tz_convert("Europe/Oslo").tz_localize(None)
                    frame.index = index.normalize()
                    if frame.index.has_duplicates:
                        raise HistoryUnavailable("duplicate_price_dates")
                    return frame.loc[(frame.index.date >= start) &
                                     (frame.index.date < end)].sort_index()
            except YFRateLimitError as error:
                # Do not turn a provider-wide limit into hundreds of retries.
                self.rate_limited = True
                raise HistoryUnavailable("yahoo_rate_limited: waiting for next scheduled attempt") from error
            except HistoryUnavailable:
                raise
            except Exception as error:
                last_error = f"{type(error).__name__}: {error}"
            finally:
                # Pace successful requests too, including targeted retries.
                self.sleep(self.pause)
            if attempt + 1 < self.tries:
                self.sleep(2 ** (attempt + 1))
        raise HistoryUnavailable("download_failed: " + last_error)

    def fetch(self, symbol: str) -> pd.DataFrame:
        record = {"ticker": symbol, "retried_sessions": [], "recovered_sessions": []}
        self.diagnostics.append(record)
        try:
            ticker = self.ticker_factory(symbol)
            start = (pd.Timestamp(self.expected) - pd.DateOffset(months=9)).date()
            end = self.expected + dt.timedelta(days=1)
            frame = self._request(ticker, start, end)
            if frame.empty:
                raise HistoryUnavailable("no_completed_session_bars")
            # Include missing sessions after the first available observation,
            # but do not manufacture pre-IPO history or weekend observations.
            dates = pd.date_range(frame.index.min(), pd.Timestamp(self.expected))
            sessions = pd.DatetimeIndex([d for d in dates if is_ose_trading_day(d.date())])
            frame = frame.reindex(sessions)
            bad = frame.index[~valid_bars(frame)]
            record["incomplete_sessions"] = [str(d.date()) for d in bad]
            if len(bad) > self.max_session_retries:
                raise HistoryUnavailable(f"incomplete_historical_ohlc: {len(bad)} sessions; retry budget exceeded")
            for day in bad:
                record["retried_sessions"].append(str(day.date()))
                try:
                    replacement = self._request(ticker, day.date(), day.date() + dt.timedelta(days=1))
                except HistoryUnavailable:
                    if self.rate_limited:
                        raise
                    continue
                if day in replacement.index and valid_bars(replacement).loc[day]:
                    # Replace the complete source observation, never just a
                    # guessed close or an intraday candle's last trade.
                    frame.loc[day, COLUMNS] = replacement.loc[day, COLUMNS]
                    record["recovered_sessions"].append(str(day.date()))
            bad = frame.index[~valid_bars(frame)]
            if len(bad):
                raise HistoryUnavailable("incomplete_historical_ohlc:" + ",".join(str(d.date()) for d in bad))
            factor = frame["Adj Close"] / frame["Close"]
            adjusted = frame[["Open", "High", "Low", "Close", "Volume"]].copy()
            adjusted[["Open", "High", "Low", "Close"]] = adjusted[["Open", "High", "Low", "Close"]].mul(factor, axis=0)
            record.update(status="complete", observations=len(adjusted))
            return adjusted
        except Exception as error:
            record.update(status="unavailable", reason=str(error))
            raise
