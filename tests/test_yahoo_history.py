import datetime as dt

import pandas as pd
import pytest
from yfinance.exceptions import YFRateLimitError

from yahoo_history import HistoryUnavailable, YahooHistoryFetcher, valid_bars

DAY = dt.date(2026, 9, 18)


def history():
    return pd.DataFrame({"Open": 100., "High": 105., "Low": 98., "Close": 102.,
                         "Adj Close": 51., "Volume": 1000.},
                        index=pd.date_range("2026-09-14", "2026-09-18", tz="Europe/Oslo"))


def fetcher(reply, **kwargs):
    calls, sleeps = [], []
    class Client:
        def history(self, **params):
            calls.append(params)
            assert params['auto_adjust'] is False and params['repair'] is False
            assert params['keepna'] is True and params['raise_errors'] is True
            return reply(params)
    return YahooHistoryFetcher(DAY, ticker_factory=lambda _: Client(), sleep=sleeps.append,
                               **kwargs), calls, sleeps


def test_long_response_missing_two_closes_recovers_from_exact_sessions():
    good = history()
    broken = good.copy()
    broken.loc[broken.index[-2:], ['Close', 'Adj Close']] = float('nan')
    def reply(params):
        if params['start'] < '2026-09-14':
            return broken
        stamp = pd.Timestamp(params['start'], tz='Europe/Oslo')
        return good.loc[[stamp]]
    reader, calls, sleeps = fetcher(reply)
    actual = reader.fetch('EQNR.OL')
    assert len(calls) == 3 and len(sleeps) == 3
    assert [c['start'] for c in calls[1:]] == ['2026-09-17', '2026-09-18']
    assert [c['end'] for c in calls[1:]] == ['2026-09-18', '2026-09-19']
    assert actual.Close.tolist() == [51.] * 5
    assert actual.Open.tolist() == [50.] * 5
    assert actual.Volume.tolist() == [1000.] * 5
    assert reader.diagnostics[0]['recovered_sessions'] == ['2026-09-17', '2026-09-18']


def test_missing_entire_day_is_retried_and_missing_history_still_blocks():
    good = history()
    broken = good.drop(good.index[1])
    reader, calls, _ = fetcher(lambda _: broken)
    with pytest.raises(HistoryUnavailable, match='2026-09-15'):
        reader.fetch('A.OL')
    assert calls[-1]['start'] == '2026-09-15'


def test_complete_history_is_paced_and_excludes_provisional_bar():
    good = history()
    good.loc[pd.Timestamp('2026-09-21', tz='Europe/Oslo')] = [900, 999, 899, 950, 950, 9999]
    reader, calls, sleeps = fetcher(lambda _: good, pause=.75)
    actual = reader.fetch('A.OL')
    assert len(calls) == 1 and sleeps == [.75]
    assert actual.index.max().date() == DAY
    assert actual.Close.iloc[-1] == 51


def test_duplicate_dates_cannot_be_hidden_by_session_retry():
    good = history()
    reader, calls, _ = fetcher(lambda _: pd.concat([good, good.tail(1)]))
    with pytest.raises(HistoryUnavailable, match='duplicate_price_dates'):
        reader.fetch('A.OL')
    assert len(calls) == 1


def test_rate_limit_stops_further_tickers_until_next_run():
    def limited(_):
        raise YFRateLimitError()
    reader, calls, _ = fetcher(limited)
    for symbol in ['A.OL', 'B.OL']:
        with pytest.raises(HistoryUnavailable, match='yahoo_rate_limited'):
            reader.fetch(symbol)
    assert len(calls) == 1
    assert reader.rate_limited


def test_network_failures_have_bounded_backoff_and_can_recover():
    attempts = 0
    def reply(_):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError('test timeout')
        return history()
    reader, calls, sleeps = fetcher(reply, pause=.6)
    assert len(reader.fetch('A.OL')) == 5
    assert len(calls) == 3
    assert sleeps == [.6, 2, .6, 4, .6]


@pytest.mark.parametrize('column,value', [('Close', 110), ('Open', 90), ('High', 97),
                                         ('Low', 106), ('Adj Close', float('nan')),
                                         ('Close', float('inf')), ('Volume', -1)])
def test_impossible_or_incomplete_candles_never_produce_adjusted_prices(column, value):
    broken = history()
    broken.loc[broken.index[-1], column] = value
    reader, _, _ = fetcher(lambda _: broken)
    with pytest.raises(HistoryUnavailable, match='2026-09-18'):
        reader.fetch('A.OL')


def test_zero_volume_with_source_prices_is_valid():
    good = history()
    good.Volume = 0
    assert valid_bars(good).all()


def test_widespread_corruption_stops_at_session_retry_budget():
    broken = history()
    broken.Close = float('nan')
    reader, calls, _ = fetcher(lambda _: broken, max_session_retries=2)
    with pytest.raises(HistoryUnavailable, match='retry budget exceeded'):
        reader.fetch('A.OL')
    assert len(calls) == 1


def test_no_history_before_first_listing_is_invented():
    good = history().tail(2)
    reader, calls, _ = fetcher(lambda _: good)
    assert len(reader.fetch('IPO.OL')) == 2
    assert len(calls) == 1
