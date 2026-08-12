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

## Tickerunivers

`universe.yaml` styrer hvilke Oslo-noterte aksjer som følges: hvilke markeder (MIC-koder) som hentes automatisk, pluss `include`/`exclude` for manuelle unntak.

```bash
# hent noterte aksjer fra Euronext og oppdater tickers.txt
python sync_universe.py

# verifiser mot Yahoo → valid_tickers.txt + invalid_tickers.csv
python validate_tickers.py
```

Begge skriptene avbryter uten å skrive filer hvis listen krymper unormalt mye (strupet/feilende nedlasting ser ellers ut som en masseavnotering). Overstyr med `FORCE_SYNC=1` henholdsvis `ALLOW_TICKER_SHRINK=1` når endringen er reell. Valideringen bruker samme historikk-krav som screeneren (`min_history_days` i `config.yaml`).

## Drift og publisering

- `Daily Screener` kjører hverdager på `main`, bygger `latest.csv`, verifiserer metadata/kolonner/rader, bygger dagsrapport, committer endringer, publiserer `latest.csv` til GitHub Pages og forsøker å trigge dashboard-refresh dersom `DASHBOARD_WORKFLOW_TOKEN` er satt.
- `Weekly Universe Sync and Ticker Validation` kjører søndager 05:20 UTC på `main`: synkroniserer `tickers.txt` mot Euronext, validerer mot Yahoo, og committer `tickers.txt` / `valid_tickers.txt` / `invalid_tickers.csv`. Nye og fjernede tickere listes i jobbsammendraget. Kan også kjøres manuelt med `workflow_dispatch` (avkryssing for å overstyre sikkerhetsgrensene).
- Begge workflows bruker concurrency slik at planlagte jobber ikke skriver over hverandre.
- `latest.csv` har metadata i kommentarfeltet øverst, inkludert `data_fetch_started`, `data_fetch_completed` og `generated_at`. Nedstrøms apper skal bruke disse feltene for friskhetskontroll.
- Dashboardet (`keresell-coder/oslo-screener-dashboard`) har egen planlagt refresh etter screener-jobben og en ekstra backup-run senere på dagen.
