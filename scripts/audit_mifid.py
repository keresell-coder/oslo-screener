"""Audit the explicitly free MiFID trade file; never feed signals from this audit.

The historical website CSV is a different service with different terms. This
collector uses one normal HTTP download and retains the unaltered source file.
Its order-book prices are provisional: official reference prices, corporate
actions, total-volume rules and historical completeness need separate checks.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from market_health import CALENDAR_VERIFIED_THROUGH, last_ose_trading_day

SOURCE_URL = ('https://marketdata.euronext.com/data-reporting-service/trades-file/'
              'download/EQUITIES/SINCE_PREVIOUS_TRADING_DAY/OSL')
TERMS_URL = 'https://www.euronext.com/sites/default/files/stld/terms_and_conditions_for_delayed_data.pdf'
MARKETS = {'XOSL', 'XOAS', 'MERK'}
FIELDS = ['TradingDateTime', 'PublicationDateTime', 'MifidInstrumentID',
          'MifidPrice', 'MifidQuantity', 'MifidPriceNotation', 'MifidCurrency',
          'MmtMarketMechanism', 'MmtModificationIndicator', 'MmtBenchMarkIndicator',
          'MmtContributionToPrice', 'MmtContingentTransactionIndicator',
          'MissingPrice', 'Venue', 'TradeUniqueIdentifier']


def audit(payload: bytes, instruments: pd.DataFrame, expected: dt.date):
    """Return identity-matched coverage and provisional lit-market observations.

    Only ordinary order-book trades form these prices. Cancellations remove the
    original trade. Amendments and conflicting identifiers withhold the affected
    instrument instead of guessing their replacement semantics.
    """
    if instruments.ticker.duplicated().any() or instruments.duplicated(['isin', 'mic']).any():
        raise ValueError('ambiguous universe identity')
    if not instruments.mic.isin(MARKETS).all():
        raise ValueError('unsupported universe market')
    with zipfile.ZipFile(io.BytesIO(payload)) as source:
        info = source.getinfo('Trades_Equities.csv')
        if info.file_size > 100_000_000:
            raise ValueError('unexpectedly large trade file')
        frame = pd.read_csv(io.BytesIO(source.read(info)), skiprows=1, dtype=str,
                            keep_default_na=False)
    if not set(FIELDS).issubset(frame.columns):
        raise ValueError('unexpected trade schema')
    frame = frame[FIELDS].drop_duplicates().copy()
    for name in ['TradingDateTime', 'PublicationDateTime']:
        frame[name] = pd.to_datetime(frame[name], utc=True, errors='raise')
        if frame[name].isna().any():
            raise ValueError('missing trade timestamp')
    frame['session'] = frame.TradingDateTime.dt.tz_convert('Europe/Oslo').dt.date
    available_sessions = sorted(str(day) for day in frame.session.unique())
    frame = frame[frame.session.eq(expected) & frame.Venue.isin(MARKETS)].copy()
    if frame.empty:
        raise ValueError('expected completed session is absent')
    if (frame.PublicationDateTime < frame.TradingDateTime).any():
        raise ValueError('publication precedes execution')
    frame['price'] = pd.to_numeric(frame.MifidPrice, errors='coerce')
    frame['quantity'] = pd.to_numeric(frame.MifidQuantity, errors='coerce')
    if frame.TradeUniqueIdentifier.eq('').any():
        raise ValueError('missing trade identifier')
    identity = ['MifidInstrumentID', 'Venue', 'TradeUniqueIdentifier']
    observations, absent, withheld = [], [], []
    for instrument in instruments.to_dict('records'):
        trades = frame[frame.MifidInstrumentID.eq(instrument['isin']) &
                       frame.Venue.eq(instrument['mic'])].copy()
        if trades.empty:
            absent.append(instrument['ticker'])
            continue
        unsupported = ~trades.MmtModificationIndicator.isin(['-', 'CANC'])
        originals = trades[trades.MmtModificationIndicator.eq('-')]
        if unsupported.any() or originals.duplicated(identity).any():
            withheld.append({'ticker': instrument['ticker'], 'reason': 'unresolved_trade_revision'})
            continue
        cancelled = set(trades.loc[trades.MmtModificationIndicator.eq('CANC'), 'TradeUniqueIdentifier'])
        if not cancelled.issubset(set(originals.TradeUniqueIdentifier)):
            withheld.append({'ticker': instrument['ticker'], 'reason': 'unmatched_trade_cancellation'})
            continue
        trades = originals[~originals.TradeUniqueIdentifier.isin(cancelled)]
        lit = trades[trades.MmtMarketMechanism.isin(['1', '5'])].copy()
        if lit.empty:
            withheld.append({'ticker': instrument['ticker'], 'reason': 'no_order_book_trade'})
            continue
        valid = (lit.MifidPriceNotation.eq('MONE') & lit.MifidCurrency.eq('NOK') &
                 lit.MissingPrice.eq('') & lit.MmtBenchMarkIndicator.eq('-') &
                 lit.MmtContributionToPrice.isin(['-', 'P']) &
                 lit.MmtContingentTransactionIndicator.eq('-') &
                 np.isfinite(lit.price) & np.isfinite(lit.quantity) &
                 lit.price.gt(0) & lit.quantity.gt(0))
        if not valid.all():
            withheld.append({'ticker': instrument['ticker'], 'reason': 'unsupported_order_book_observation'})
            continue
        lit = lit.sort_values(['TradingDateTime', 'PublicationDateTime'], kind='stable')
        observations.append({**instrument, 'session': expected.isoformat(),
            'open': float(lit.price.iloc[0]), 'high': float(lit.price.max()),
            'low': float(lit.price.min()), 'last_lit_trade': float(lit.price.iloc[-1]),
            'lit_volume': float(lit.quantity.sum()), 'lit_trades': len(lit)})
    manifest = {
        'source': 'Euronext MiFID delayed trade files',
        'terms_url': TERMS_URL, 'sha256': hashlib.sha256(payload).hexdigest(),
        'expected_session': expected.isoformat(), 'signal_input_approved': False,
        'available_sessions': available_sessions,
        'universe_count': len(instruments), 'observed_trades': len(frame),
        'venues': frame.Venue.value_counts().to_dict(),
        'cancellations': int(frame.MmtModificationIndicator.eq('CANC').sum()),
        'order_book_observations': len(observations),
        'without_trades_in_file': absent, 'withheld': withheld,
        'limitations': ['last_lit_trade is not certified as the official closing reference price',
                       'lit_volume is not total exchange volume',
                       'no dividends, split adjustments or historical backfill',
                       'absence does not establish delisting or a confirmed no-trade session'],
    }
    return manifest, observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-zip', type=Path)
    parser.add_argument('--instruments', type=Path, default=Path('instruments.csv'))
    parser.add_argument('--output', type=Path, default=Path('mifid-audit'))
    args = parser.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    expected = last_ose_trading_day(now)
    if expected.year > CALENDAR_VERIFIED_THROUGH:
        raise ValueError('exchange calendar requires annual verification')
    if args.input_zip:
        payload = args.input_zip.read_bytes()
    else:
        response = requests.get(SOURCE_URL, timeout=60)
        response.raise_for_status()
        payload = response.content
    manifest, observations = audit(payload, pd.read_csv(args.instruments, dtype=str), expected)
    manifest['audited_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
    manifest['retrieved_at'] = None if args.input_zip else manifest['audited_at']
    manifest['download_url'] = None if args.input_zip else SOURCE_URL
    manifest['input_file'] = str(args.input_zip) if args.input_zip else None
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'source.zip').write_bytes(payload)
    (args.output / 'audit.json').write_text(json.dumps(manifest, indent=2) + '\n')
    pd.DataFrame(observations).to_csv(args.output / 'provisional-order-book.csv', index=False)
    print(json.dumps({k: manifest[k] for k in ['expected_session', 'universe_count',
        'observed_trades', 'venues', 'cancellations', 'order_book_observations',
        'signal_input_approved']}))


if __name__ == '__main__':
    main()
