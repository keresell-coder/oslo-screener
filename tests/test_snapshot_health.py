import copy
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

import screener
from market_health import SCHEMA, evaluate_snapshot, last_ose_trading_day
from scripts import build_report
from scripts.validate_snapshot import read_csv, validate_snapshot

NOW = dt.datetime.fromisoformat('2026-09-08T18:00:00+02:00')


def row(ticker='A.OL', **overrides):
    value = dict(ticker=ticker, date='2026-09-08', data_status='current', signal='BUY',
                 close=100, rsi14=30, rsi_dir=1, macd_hist=0.1, sma50=105,
                 pct_above_sma50=-4.76, adx14=24, rsi6=25, mfi14=30,
                 stop_loss_pct=3, position_pct=3, primary_count=3, risk='MODERATE', snapshot_id='test')
    value.update(overrides)
    return value


def meta(**overrides):
    value = dict(schema=SCHEMA, snapshot_id='test', generated_at=NOW.isoformat(),
                 expected_session='2026-09-08', universe_count=1, min_coverage_ratio='0.9')
    value.update(overrides)
    return value


@pytest.mark.parametrize('moment,expected', [
    ('2026-09-08T09:15:00+02:00','2026-09-07'),
    ('2026-09-08T16:30:00+02:00','2026-09-07'),
    ('2026-09-08T16:44:59+02:00','2026-09-07'),
    ('2026-09-08T16:45:00+02:00','2026-09-08'),
    ('2026-04-01T13:24:59+02:00','2026-03-31'),
    ('2026-04-01T13:25:00+02:00','2026-04-01'),
    ('2026-12-24T18:00:00+01:00','2026-12-23'),
    ('2026-12-31T18:00:00+01:00','2026-12-30'),
    ('2026-03-30T14:44:59+00:00','2026-03-27'),
    ('2026-10-26T15:45:00+00:00','2026-10-26'),
])
def test_completed_calendar_boundaries(moment, expected):
    assert last_ose_trading_day(dt.datetime.fromisoformat(moment)).isoformat() == expected


@pytest.mark.parametrize('rows,metadata,reason', [
    ([row(date='2026-09-04')], meta(), 'current_coverage_below_minimum'),
    ([row(date='2026-09-09')], meta(), 'current_coverage_below_minimum'),
    ([row(snapshot_id='another')], meta(), 'current_coverage_below_minimum'),
    ([row(close=float('inf'))], meta(), 'current_coverage_below_minimum'),
    ([row()], meta(generated_at=None), 'missing_or_invalid_generated_at'),
    ([row()], meta(generated_at='2026-09-09T18:00:00+02:00'), 'future_generated_at'),
    ([row()], meta(generated_at='2026-09-08T12:00:00+02:00'), 'session_incomplete_at_generation'),
    ([row()], meta(schema=None), 'missing_or_unsupported_schema'),
    ([row()], meta(universe_count=2), 'universe_row_count_or_identity_mismatch'),
    ([row(), row()], meta(universe_count=2), 'universe_row_count_or_identity_mismatch'),
])
def test_failure_injection_never_promotes_newly_generated_bad_data(rows, metadata, reason):
    health = evaluate_snapshot(rows, metadata, NOW)
    assert health['status'] == 'blocked'
    assert not health['actionable'] and not health['eligible_tickers']
    assert reason in health['reasons']


def test_coverage_distinguishes_full_partial_and_blocked():
    rows = [row(f'T{i}.OL') for i in range(10)]
    assert evaluate_snapshot(rows, meta(universe_count=10), NOW)['status'] == 'current'
    rows[-1] = row('T9.OL', date='2026-09-04')
    partial = evaluate_snapshot(rows, meta(universe_count=10), NOW)
    assert partial['status'] == 'degraded' and len(partial['eligible_tickers']) == 9
    rows[-2] = row('T8.OL', data_status='missing', date=None)
    assert evaluate_snapshot(rows, meta(universe_count=10), NOW)['status'] == 'blocked'


def test_snapshot_expires_at_next_completed_session_not_midnight():
    value = evaluate_snapshot([row()], meta(), dt.datetime.fromisoformat('2026-09-09T12:00:00+02:00'))
    assert value['status'] == 'current'
    assert value['valid_until'] == '2026-09-09T16:45:00+02:00'
    value = evaluate_snapshot([row()], meta(), dt.datetime.fromisoformat('2026-09-09T16:45:00+02:00'))
    assert value['status'] == 'blocked'


def test_calendar_requires_annual_primary_source_review():
    health = evaluate_snapshot([row()], meta(), dt.datetime.fromisoformat('2027-01-04T18:00:00+01:00'))
    assert 'exchange_calendar_requires_annual_verification' in health['reasons']
    assert health['status'] == 'blocked'


def publish(tmp_path, monkeypatch, rows):
    monkeypatch.chdir(tmp_path)
    return screener.publish_snapshot(rows, len(rows), NOW, NOW, NOW, 'test')


