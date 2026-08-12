# sync_universe.py
# Henter noterte aksjer på Oslo-markedene fra Euronext og skriver tickers.txt.
# Styres av universe.yaml (markeder, include/exclude, sikkerhetsgrenser).
#
# Miljøvariabler:
#   FORCE_SYNC=1        – skriv tickers.txt selv om sikkerhetsgrensene slår inn
#   UNIVERSE_FILE       – alternativ sti til universe.yaml
#   TICKERS_FILE        – alternativ sti til tickers.txt

import html
import os
import re
import sys
import time

import requests
import yaml

EURONEXT_URL = "https://live.euronext.com/en/product_directory/data/stocks-oslo"
PAGE_SIZE = 300
REQUEST_TIMEOUT = 60
FETCH_TRIES = 3
FETCH_BACKOFF = 5.0

UNIVERSE_FILE = os.getenv("UNIVERSE_FILE", "universe.yaml")
TICKERS_FILE = os.getenv("TICKERS_FILE", "tickers.txt")

DEFAULT_GUARDS = {"min_fetched": 150, "max_removed_pct": 10.0}
SYMBOL_RE = re.compile(r"^[A-Z0-9\-]+$")


class SyncError(RuntimeError):
    """Avbryter kjøringen uten å skrive tickers.txt."""


# ---------- Konfig ----------
def load_universe_config(path: str = UNIVERSE_FILE) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}

    markets = [str(m).strip().upper() for m in cfg.get("markets") or [] if str(m).strip()]
    if not markets:
        raise SyncError(f"{path}: 'markets' er tom – ingen markeder å synkronisere")

    guards = dict(DEFAULT_GUARDS)
    guards.update(cfg.get("guards") or {})

    return {
        "markets": markets,
        "include": [normalize(t) for t in cfg.get("include") or []],
        "exclude": {normalize(t) for t in cfg.get("exclude") or []},
        "guards": guards,
    }


def normalize(ticker: str) -> str:
    t = str(ticker).strip().upper()
    if t.endswith(".OL"):
        t = t[:-3]
    return f"{t}.OL"


# ---------- Euronext ----------
def strip_html(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value or "")).strip()


