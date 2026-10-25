import datetime as dt
import pandas as pd
import pytest
from liquidity import assess_liquidity, describe_liquidity, session_window

END = dt.date(2026, 10, 23)

def history():
    return pd.DataFrame({'RawClose': 100.0, 'Volume': 1000.0}, index=pd.to_datetime(session_window(END)))

def test_full_activity_and_order_proxy_not_investment_gate():
    result = assess_liquidity(history(), END, 'NOK')
    assert result['activity_status'] == 'activity_confirmed_vendor'
    assert result['activity_positive_sessions'] == 60
    assert result['turnover_proxy_median20_nok'] == 100000
    assert result['order_100k_to_median20_pct'] == 100
    assert result['order_500k_to_median20_pct'] == 500
    text = describe_liquidity({**result, 'date': END.isoformat()})
    assert '60/60' in text and '500.00%' in text
    assert 'Execution suitability unverified' in text
    assert 'No safe participation cutoff' in text

@pytest.mark.parametrize('kind', ['missing', 'nan', 'negative', 'duplicate'])
def test_bad_session_never_becomes_confirmed_activity(kind):
    frame = history()
    if kind == 'missing': frame = frame.iloc[1:]
    elif kind == 'nan': frame.iloc[0, 1] = float('nan')
    elif kind == 'negative': frame.iloc[0, 1] = -1
    else: frame = pd.concat([frame, frame.iloc[:1]])
    result = assess_liquidity(frame, END, 'NOK')
    assert result['activity_status'] == 'unverified'
    assert result['activity_unknown_sessions'] == 1
    assert result['activity_positive_sessions'] == 59


def test_zero_volume_means_reported_no_trade_even_with_other_unknowns():
    frame = history().iloc[1:]
    frame.iloc[0, 1] = 0
    result = assess_liquidity(frame, END, 'NOK')
    assert result['activity_status'] == 'ineligible_no_trade_reported'
    assert result['activity_zero_sessions'] == 1
    assert 'Ineligible' in describe_liquidity({**result, 'date': END.isoformat()})

@pytest.mark.parametrize('kind', ['missing', 'duplicate', 'negative', 'bad_close'])
def test_capacity_needs_all_exact_twenty_sessions(kind):
    frame = history()
    if kind == 'missing': frame = frame.iloc[:-1]
    elif kind == 'duplicate': frame = pd.concat([frame, frame.iloc[-1:]])
    elif kind == 'negative': frame.iloc[-1, 1] = -1
    else: frame.iloc[-1, 0] = float('nan')
    result = assess_liquidity(frame, END, 'NOK')
    assert result['turnover_proxy_median20_nok'] is None
    assert result['order_500k_to_median20_pct'] is None


def test_calendar_weekends_holidays_and_partial_session_ignored():
    end = dt.date(2026, 4, 7)
    days = session_window(end)
    assert dt.date(2026, 4, 6) not in days  # Easter Monday
    assert dt.date(2026, 4, 3) not in days
    assert len(days) == 60 and days[-1] == end
    frame = history()
    extras = pd.DataFrame({'Close': [1, 1], 'Volume': [0, 0]}, index=pd.to_datetime(['2026-10-24', '2026-10-26']))
    assert assess_liquidity(pd.concat([frame, extras]), END)['activity_positive_sessions'] == 60


def test_unverified_calendar_and_zero_median_fail_closed():
    assert assess_liquidity(history(), dt.date(2027, 1, 4))['activity_status'] == 'unverified'
    frame = history(); frame['Volume'] = 0
    result = assess_liquidity(frame, END, 'NOK')
    assert result['capacity_status'] == 'zero_or_invalid_median_no_capacity_evidence'
    assert result['order_100k_to_median20_pct'] is None


def test_legacy_stale_and_malformed_counts_unverified():
    assert 'unverified' in describe_liquidity({'date': END.isoformat()})
    result = assess_liquidity(history(), END, 'NOK')
    assert 'unverified (missing/current-session' in describe_liquidity({**result, 'date': '2026-10-22'})
    result['activity_positive_sessions'] = 61
    assert 'invalid evidence counts' in describe_liquidity({**result, 'date': END.isoformat()})

