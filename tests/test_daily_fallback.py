import datetime as dt

import numpy as np
import pandas as pd
import pytest

from euronext_daily import EuronextDailySource
from yahoo_history import HistoryUnavailable, YahooHistoryFetcher


def frames():
    dates = pd.bdate_range(end='2026-09-18', periods=20)
    close = np.arange(100., 120.)
    yahoo = pd.DataFrame({'Open': close - 1, 'High': close + 2, 'Low': close - 2,
                          'Close': close, 'Adj Close': close, 'Volume': 5000.,
                          'Dividends': 0., 'Stock Splits': 0.}, index=dates)
    source = yahoo[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    source.Volume = np.arange(1000., 1020.)
    return yahoo, source


def reader(yahoo, source):
    class Client:
        def history(self, **kwargs):
            return yahoo.copy()
    return YahooHistoryFetcher(dt.date(2026, 9, 18), ticker_factory=lambda _: Client(),
        sleep=lambda _: None, daily_fallback=lambda symbol, start, end: source.copy())


def remove_prices(frame, day):
    frame.loc[day, ['Open', 'High', 'Low', 'Close', 'Adj Close']] = np.nan
    frame.loc[day, 'Volume'] = 0


def test_entire_missing_session_uses_observed_daily_bar_and_uniform_mfi_volume():
    yahoo, source = frames()
    remove_prices(yahoo, '2026-09-17')
    fetcher = reader(yahoo, source)
    result = fetcher.fetch('EQNR.OL')
    assert result.loc['2026-09-17', 'Close'] == 118.
    assert result.loc['2026-09-17', 'Volume'] == 1018.
    assert fetcher.diagnostics[0]['euronext_recovered_sessions'] == ['2026-09-17']
    assert [r['Volume'] for r in result.attrs['mfi_history']] == list(np.arange(1005., 1020.))


def test_dividend_after_missing_day_uses_the_pre_event_adjustment_factor():
    yahoo, source = frames()
    yahoo.loc[yahoo.index[:-1], 'Adj Close'] *= 116 / 118
    yahoo.loc['2026-09-18', 'Dividends'] = 2.
    remove_prices(yahoo, '2026-09-17')
    result = reader(yahoo, source).fetch('EQNR.OL')
    assert result.loc['2026-09-17', 'Close'] == pytest.approx(116.)
    assert result.loc['2026-09-18', 'Close'] == 119.


def test_ex_dividend_day_uses_the_following_post_event_factor():
    yahoo, source = frames()
    yahoo.loc[yahoo.index[:-2], 'Adj Close'] *= .98
    yahoo.loc['2026-09-17', 'Dividends'] = 2.
    remove_prices(yahoo, '2026-09-17')
    result = reader(yahoo, source).fetch('EQNR.OL')
    assert result.loc['2026-09-17', 'Close'] == 118.


@pytest.mark.parametrize('action', ['Dividends', 'Stock Splits'])
def test_unknown_adjustment_across_action_on_missing_final_day_is_withheld(action):
    yahoo, source = frames()
    remove_prices(yahoo, '2026-09-18')
    yahoo.loc['2026-09-18', action] = 2.
    with pytest.raises(HistoryUnavailable, match='2026-09-18'):
        reader(yahoo, source).fetch('EQNR.OL')


def test_different_price_basis_cannot_be_combined():
    yahoo, source = frames()
    remove_prices(yahoo, '2026-09-17')
    source[['Open', 'High', 'Low', 'Close']] *= 2
    with pytest.raises(HistoryUnavailable, match='2026-09-17'):
        reader(yahoo, source).fetch('EQNR.OL')


def test_zero_trade_day_does_not_manufacture_open_high_or_low():
    yahoo, source = frames()
    remove_prices(yahoo, '2026-09-17')
    source.loc['2026-09-17', ['Open', 'High', 'Low', 'Volume']] = 0.
    with pytest.raises(HistoryUnavailable, match='2026-09-17'):
        reader(yahoo, source).fetch('EQNR.OL')


def test_bad_high_can_be_corrected_only_when_close_and_adjustment_reconcile():
    yahoo, source = frames()
    yahoo.loc['2026-09-10', 'High'] = 1.
    result = reader(yahoo, source).fetch('EQNR.OL')
    assert result.loc['2026-09-10', 'High'] == source.loc['2026-09-10', 'High']
    source.loc['2026-09-10', 'Close'] += .5
    with pytest.raises(HistoryUnavailable, match='2026-09-10'):
        reader(yahoo, source).fetch('EQNR.OL')


def test_mfi_is_withheld_if_exchange_volume_window_is_incomplete():
    yahoo, source = frames()
    remove_prices(yahoo, '2026-09-17')
    source.loc['2026-09-09', 'Volume'] = np.nan
    result = reader(yahoo, source).fetch('EQNR.OL')
    assert result.attrs['mixed_price_sources']
    assert 'mfi_history' not in result.attrs


def test_daily_file_requires_exact_instrument_identity_and_unique_dates(tmp_path):
    mapping = tmp_path / 'instruments.csv'
    mapping.write_text('ticker,isin,mic,name\nEQNR.OL,NO0010096985,XOSL,Equinor\n')
    body = ['"Historical Data"\n"From 2026-09-17 to 2026-09-18"\nNO0010096985\n'
            'Date;Open;High;Low;Last;Close;Number of Shares\n'
            '18/09/2026;411.3;420.4;410.2;419;419;12166749\n']
    class Response:
        url = 'https://live.euronext.com/test'
        @property
        def text(self): return body[0]
        def raise_for_status(self): pass
    source = EuronextDailySource(mapping, get=lambda *args, **kwargs: Response())
    result = source('EQNR.OL', dt.date(2026, 9, 17), dt.date(2026, 9, 18))
    assert result.loc['2026-09-18', 'Close'] == 419.
    body[0] = body[0].replace('NO0010096985', 'NO0013461350')
    with pytest.raises(ValueError, match='identity mismatch'):
        source('EQNR.OL', dt.date(2026, 9, 17), dt.date(2026, 9, 18))
    body[0] = body[0].replace('NO0013461350', 'NO0010096985')
    body[0] += body[0].splitlines()[-1] + '\n'
    with pytest.raises(ValueError, match='duplicate daily CSV dates'):
        source('EQNR.OL', dt.date(2026, 9, 17), dt.date(2026, 9, 18))
