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

`scripts/build_v231_report.py` kan nå selv forsøke å hente `latest.csv` fra GitHub.

```bash
# få oversikt over tilgjengelige flagg
python scripts/build_v231_report.py --help

# vanlig bruk: last ned (med GitHub-token hvis satt) og bygg dagsrapporten
python scripts/build_v231_report.py --refresh-latest

# spesifiser ekstra kilde dersom du tester andre speil
python scripts/build_v231_report.py --refresh-latest --latest-url https://min-server/latest.csv
```

## Slik bruker du endringene når «Apply»-knappen ikke virker

Hvis GitHub/IDE-suggestede patches ikke kan brukes direkte, kan du hente inn commitene manuelt:

1. **Oppdater lokal klone**
   ```bash
   git pull
   ```

2. **Hent en pull request som patch (hvis aktuelt)**
   Erstatt `<PR_NR>` med nummeret på pull requesten du vil teste:
   ```bash
   git fetch origin pull/<PR_NR>/head:apply-pr
   git checkout apply-pr
   ```

3. **Bruk patch-fil direkte (alternativ)**
   Hvis du har fått en `.patch`-fil, lagre den lokalt og kjør:
   ```bash
   git apply path/til/fila.patch
   ```

4. **Hent akkurat denne endringen (denne branchen)**
   Dersom du bare vil teste endringene som følger med denne veiledningen, kan du hente branchen direkte fra GitHub og sjekke den ut lokalt:
   ```bash
   git fetch origin work:apply-work
   git checkout apply-work
   ```
   Når du er fornøyd, slå den sammen inn i din egen hovedbranch (for eksempel `main` eller `master`):
   ```bash
   git checkout main
   git merge apply-work
   ```

5. **Verifiser**
   Kjør testene eller skriptene som normalt (for eksempel `pytest` eller `python scripts/build_v231_report.py --help`) for å bekrefte at endringene fungerer.