def test_empty_categories_overwrite_prior_signal_files(tmp_path, monkeypatch):
    publish(tmp_path, monkeypatch, [row()])
    assert len(read_csv('buy.csv')[0]) == 1
    publish(tmp_path, monkeypatch, [row(signal='NEUTRAL')])
    assert read_csv('buy.csv')[0] == []
    assert read_csv('signals_only.csv')[0] == []
    assert validate_snapshot(now=NOW)['status'] == 'current'


def test_blocked_feed_publishes_consistent_empty_actions_and_report(tmp_path, monkeypatch):
    health = publish(tmp_path, monkeypatch, [dict(ticker='A.OL', data_status='missing', note='feed_timeout')])
    assert health['status'] == 'blocked'
    assert read_csv('latest.csv')[0][0]['signal'] == 'WITHHELD'
    monkeypatch.setattr(build_report, 'validate_snapshot', lambda: validate_snapshot(now=NOW))
    assert build_report.main() == 0
    assert 'BLOCKED' in Path('summaries/latest.md').read_text()
    assert validate_snapshot(now=NOW, require_report=True)['status'] == 'blocked'


def test_report_failure_rejects_tampered_bundle(tmp_path, monkeypatch):
    publish(tmp_path, monkeypatch, [row()])
    Path('buy.csv').write_text('stale report')
    monkeypatch.setattr(build_report, 'validate_snapshot', lambda: validate_snapshot(now=NOW))
    assert build_report.main() == 1
    assert not Path('summaries/latest.md').exists()


def test_valid_report_and_categories_share_snapshot(tmp_path, monkeypatch):
    publish(tmp_path, monkeypatch, [row()])
    monkeypatch.setattr(build_report, 'validate_snapshot', lambda: validate_snapshot(now=NOW))
    assert build_report.main() == 0
    assert validate_snapshot(now=NOW, require_report=True)['snapshot_id'] == 'test'
    Path('summaries/latest.md').write_text('old report')
    with pytest.raises(ValueError, match='checksum'):
        validate_snapshot(now=NOW, require_report=True)


def test_run_excludes_provisional_bar_before_calculating_indicators(tmp_path, monkeypatch):
    moment = dt.datetime.fromisoformat('2026-09-09T12:00:00+02:00')
    class Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return moment.astimezone(tz) if tz else moment
    dates = pd.bdate_range(end='2026-09-09', periods=100)
    prices = [100 + i * .1 for i in range(100)]
    frame = pd.DataFrame(dict(Close=prices, High=[x+1 for x in prices],
                              Low=[x-1 for x in prices], Volume=10000), index=dates)
    frame.loc[dates[-1], ['Close','High','Low']] = [999,1000,998]
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(screener, 'datetime', Frozen)
    monkeypatch.setattr(screener, 'load_tickers', lambda: ['A.OL'])
    monkeypatch.setattr(screener, 'fetch_ohlc_single', lambda ticker: frame)
    health = screener.run()
    result = read_csv('latest.csv')[0][0]
    assert result['date'] == '2026-09-08' and result['source_latest_date'] == '2026-09-09'
    assert float(result['close']) == prices[-2]
    assert health['status'] == 'current'
    assert validate_snapshot(now=moment)['status'] == 'current'


def test_workflow_requires_report_and_publishes_blocked_health_before_failing():
    workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/daily.yml').read_text()
    assert 'continue-on-error' not in workflow
    assert '--require-report --allow-blocked' in workflow
    assert "needs.run.outputs.data_status == 'blocked'" in workflow

@pytest.mark.parametrize('missing_close', [False, True])
def test_zero_volume_quotes_are_valid_but_live_missing_close_is_blocked(tmp_path, monkeypatch, missing_close):
    class Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None): return NOW.astimezone(tz) if tz else NOW
    dates = pd.bdate_range(end='2026-09-08', periods=100)
    prices = [100 + i * .1 for i in range(100)]
    frame = pd.DataFrame(dict(Close=prices, High=[x+1 for x in prices],
                              Low=[x-1 for x in prices], Volume=10000), index=dates)
    frame.loc[dates[-1], 'Volume'] = 0
    if missing_close:
        # Reproduce observed Yahoo failure: Sep7 absent, Sep8 adjusted OHLC absent,
        # volume present; previous valid close is Sep4. No price is imputed.
        frame = frame.drop(pd.Timestamp('2026-09-07'))
        frame.loc[dates[-1], ['Close', 'High', 'Low']] = float('nan')
        frame.loc[dates[-1], 'Volume'] = 1580138
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(screener, 'datetime', Frozen)
    monkeypatch.setattr(screener, 'load_tickers', lambda: ['EQNR.OL'])
    monkeypatch.setattr(screener, 'fetch_ohlc_single', lambda ticker: frame)
    health = screener.run()
    result = read_csv('latest.csv')[0][0]
    assert health['status'] == ('blocked' if missing_close else 'current')
    if missing_close:
        assert result['signal'] == 'WITHHELD'
        assert result['date'] == '2026-09-08'
        assert result['last_valid_ohlc_date'] == health['market_data_as_of'] == '2026-09-04'
        assert 'missing_or_invalid_required_session_ohlc' in result['note']
    assert validate_snapshot(now=NOW)['status'] == health['status']
