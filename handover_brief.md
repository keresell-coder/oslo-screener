# Handover Brief — Oslo Børs Screener

**Formål:** Daglig, automatisk screening av OSE-hovedlisten (aksjer + EK-bevis) i Yahoo Finance-format (`.OL`). Output til CSV + GitHub Actions artifacts. Ingen anbefalinger, kun systematiske signaler.

## Arkitektur (kort)
- **Datakilde:** Yahoo Finance via `yfinance`
- **Kode:** `screener.py` (indikatorer, signaler, CSV), `validate_tickers.py` (vask/QA av tickere), `raw_to_tickers.py` (normaliserer råliste → `.OL`)
- **Konfig:** `config.yaml` (terskler, regler, risikoparametre)
- **Lister:** `tickers.txt` (i bruk), `valid_tickers.txt`/`invalid_tickers.csv` (fra validator)
- **Automatisering:** GitHub Actions
  - Daglig kjør: `.github/workflows/daily.yml` (UTC cron, artifacts)
  - Ukentlig validering: `.github/workflows/weekly_validate.yml`
- **Dok:** `README.md`, **denne** `handover_brief.md`

## Hvordan kjøre lokalt
```bash
# i prosjektroten
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python screener.py
