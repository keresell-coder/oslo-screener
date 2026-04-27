#!/usr/bin/env python3
"""
fetch_oslo_tickers.py
Fetch the full list of equities listed on Oslo Børs (Euronext Oslo).

Strategy 1: Euronext pd_es DataTables API (correct endpoint per R package source)
Strategy 2: Wikipedia list of Oslo Stock Exchange companies (public, no bot blocking)

No API key required.
"""

import argparse
import json
import re
import sys
import time

import requests

BASE_URL = "https://live.euronext.com"
# Correct endpoint per Euronext R package (cran/Euronext EN_Stocks_List.R)
PD_ES_URL = f"{BASE_URL}/en/pd_es/data/stocks"

WIKIPEDIA_URL = (
    "https://en.wikipedia.org/wiki/List_of_companies_listed_on_the_Oslo_Stock_Exchange"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"{BASE_URL}/en/markets/oslo/equities/list",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": BASE_URL,
}

PAGE_SIZE = 100
MAX_RECORDS = 2000

# Column index for ticker symbol in aaData rows (per Euronext R package)
TICKER_COL = 4


def _clean_ticker(raw: str) -> str | None:
    t = re.sub(r"<[^>]+>", "", raw).strip().upper()
    if not t or t in ("-", "NAN", "N/A", ""):
        return None
    # Strip any "OL:" prefix (Wikipedia sometimes uses this format)
    t = re.sub(r"^OL:", "", t)
    if not t.endswith(".OL"):
        t += ".OL"
    return t


def _dedup_sorted(tickers: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return sorted(result)


# ---------------------------------------------------------------------------
# Strategy 1: Euronext pd_es endpoint
# ---------------------------------------------------------------------------

def fetch_via_euronext(mics: str = "XOSL", timeout: int = 30) -> list[str]:
    session = requests.Session()
    session.headers.update(HEADERS)
    session.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

    def _post(start: int, length: int, draw: int) -> dict:
        payload = {
            "draw": str(draw),
            "columns[0][data]": "0",
            "columns[0][name]": "",
            "search[value]": "",
            "search[regex]": "false",
            "args[initialLetter]": "",
            "iDisplayLength": str(length),
            "iDisplayStart": str(start),
            "sSortDir_0": "asc",
            "sSortField": "name",
        }
        r = session.post(PD_ES_URL, params={"mics": mics}, data=payload, timeout=timeout)
        r.raise_for_status()
        return json.loads(r.text)

    probe = _post(start=0, length=1, draw=1)
    total = int(probe.get("iTotalDisplayRecords", probe.get("iTotalRecords", 0)))
    if total <= 0:
        raise ValueError(f"pd_es probe returned total={total}; response keys: {list(probe)}")

    print(f"[euronext] Total records on exchange: {total}", file=sys.stderr)

    all_rows: list[list] = []
    page = 0
    while len(all_rows) < min(total, MAX_RECORDS):
        data = _post(start=page * PAGE_SIZE, length=PAGE_SIZE, draw=page + 2)
        rows = data.get("aaData", [])
        if not rows:
            break
        all_rows.extend(rows)
        page += 1
        if len(rows) < PAGE_SIZE:
            break
        time.sleep(0.25)

    print(f"[euronext] Fetched {len(all_rows)} rows across {page} page(s)", file=sys.stderr)

    tickers = []
    for row in all_rows:
        if row and len(row) > TICKER_COL:
            t = _clean_ticker(str(row[TICKER_COL]))
            if t:
                tickers.append(t)
    return _dedup_sorted(tickers)


# ---------------------------------------------------------------------------
# Strategy 2: Wikipedia (public, no bot blocking, no Cloudflare)
# ---------------------------------------------------------------------------

def fetch_via_wikipedia(timeout: int = 30) -> list[str]:
    import pandas as pd

    r = requests.get(
        WIKIPEDIA_URL,
        timeout=timeout,
        headers={"User-Agent": "oslo-screener/1.0 (ticker-sync; github.com/keresell-coder/oslo-screener)"},
    )
    r.raise_for_status()

    tables = pd.read_html(r.text)

    # Find the table containing a ticker/symbol column
    ticker_keywords = ("ticker", "symbol", "code", "trading")
    for df in tables:
        col_map = {str(c).lower(): c for c in df.columns}
        col_key = next((k for k in ticker_keywords if k in col_map), None)
        if col_key is None:
            # Try partial match
            col_key = next((k for k in col_map if any(kw in k for kw in ticker_keywords)), None)
        if col_key is None:
            continue

        col = col_map[col_key]
        tickers = []
        for raw in df[col].dropna():
            t = _clean_ticker(str(raw))
            if t:
                tickers.append(t)
        if tickers:
            print(f"[wikipedia] Found {len(tickers)} tickers in column '{col}'", file=sys.stderr)
            return _dedup_sorted(tickers)

    raise ValueError("No ticker column found in any table on the Wikipedia page")


# ---------------------------------------------------------------------------
# Main fetch function with fallback chain
# ---------------------------------------------------------------------------

def fetch_oslo_tickers(mics: str = "XOSL", timeout: int = 30) -> list[str]:
    """
    Return sorted TICKER.OL strings for all equities on Oslo Børs.
    Tries Euronext first, falls back to Wikipedia if Euronext is blocked.

    Note: Euronext live.euronext.com uses Cloudflare bot protection.
    GitHub Actions IPs may be blocked — Wikipedia fallback handles this case.
    """
    strategies = [
        ("Euronext pd_es API", lambda: fetch_via_euronext(mics=mics, timeout=timeout)),
        ("Wikipedia",          lambda: fetch_via_wikipedia(timeout=timeout)),
    ]

    last_error: Exception | None = None
    for name, fn in strategies:
        try:
            print(f"[fetch] Trying: {name}", file=sys.stderr)
            tickers = fn()
            if tickers:
                print(f"[fetch] SUCCESS via '{name}': {len(tickers)} tickers", file=sys.stderr)
                return tickers
            print(f"[fetch] '{name}' returned 0 tickers, trying next...", file=sys.stderr)
        except Exception as e:
            print(f"[fetch] '{name}' failed: {type(e).__name__}: {e}", file=sys.stderr)
            last_error = e

    raise RuntimeError(
        f"All strategies failed to fetch Oslo Børs tickers. Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Oslo Børs equity list and write TICKER.OL format."
    )
    parser.add_argument("--output", "-o", default="tickers.txt",
                        help="Output file (default: tickers.txt). Use '-' for stdout.")
    parser.add_argument("--mics", default="XOSL",
                        help="Euronext MIC codes (default: XOSL = Oslo Børs main market).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print to stdout without writing.")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    tickers = fetch_oslo_tickers(mics=args.mics, timeout=args.timeout)

    if args.dry_run or args.output == "-":
        for t in tickers:
            print(t)
    else:
        with open(args.output, "w") as f:
            for t in tickers:
                f.write(t + "\n")
        print(f"Wrote {len(tickers)} tickers to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
