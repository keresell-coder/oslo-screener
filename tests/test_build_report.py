"""Near-trigger contract: actual RSI/day gates, never mixed-unit ranking."""
import pandas as pd
import pytest
from scripts.build_report import _enrich,_watch_table
from setup_semantics import describe_gates


def row(**changes):
    value=dict(ticker='X.OL',signal='BUY-watch',close=100,previous_close=100,day_direction='flat',data_status='current',rsi14=35,rsi_dir=5,macd_hist=-.001,pct_above_sma50=20,adx14=25,rsi6=30,mfi14=30)
    value.update(changes);return pd.Series(value)


@pytest.mark.parametrize('signal,rsi,direction,needed',[('BUY-watch',35,'flat','up-close'),('BUY-watch',34,'down','up-close'),('SELL-watch',65,'flat','down-close'),('SELL-watch',66,'up','down-close')])
def test_equality_and_flat_describe_missing_day_gate(signal,rsi,direction,needed):
    previous={'flat':100,'up':99,'down':101}[direction]
    value=_enrich(row(signal=signal,rsi14=rsi,day_direction=direction,previous_close=previous))
    assert 'Needs '+needed in value['missing_gates']
    assert 'RSI' in value['missing_gates'] and 'met' in value['missing_gates']
    assert 'confirmations only' in value['missing_gates']
    assert 'closest' not in value and 'closest_delta' not in value


def test_macd_currency_and_sma_percentage_never_rank_missing_gates():
    a=_enrich(row(macd_hist=-.00001,pct_above_sma50=-97))
    b=_enrich(row(macd_hist=-1000,pct_above_sma50=80))
    assert a['missing_gates']==b['missing_gates']
    table=_watch_table(pd.DataFrame([a,b]))
    assert 'not ranked' in table and 'Δ=' not in table


def test_delta_rsi_cannot_replace_missing_day_direction():
    value=describe_gates(row(previous_close=None,day_direction=None,rsi_dir=100))
    assert 'Day direction unavailable' in value


@pytest.mark.parametrize('status',['stale','missing','invalid'])
def test_bad_source_never_describes_usable_trigger(status):
    assert describe_gates(row(data_status=status)).startswith('Withheld:')


def test_wrong_rsi_and_unknown_rsi_are_explicit():
    assert 'Needs RSI <=35' in describe_gates(row(rsi14=36))
    assert 'RSI condition unavailable' in describe_gates(row(rsi14=None))


def test_snapshot_configuration_is_used_not_new_thresholds():
    assert 'RSI <=30 met' in describe_gates(row(rsi14=30),{'rsi14_buy_max':'30'})
    assert 'disabled' in describe_gates(row(),{'require_day_up_for_buy':'false'})