def post_page(session: requests.Session, params: dict, headers: dict, start: int) -> dict:
    """Én side fra Euronext, med retry mot forbigående nettverks-/serverfeil."""

    last_exc: Exception | None = None
    for attempt in range(1, FETCH_TRIES + 1):
        try:
            resp = session.post(
                EURONEXT_URL,
                params=params,
                headers=headers,
                data={"draw": 1, "iDisplayStart": start, "iDisplayLength": PAGE_SIZE},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            last_exc = e
            if attempt < FETCH_TRIES:
                print(f"Euronext-forsøk {attempt}/{FETCH_TRIES} feilet ({e}) – prøver igjen",
                      file=sys.stderr)
                time.sleep(FETCH_BACKOFF * attempt)

    raise SyncError(f"Euronext svarte ikke etter {FETCH_TRIES} forsøk: {last_exc}")


def fetch_rows(markets: list[str], session: requests.Session | None = None) -> list[dict]:
    """Hent alle instrumenter for de valgte MIC-kodene fra Euronext."""

    session = session or requests.Session()
    params = {"mics": ",".join(markets)}
    headers = {
        "User-Agent": "oslo-screener/1.0 (+https://github.com/keresell-coder/oslo-screener)",
        "X-Requested-With": "XMLHttpRequest",
    }

    rows: list[dict] = []
    start = 0
    total = None

    while total is None or start < total:
        payload = post_page(session, params, headers, start)

        total = int(payload.get("iTotalRecords") or 0)
        page = payload.get("aaData") or []
        if not page:
            break

        for raw in page:
            if len(raw) < 4:
                continue
            rows.append(
                {
                    "name": strip_html(raw[0]),
                    "isin": strip_html(raw[1]),
                    "symbol": strip_html(raw[2]).upper(),
                    "mic": strip_html(raw[3]).upper(),
                }
            )
        start += len(page)

    return rows


def rows_to_tickers(rows: list[dict], cfg: dict) -> tuple[list[str], list[str]]:
    """Returnerer (tickers, skipped) etter markeds-, include- og exclude-filtrering."""

    markets = set(cfg["markets"])
    tickers: set[str] = set()
    skipped: list[str] = []

    for row in rows:
        if row["mic"] not in markets:
            continue
        symbol = row["symbol"]
        if not SYMBOL_RE.match(symbol):
            skipped.append(f"{symbol or '(tomt symbol)'} – uventet symbolformat ({row['name']})")
            continue
        ticker = normalize(symbol)
        if ticker in cfg["exclude"]:
            skipped.append(f"{ticker} – ekskludert i {UNIVERSE_FILE} ({row['name']})")
            continue
        tickers.add(ticker)

    for ticker in cfg["include"]:
        if ticker not in cfg["exclude"]:
            tickers.add(ticker)

    return sorted(tickers), skipped


# ---------- Filhåndtering ----------
def read_current(path: str = TICKERS_FILE) -> list[str]:
    try:
        with open(path) as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def check_guards(fetched_count: int, current: list[str], new: list[str], guards: dict) -> list[str]:
    """Returnerer liste med brudd på sikkerhetsgrensene (tom liste = alt ok)."""

    problems = []

    if not new:
        problems.append("den nye listen er tom")

    if fetched_count < int(guards["min_fetched"]):
        problems.append(
            f"Euronext returnerte bare {fetched_count} instrumenter "
            f"(min_fetched={guards['min_fetched']})"
        )

    removed = sorted(set(current) - set(new))
    if current and removed:
        removed_pct = 100.0 * len(removed) / len(current)
        if removed_pct > float(guards["max_removed_pct"]):
            problems.append(
                f"{len(removed)} av {len(current)} tickers ({removed_pct:.1f} %) ville blitt fjernet "
                f"(max_removed_pct={guards['max_removed_pct']})"
            )

    return problems


def write_tickers(tickers: list[str], path: str = TICKERS_FILE) -> None:
    with open(path, "w") as f:
        f.write("\n".join(tickers) + "\n")


def write_summary(lines: list[str]) -> None:
    print("\n".join(lines))
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write("\n".join(lines) + "\n")


def format_summary(current: list[str], new: list[str], skipped: list[str], forced: bool) -> list[str]:
    added = sorted(set(new) - set(current))
    removed = sorted(set(current) - set(new))

    lines = [
        "### Universe sync",
        "",
        f"- Tickers før: **{len(current)}** → etter: **{len(new)}**",
        f"- Lagt til: **{len(added)}** | fjernet: **{len(removed)}**",
    ]
    if forced:
        lines.append("- ⚠️ FORCE_SYNC=1 – sikkerhetsgrensene ble overstyrt")
    if added:
        lines += ["", "**Nye:** " + ", ".join(added)]
    if removed:
        lines += ["", "**Fjernet:** " + ", ".join(removed)]
    if skipped:
        lines += ["", "**Hoppet over:**"] + [f"- {s}" for s in skipped]
    return lines


# ---------- Hovedløp ----------
def main() -> int:
    forced = os.getenv("FORCE_SYNC") == "1"

    try:
        cfg = load_universe_config(UNIVERSE_FILE)
        rows = fetch_rows(cfg["markets"])
    except (SyncError, requests.RequestException, ValueError, OSError) as e:
        print(f"Universe sync feilet: {e}", file=sys.stderr)
        return 1

    new, skipped = rows_to_tickers(rows, cfg)
    current = read_current(TICKERS_FILE)

    problems = check_guards(len(rows), current, new, cfg["guards"])
    if problems and not forced:
        for p in problems:
            print(f"Universe sync avbrutt: {p}", file=sys.stderr)
        print(f"{TICKERS_FILE} er uendret. Kjør på nytt med FORCE_SYNC=1 hvis endringen er reell.",
              file=sys.stderr)
        return 1

    if new == current:
        write_summary(["### Universe sync", "", f"- Ingen endringer ({len(current)} tickers)."])
        return 0

    write_tickers(new, TICKERS_FILE)
    write_summary(format_summary(current, new, skipped, forced))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
