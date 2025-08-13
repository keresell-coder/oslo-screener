# Oslo Børs Screener (RSI14/RSI6, SMA50, MACD, ADX, MFI)

**Formål:** Automatisk daglig screening av utvalgte OSE-aksjer (Yahoo Finance `.OL`), med BUY/SELL/Watch-signaler og risikomodul.

## Hvordan kjøre lokalt
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python screener.py
