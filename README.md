# Oslo Børs Screener (RSI14/RSI6, SMA50, MACD, ADX, MFI)

**Formål:** Automatisk daglig screening av Oslo Børs, Euronext Expand Oslo og Euronext Growth Oslo (Yahoo Finance `.OL`), med BUY/SELL/Watch-signaler og risikomodul.

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

Alle tre markeder (`XOSL`, `XOAS`, `MERK`) er med. Screeneren leser hele `tickers.txt`, slik at en Yahoo-feil eller kort IPO-historikk ikke skjuler en notert aksje fra rapportens dekningsgrunnlag. `valid_tickers.txt` og `invalid_tickers.csv` er diagnostikk fra den ukentlige kontrollen. `SCREENER_TICKERS_FILE` kan velge en annen liste ved lokal testing; det eldre eksplisitte `VALID_TICKERS_FILE` støttes fortsatt.

```bash
# hent noterte aksjer fra Euronext og oppdater tickers.txt
python sync_universe.py

# verifiser mot Yahoo → valid_tickers.txt + invalid_tickers.csv
python validate_tickers.py
```

Begge skriptene avbryter uten å skrive filer hvis listen krymper unormalt mye (strupet/feilende nedlasting ser ellers ut som en masseavnotering). Overstyr med `FORCE_SYNC=1` henholdsvis `ALLOW_TICKER_SHRINK=1` når endringen er reell. Valideringen bruker samme historikk-krav som screeneren (`min_history_days` i `config.yaml`).

## Drift, datakvalitet og publisering

`Daily Screener` har tre gratis forsøk per handelssesjon: 19:37 og 23:37 UTC mandag–fredag, samt 03:37 UTC tirsdag–lørdag. Første forsøk er 20:37 CET / 21:37 CEST; siste forsøk er 04:37 CET / 05:37 CEST neste morgen. Dette gir Yahoo tid til å ferdigstille dagsdata og margin før børsåpning kl. 09:00 Oslo. Fredagens siste forsøk er lørdag morgen. GitHub kan forsinke eller miste planlagte kjøringer; tidspunktene er mål, ikke en garantert leveringstid.

`yahoo_history.py` henter ni måneders historikk med eksplisitt sluttdato, inkludert manglende observasjoner. Den venter mellom **alle** forespørsler (standard 0,6 sekunder), og prøver nettverksfeil på nytt opptil tre ganger med økende ventetid. Inntil åtte ufullstendige/manglende sesjoner per aksje hentes på nytt én dag av gangen. Dette håndterer feilen der Yahoo gir blank Close i lange forespørsler, men komplett dagsbar i en kort forespørsel. Hele OHLCV-baren og Yahoo Adjusted Close må være gyldig; historiske hull, ugyldige priser og umulige OHLC-forhold blokkerer aksjen. Det lages ingen priser fra intradagdata, gamle sluttkurser eller interpolering. Yahoo-ratebegrensning stanser flere nedlastinger i den kjøringen og overlater neste forsøk til planen.

Yahoo sine justeringsfaktorer brukes først etter at hele vinduet er validert. Historikken lastes på nytt hver kjøring for å ta med senere splitt-/utbyttejusteringer. Nye selskaper må ha nok ekte historikk for indikatorenes oppvarming, også SMA50. Alle indikatorer beregnes **etter** at uavsluttede dagsbarer er fjernet. `fetch_diagnostics.json` lagres som Actions-artifact med forespørselsantall, gjenhentede datoer og gjenværende feil. Yahoo er fortsatt en gratis kilde uten oppetidsgaranti; gyldighetskontrollene gjelder også etter vellykket HTTP-svar.

`Live free-data acceptance` tester samme fullstendige pris- og rapportløp på GitHubs runner ved relevante PR-er. Rapport og diagnostikk kan lastes ned fra Actions, også når dekningen blokkeres. Denne testen skriver ikke til main eller Pages. En manuell `Daily Screener`-kjøring fra en annen branch bygger også kun review-artifacts; publisering er begrenset til main.

Endringer i produksjonskoden på main utløser også en ny dagskjøring, slik at en rettelse publiseres etter merge uten å vente til neste planlagte forsøk. Prisinnhenting har en øvre grense på 90 minutter. Fremdrift og delvis diagnostikk lagres for hver tiende aksje, slik at langsomme/avbrutte kjøringer kan undersøkes.

`health.json` og metadata i hver CSV deler `snapshot_id`, `generated_at`, `expected_session`, `market_data_as_of` og `status`. Hver rad har `data_status`, observasjonsdato og en eventuell årsak til at den er utelatt. Fersk genereringstid gjør aldri gamle observasjoner aktuelle. `last_valid_ohlc_date` skiller siste brukbare prisbar fra en nyere datostemplet rad med manglende OHLC; `market_data_as_of` viser siste brukbare observasjon på tvers av universet.

- `current`: 100% av universet har aktuelle, gyldige observasjoner.
- `degraded`: minst 90%, men under 100%, har aktuelle observasjoner. Bare disse radene kan gi oppsett.
- `blocked`: under minimumsdekning, ugyldig metadata eller uavsluttet/utdatert sesjon. Alle signaler holdes tilbake (`WITHHELD`). `MIN_CURRENT_COVERAGE` kan endre det eksplisitte dekningskravet; standard er 0.9.
- `coverage` inneholder universe_count, received_count, current, stale, missing, invalid, current_ratio, min_current_ratio og actionable_count.
- `reasons`, `excluded`, `observation_dates` og `signal_counts` forklarer dekningen. `artifacts` inneholder SHA-256 for publiserte CSV-er og rapporter.
- `valid_until` er når neste handelssesjon pluss datamargin er ferdig. Konsumenter skal blokkere en bufret status etter dette tidspunktet, selv om siste kjøring var vellykket.

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
