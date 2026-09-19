"""Read Euronext's public daily CSV by verified ISIN and Oslo market.

This is an ordinary HTTP download, not a browser or a live-trade reconstruction.
The caller must reconcile the price basis before using these unadjusted bars.
"""
import csv
import io
from pathlib import Path
import re

import pandas as pd
import requests


class EuronextDailySource:
    def __init__(self, instruments_file='instruments.csv', get=None):
        self.instruments = {}
        path = Path(instruments_file)
        if path.exists():
            for row in csv.DictReader(path.open(encoding='utf-8')):
                if row['ticker'] in self.instruments:
                    raise ValueError('ambiguous instrument mapping')
                if not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}[0-9]', row['isin']):
                    raise ValueError('invalid instrument ISIN')
                if row['mic'] not in {'XOSL', 'XOAS', 'MERK'}:
                    raise ValueError('unsupported instrument market')
                self.instruments[row['ticker']] = row
        self.get = get or requests.get

    def __call__(self, ticker, start, end):
        if ticker not in self.instruments:
            raise ValueError('no verified exchange identity for ' + ticker)
        instrument = self.instruments[ticker]
        url = 'https://live.euronext.com/en/ajax/AwlHistoricalPrice/getFullDownloadAjax/'
        url += instrument['isin'] + '-' + instrument['mic']
        response = self.get(url, params={
            'format': 'csv', 'decimal_separator': '.', 'date_form': 'd/m/Y',
            'adjusted': 'N', 'startdate': start.isoformat(), 'enddate': end.isoformat(),
        }, timeout=20)
        response.raise_for_status()
        lines = response.text.lstrip('\ufeff').splitlines()
        if len(lines) < 4 or lines[2].strip('"') != instrument['isin']:
            raise ValueError('daily CSV instrument identity mismatch')
        frame = pd.read_csv(io.StringIO('\n'.join(lines[3:])), sep=';')
        frame.index = pd.to_datetime(frame['Date'], format='%d/%m/%Y', errors='raise')
        if frame.index.has_duplicates:
            raise ValueError('duplicate daily CSV dates')
        frame = frame.rename(columns={'Number of Shares': 'Volume'})
        frame = frame[['Open', 'High', 'Low', 'Close', 'Volume']].apply(pd.to_numeric, errors='raise')
        frame = frame.loc[(frame.index.date >= start) & (frame.index.date <= end)].sort_index()
        frame.attrs['source_url'] = response.url
        frame.attrs['isin'] = instrument['isin']
        frame.attrs['mic'] = instrument['mic']
        return frame
