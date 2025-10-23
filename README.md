# Oslo Børs Screener (RSI14/RSI6, SMA50, MACD, ADX, MFI)

**Formål:** Automatisk daglig screening av utvalgte OSE-aksjer (Yahoo Finance `.OL`), med BUY/SELL/Watch-signaler og risikomodul.

## Hvordan kjøre lokalt
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python screener.py

## Oppdatere/latest.csv og bygge rapport manuelt

`scripts/build_v231_report.py` kan nå selv forsøke å hente `latest.csv` fra GitHub.

```bash
# få oversikt over tilgjengelige flagg
python scripts/build_v231_report.py --help

# vanlig bruk: last ned (med GitHub-token hvis satt) og bygg dagsrapporten
python scripts/build_v231_report.py --refresh-latest

# spesifiser ekstra kilde dersom du tester andre speil
python scripts/build_v231_report.py --refresh-latest --latest-url https://min-server/latest.csv
```
