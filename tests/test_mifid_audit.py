"""Synthetic trade events verify audit semantics, not live provider accuracy."""
import datetime as dt
import io
import zipfile

import pandas as pd
import pytest

from scripts.audit_mifid import FIELDS, audit

DAY = dt.date(2026, 9, 18)
UNIVERSE = pd.DataFrame([
    {'ticker': 'A.OL', 'isin': 'NO0000000001', 'mic': 'XOSL'},
    {'ticker': 'B.OL', 'isin': 'NO0000000002', 'mic': 'XOAS'},
    {'ticker': 'C.OL', 'isin': 'NO0000000003', 'mic': 'MERK'},
])


def event(identifier='t1', **changes):
    row = {key: '-' for key in FIELDS}
    row.update(TradingDateTime='2026-09-18T10:00:00Z',
        PublicationDateTime='2026-09-18T10:00:01Z', MifidInstrumentID='NO0000000001',
        MifidPrice='100', MifidQuantity='10', MifidPriceNotation='MONE',
        MifidCurrency='NOK', MmtMarketMechanism='1', MissingPrice='', Venue='XOSL',
        TradeUniqueIdentifier=identifier)
    row.update(changes)
    return row


def payload(*rows):
    data = 'Synthetic fixture\n' + pd.DataFrame(rows, columns=FIELDS).to_csv(index=False)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('Trades_Equities.csv', data)
    return buffer.getvalue()


def test_all_three_markets_and_off_book_prices_do_not_change_order_book_candle():
    report, prices = audit(payload(event(), event('auction', MifidPrice='103',
        MmtMarketMechanism='5', TradingDateTime='2026-09-18T14:25:00Z',
        PublicationDateTime='2026-09-18T14:25:01Z'),
        event('off-book', MifidPrice='999', MmtMarketMechanism='4'),
        event('b', MifidInstrumentID='NO0000000002', Venue='XOAS'),
        event('c', MifidInstrumentID='NO0000000003', Venue='MERK')),
        UNIVERSE, DAY)
    assert report['order_book_observations'] == 3
    assert set(report['venues']) == {'XOSL', 'XOAS', 'MERK'}
    assert report['signal_input_approved'] is False
    assert prices[0]['open'] == 100 and prices[0]['high'] == 103
    assert prices[0]['last_lit_trade'] == 103 and prices[0]['lit_volume'] == 20


def test_cancellation_removes_original_without_double_counting():
    first = event()
    later = event('later', MifidPrice='110', TradingDateTime='2026-09-18T11:00:00Z',
                  PublicationDateTime='2026-09-18T11:00:01Z')
    cancel = {**later, 'MmtModificationIndicator': 'CANC',
              'PublicationDateTime': '2026-09-18T11:01:00Z'}
    report, prices = audit(payload(first, first, later, cancel), UNIVERSE, DAY)
    assert report['cancellations'] == 1
    assert prices[0]['high'] == prices[0]['last_lit_trade'] == 100
    assert prices[0]['lit_volume'] == 10
    assert report['without_trades_in_file'] == ['B.OL', 'C.OL']


@pytest.mark.parametrize('bad', [
    event('revision', MmtModificationIndicator='AMND'),
    event('orphan', MmtModificationIndicator='CANC'),
    event('t1', MifidPrice='101'),
    event('usd', MifidCurrency='USD'),
    event('invalid', MifidPrice='NaN'),
])
def test_unresolved_trade_or_currency_withholds_instrument(bad):
    report, prices = audit(payload(event(), bad), UNIVERSE, DAY)
    assert prices == []
    assert report['withheld'][0]['ticker'] == 'A.OL'


def test_a_stale_file_cannot_pass_as_today():
    with pytest.raises(ValueError, match='expected completed session is absent'):
        audit(payload(event()), UNIVERSE, dt.date(2026, 9, 21))


def test_missing_timestamp_and_ambiguous_mapping_fail():
    with pytest.raises(ValueError, match='missing trade timestamp'):
        audit(payload(event(PublicationDateTime='')), UNIVERSE, DAY)
    with pytest.raises(ValueError, match='ambiguous universe identity'):
        audit(payload(event()), pd.concat([UNIVERSE, UNIVERSE.head(1)]), DAY)