@pytest.mark.parametrize('currency', [None, 'USD', '', 'nok'])
def test_currency_must_be_confirmed_nok_before_order_comparison(currency):
    result = assess_liquidity(history(), END, currency)
    assert result['activity_positive_sessions'] == 60
    assert result['capacity_status'] == 'unverified_currency'
    assert result['turnover_proxy_median20_nok'] is None
    assert result['order_100k_to_median20_pct'] is None
    assert 'Order-size comparison unavailable' in describe_liquidity({**result, 'date': END.isoformat()})


def test_currency_metadata_failure_returns_unknown(monkeypatch):
    import screener
    class Ticker:
        @property
        def fast_info(self):
            raise RuntimeError('metadata unavailable')
    monkeypatch.setattr(screener.yf, 'Ticker', lambda ticker: Ticker())
    assert screener.fetch_quote_currency('X.OL') is None


def test_nonfinite_ratio_is_not_emitted():
    frame=history(); frame['RawClose']=1e-320; frame['Volume']=1
    result=assess_liquidity(frame,END,'NOK')
    assert result['order_500k_to_median20_pct'] is None
    assert 'Order-size comparison unavailable' in describe_liquidity({**result,'date':END.isoformat()})


def test_raw_close_is_required_not_adjusted_price_substitution():
    frame=history().rename(columns={'RawClose':'Close'})
    result=assess_liquidity(frame,END,'NOK')
    assert result['activity_positive_sessions']==60
    assert result['turnover_proxy_median20_nok'] is None


def test_download_preserves_original_adjusted_technicals_and_raw_capacity(monkeypatch):
    import screener
    raw=pd.DataFrame({'Open':[100.,110.], 'High':[102.,112.], 'Low':[98.,108.],
                      'Close':[100.,110.], 'Adj Close':[50.,110.], 'Volume':[1000.,2000.]},
                     index=pd.to_datetime(['2026-10-22','2026-10-23']))
    expected=screener.yf.utils.auto_adjust(raw)
    def download(*args,**kwargs):
        assert kwargs['auto_adjust'] is False
        return raw.copy()
    monkeypatch.setattr(screener.yf,'download',download)
    actual=screener.fetch_ohlc_single('X.OL')
    pd.testing.assert_frame_equal(actual.drop(columns='RawClose'),expected)
    assert actual['RawClose'].tolist()==[100.,110.]
    assert actual['Close'].tolist()==[50.,110.]

@pytest.mark.parametrize('ticker_first', [False, True])
def test_download_flatten_preserves_both_multiindex_orders(monkeypatch,ticker_first):
    import screener
    raw=pd.DataFrame({'Open':[100.], 'High':[102.], 'Low':[98.], 'Close':[100.], 'Adj Close':[50.], 'Volume':[1000.]},index=pd.to_datetime(['2026-10-23']))
    nested=raw.copy()
    nested.columns=pd.MultiIndex.from_tuples([( 'X.OL', col) if ticker_first else (col,'X.OL') for col in raw.columns])
    monkeypatch.setattr(screener.yf,'download',lambda *a,**kw:nested.copy())
    actual=screener.fetch_ohlc_single('X.OL')
    pd.testing.assert_frame_equal(actual.drop(columns='RawClose'),screener.yf.utils.auto_adjust(raw))
    assert actual['RawClose'].iloc[0]==100


def test_missing_adjustment_column_is_not_raw_technical_fallback(monkeypatch):
    import screener
    raw=pd.DataFrame({'Open':[100.], 'High':[102.], 'Low':[98.], 'Close':[100.], 'Volume':[1000.]},index=pd.to_datetime(['2026-10-23']))
    monkeypatch.setattr(screener.yf,'download',lambda *a,**kw:raw.copy())
    monkeypatch.setattr(screener.time,'sleep',lambda _:None)
    assert screener.fetch_ohlc_single('X.OL') is None
