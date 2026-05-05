# Oslo Børs Screener (RSI14/RSI6, SMA50, MACD, ADX, MFI)

**Formål:** Automatisk daglig screening av utvalgte OSE-aksjer (Yahoo Finance `.OL`), med BUY/SELL/Watch-signaler og risikomodul.

## Hvordan kjøre lokalt
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python screener.py
```

## Oppdatere/latest.csv og bygge rapport manuelt

`scripts/build_report.py` bygger dagsrapport fra lokal `latest.csv`.

```bash
# kjør screeneren først, slik at latest.csv finnes lokalt
python screener.py

# bygg dagsrapport i summaries/
python scripts/build_report.py
```

## Drift og publisering

- `Daily Screener` kjører hverdager på `main`, bygger `latest.csv`, verifiserer metadata/kolonner/rader, bygger dagsrapport, committer endringer, publiserer `latest.csv` til GitHub Pages og forsøker å trigge dashboard-refresh dersom `DASHBOARD_WORKFLOW_TOKEN` er satt.
- `Weekly Ticker Validation` kjører mandager på `main` og oppdaterer `valid_tickers.txt` / `invalid_tickers.csv`.
- Begge workflows bruker concurrency slik at planlagte jobber ikke skriver over hverandre.
- `latest.csv` har metadata i kommentarfeltet øverst, inkludert `data_fetch_started`, `data_fetch_completed` og `generated_at`. Nedstrøms apper skal bruke disse feltene for friskhetskontroll.
- Dashboardet (`keresell-coder/oslo-screener-dashboard`) har egen planlagt refresh etter screener-jobben og en ekstra backup-run senere på dagen.
