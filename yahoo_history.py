"""Fetch complete daily observations without inventing missing prices.

Yahoo sometimes omits closes in a long query while serving a complete candle
for the same day alone. Retry those sessions, then validate the entire window
and apply Yahoo's own adjustment factors. An optional exchange daily-file
backup must reconcile to that price basis. Never use intraday reconstruction.
"""
from __future__ import annotations

import datetime as dt
import threading
import time

import numpy as np
import pandas as pd
import yfinance as yf
from yfinance.exceptions import YFRateLimitError, YFPricesMissingError

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
                 max_session_retries=8, ticker_factory=None, sleep=None, daily_fallback=None, mfi_length=14):
        self.expected = expected_session
        self.pause = max(0.0, float(pause))
        self.tries = max(1, tries)
        self.max_session_retries = max_session_retries
        self.ticker_factory = ticker_factory or yf.Ticker
        self.sleep = sleep or time.sleep
        self.rate_limited = False
        self.requests = 0
        self.diagnostics = []
        self._request_lock = threading.Lock()
        self.daily_fallback = daily_fallback
        self.mfi_observations = max(2, int(mfi_length) + 1)

    def _pace_request(self):
        with self._request_lock:
            if self.rate_limited:
                raise HistoryUnavailable("yahoo_rate_limited: waiting for next scheduled attempt")
            self.sleep(self.pause)
            self.requests += 1

    def _request(self, ticker, start, end):
        if self.rate_limited:
            raise HistoryUnavailable("yahoo_rate_limited: waiting for next scheduled attempt")
        last_error = "empty_response"
        for attempt in range(self.tries):
            # One shared pacer for all workers, including targeted retries.
            # Wait before starting so slow responses can overlap safely.
            self._pace_request()
            try:
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
                with self._request_lock:
                    self.rate_limited = True
                raise HistoryUnavailable("yahoo_rate_limited: waiting for next scheduled attempt") from error
            except YFPricesMissingError as error:
                raise HistoryUnavailable("no_completed_session_bars") from error
            except HistoryUnavailable:
                raise
            except Exception as error:
                last_error = f"{type(error).__name__}: {error}"
            if attempt + 1 < self.tries:
                self.sleep(2 ** (attempt + 1))
        raise HistoryUnavailable("download_failed: " + last_error)

    def _recover_daily_observations(self, symbol, frame, events, record):
        """Reconcile exchange observations to Yahoo's fresh adjustment basis.

        A factor can only come from a matching Yahoo close on the same date,
        or a matching adjacent observation with no intervening corporate event.
        Never interpolate prices or turn zero-trade rows into observed candles.
        """
        if self.daily_fallback is None:
            return None
        good = valid_bars(frame)
        bad = frame.index[~good]
        if not len(bad):
            return None
        anchors = frame.index[good]
        before = anchors[anchors < bad[0]]
        start = min(before[-1] if len(before) else bad[0], frame.index[max(0, len(frame) - self.mfi_observations)])
        self._pace_request()
        try:
            source = self.daily_fallback(symbol, start.date(), self.expected)
            source = source.copy()
            source['Adj Close'] = source['Close']
            source_valid = valid_bars(source)
        except Exception as error:
            record['daily_fallback_error'] = str(error)
            return None
        record['daily_fallback_url'] = source.attrs.get('source_url')
        repaired = []

        def same_price(a, b):
            return np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0 and np.isclose(a, b, rtol=1e-5, atol=0)

        for day in bad:
            if day not in source.index or not source_valid.loc[day]:
                if day in source.index and source.loc[day, 'Volume'] == 0 and (source.loc[day, ['Open', 'High', 'Low']] == 0).all():
                    record.setdefault('nontrading_sessions', []).append(day.date().isoformat())
                continue
            close, adj = frame.loc[day, ['Close', 'Adj Close']]
            factor = None
            if same_price(close, source.loc[day, 'Close']) and np.isfinite(adj) and adj > 0:
                factor = adj / close
            elif not (np.isfinite(close) and close > 0):
                following = anchors[anchors > day]
                preceding = anchors[anchors < day]
                candidates = ([following[0]] if len(following) else []) + ([preceding[-1]] if len(preceding) else [])
                for anchor in candidates:
                    if anchor not in source.index or not source_valid.loc[anchor]:
                        continue
                    if not same_price(frame.loc[anchor, 'Close'], source.loc[anchor, 'Close']):
                        continue
                    lo, hi = sorted([day, anchor])
                    action_columns = ['Dividends', 'Stock Splits']
                    if not all(c in frame for c in action_columns):
                        continue
                    interval = frame.loc[(frame.index > lo) & (frame.index <= hi), action_columns]
                    # Include action-only dates (e.g. a weekend) from the source.
                    extra = events.loc[(events.index > lo) & (events.index <= hi)]
                    if not interval.notna().all().all() or not (interval == 0).all().all():
                        continue
                    if not extra.notna().all().all() or not (extra == 0).all().all():
                        continue
                    factor = frame.loc[anchor, 'Adj Close'] / frame.loc[anchor, 'Close']
                    break
            if factor is None or not np.isfinite(factor) or factor <= 0:
                continue
            frame.loc[day, COLUMNS] = source.loc[day, COLUMNS]
            frame.loc[day, 'Adj Close'] = source.loc[day, 'Close'] * factor
            repaired.append(day.date().isoformat())
        record['euronext_recovered_sessions'] = repaired
        record['recovered_sessions'].extend(repaired)
        return source if repaired else None

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
            events = frame.reindex(columns=['Dividends', 'Stock Splits']).copy()
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
                    for col in ('Dividends', 'Stock Splits'):
                        if col in replacement:
                            frame.loc[day, col] = replacement.loc[day, col]
                            events.loc[day, col] = replacement.loc[day, col]
                    record["recovered_sessions"].append(str(day.date()))
            recovered_source = self._recover_daily_observations(symbol, frame, events, record)
            bad = frame.index[~valid_bars(frame)]
            if len(bad):
                raise HistoryUnavailable("incomplete_historical_ohlc:" + ",".join(str(d.date()) for d in bad))
            factor = frame["Adj Close"] / frame["Close"]
            adjusted = frame[["Open", "High", "Low", "Close", "Volume"]].copy()
            adjusted[["Open", "High", "Low", "Close"]] = adjusted[["Open", "High", "Low", "Close"]].mul(factor, axis=0)
            if recovered_source is not None:
                adjusted.attrs['source_note'] = 'Euronext daily recovery: ' + ','.join(record['euronext_recovered_sessions'])
                # MFI needs a consistent volume definition throughout its window.
                # Use one full exchange window, or withhold MFI alone.
                adjusted.attrs['mixed_price_sources'] = True
                dates = frame.index[-self.mfi_observations:]
                recent = recovered_source.reindex(dates)
                agrees = np.isclose(recent.Close, frame.loc[dates, 'Close'], rtol=1e-5, atol=0).all()
                if len(dates) == self.mfi_observations and valid_bars(recent).all() and agrees:
                    recent = recent[['High', 'Low', 'Close', 'Volume']].copy()
                    recent[['High', 'Low', 'Close']] = recent[['High', 'Low', 'Close']].mul(factor.loc[dates], axis=0)
                    adjusted.attrs['mfi_history'] = recent.to_dict('records')
            record.update(status="complete", observations=len(adjusted))
            return adjusted
        except Exception as error:
            record.update(status="unavailable", reason=str(error))
            raise
