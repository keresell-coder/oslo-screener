import pytest
from screener import classify,load_config
from setup_semantics import LABELS,describe_gates


@pytest.mark.parametrize('rsi,up,down,expected',[(35,True,False,'BUY'),(35,False,False,'BUY-watch'),(34,False,True,'BUY-watch'),(65,False,True,'SELL'),(65,False,False,'SELL-watch'),(66,True,False,'SELL-watch'),(50,True,False,'NEUTRAL')])
def test_original_rule_boundaries_unchanged(rsi,up,down,expected):
    cfg=load_config()
    signal,_=classify(rsi<=cfg['rsi14_buy_max'],rsi>=cfg['rsi14_sell_min'],up,down,100,200,-1,cfg)
    assert signal==expected


def test_labels_do_not_imply_short_or_portfolio_allocation():
    assert 'not short' in LABELS['SELL']
    assert 'review' in LABELS['BUY']
