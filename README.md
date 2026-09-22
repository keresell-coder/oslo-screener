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

## Drift, datakvalitet og publisering

`Daily Screener` kjører hverdager 06:15 og 16:15 UTC. Morgenkjøringen bruker forrige avsluttede handelssesjon; siste kjøring følger Oslo-slutt i både CET og CEST. Alle indikatorer beregnes **etter** at uavsluttede dagsbarer er fjernet. Minstekravet til historikk dekker alle indikatorenes oppvarming, også SMA50.

`health.json` og metadata i hver CSV deler `snapshot_id`, `generated_at`, `expected_session`, `market_data_as_of` og `status`. Hver rad har `data_status`, observasjonsdato og en eventuell årsak til at den er utelatt. Fersk genereringstid gjør aldri gamle observasjoner aktuelle. `last_valid_ohlc_date` skiller siste brukbare prisbar fra en nyere datostemplet rad med manglende OHLC; `market_data_as_of` viser siste brukbare observasjon på tvers av universet.

- `current`: 100% av universet har aktuelle, gyldige observasjoner.
- `degraded`: universet er ufullstendig, men minst én aksje består datakontrollen i den midlertidige `per_stock`-modusen. Bare gyldige, aktuelle rader kan gi oppsett. I `minimum`-modus kreves minst `MIN_CURRENT_COVERAGE` (standard 90%).
- `blocked`: ingen gyldige, aktuelle aksjer, ugyldig metadata eller uavsluttet/utdatert sesjon. I `minimum`-modus blokkeres også dekning under prosentkravet. Alle signaler holdes tilbake (`WITHHELD`).
- `coverage` inneholder universe_count, received_count, current, stale, missing, invalid, current_ratio, min_current_ratio og actionable_count.
- `reasons`, `excluded`, `observation_dates` og `signal_counts` forklarer dekningen. `artifacts` inneholder SHA-256 for publiserte CSV-er og rapporter.
- `valid_until` er når neste handelssesjon pluss datamargin er ferdig. Konsumenter skal blokkere en bufret status etter dette tidspunktet, selv om siste kjøring var vellykket.

**Midlertidig dekningspolicy (22. september 2026):** `coverage_policy: per_stock` i `config.yaml` suspenderer 90%-kravet for samlet dekning etter eiers ønske. Ingen ugyldige kurser fylles inn, og kontroller per aksje beholdes. Manglende/ugyldige aksjer vises med årsak i rapporten, på helsesiden og i `health.json`; de gir ikke signaler. Ufullstendige rapporter er merket `degraded`, også ved svært lav dekning. Det finnes ikke et nytt prosentgulv. Null brukbare aksjer gir fortsatt `blocked`.

For å avslutte unntaket, sett `coverage_policy: minimum`; da brukes igjen `MIN_CURRENT_COVERAGE` (standard 0.9). Manglende konfigurasjon og eldre snapshot uten policyfelt bruker `minimum`. Hvert nytt snapshot lagrer policyen i CSV-metadata og helsemanifestet. I den eksisterende ratio-kontrakten representeres kravet om én brukbar aksje som `1 / universe_count`, slik at eldre konsumenter kan lese delvise rapporter uten å godta tomme datasett.

Dette endrer bare samlet dekningspolicy. Utvidet univers og strengere historikkontroll i PR #16, og publiseringsvern i PR #17, er egne endringer. Endringen innfører ikke en ny datakilde eller godkjenner de ekskluderte observasjonene.

Alle kategori-CSV-er overskrives også når de er tomme. Rapport, hoved-CSV og kategori-CSV-er valideres som ett snapshot; rapportfeil stanser publisering. En gyldig **blocked**-rapport publiseres med tomme handlingslister og synlig helse, før workflowen markeres feilet. Status er tilgjengelig på https://keresell-coder.github.io/oslo-screener/health.json sammen med de tilhørende filene.

`scripts/prepare_publication.py` lager én helseside og `.nojekyll` i repo-roten, legger dem i checksum-manifestet og kopierer nøyaktig samme publiseringspakke til `site/`. Både den eldre branch-baserte Pages-byggingen og workflowens Pages-artifact får dermed samme `index.html`, helse, rapport og alle deklarerte CSV-er. Allerede Git-sporede `report_*.csv` og `summaries/*.md` kopieres også fra Git-indeksen, slik at eksisterende arkivlenker virker i begge publiseringsveier uten å publisere uvedkommende lokale endringer. `--stage` validerer begge kopiene og legger bare manifestets eksakte filnavn i Git, også tidsstemplet CSV som ellers er ignorert. Tidligere arkiver endres ikke. Helsesiden starter uverifisert, kontrollerer levende manifest og snapshot-ID, og sperrer ved hentefeil eller utløpt gyldighet.

Pull requests og kodeendringer på main kjører regresjonstester. Direkte avhengigheter er låst til versjonene brukt ved kontrollen:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python screener.py
python scripts/build_report.py
python scripts/prepare_publication.py
python scripts/validate_snapshot.py --require-report --allow-blocked
python scripts/prepare_publication.py --verify
```

`--allow-blocked` tillater validering av en trygg sperret publisering; det endrer aldri datastatus. Uten flagget gir blocked returkode ulik null.

Kalenderen er kontrollert mot Euronexts 2026-kalender og gjeldende kontanthandelstider: slutt på trading-at-last 16:30 Oslo, 13:10 på onsdag før påske. En konservativ **15 minutters datamargin** kommer i tillegg. 24. og 31. desember er stengt. Primærkildene står i `market_health.py`. **Neste års offisielle kalender må kontrolleres før 2027; ukjente fremtidige år blokkerer oppsett.**

BUY/SELL-reglene er fortsatt RSI-terskel og dagsretning. SMA50/MACD-støtte endrer primærantall, ikke selve merkelappen. ADX-bånd og prosentvise stopp/posisjoner er heuristikker, og nyhets-/fundamentaldekning inngår ikke. Dette er tekniske forskningskandidater, ikke en empirisk validert handelsstrategi.
