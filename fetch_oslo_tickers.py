#!/usr/bin/env python3
"""
fetch_oslo_tickers.py
Fetch the full list of equities listed on Oslo Børs (Euronext Oslo, MIC: XOSL)
and write them as TICKER.OL format suitable for Yahoo Finance.

No API key or authentication required.

Sources tried in order:
1. Euronext pd_feed (POST, DataTables JSON) - primary
2. Euronext pd/data/stocks (GET, DataTables JSON) - fallback
3. Euronext market-data CSV download - fallback

Usage:
    python fetch_oslo_tickers.py                   # writes tickers.txt
    python fetch_oslo_tickers.py --output my.txt   # custom output path
    python fetch_oslo_tickers.py --mics XOSL,MERK  # include Euronext Growth Oslo too
    python fetch_oslo_tickers.py --dry-run          # print to stdout only
"""

import argparse
import json
import re
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://live.euronext.com"

# DataTables server-side POST endpoint (used by the equities list page)
PD_FEED_URL = f"{BASE_URL}/en/pd_feed/"

# Alternative GET endpoint (newer, same JSON schema)
PD_DATA_URL = f"{BASE_URL}/en/pd/data/stocks"

# Direct CSV download endpoint
CSV_DOWNLOAD_URL = f"{BASE_URL}/en/market-data/equities/download"

# Norwegian market MIC codes:
#   XOSL = Oslo Børs main list (~200-230 companies)
#   XOAS = Oslo Axess (legacy; mostly merged into XOSL now)
#   MERK = Euronext Growth Oslo (formerly Merkur Market, ~100 companies)
DEFAULT_MICS = "XOSL"

# Browser-like headers to avoid bot detection
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": f"{BASE_URL}/en/products/equities/list",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": BASE_URL,
}

PAGE_SIZE = 100   # records per request; increase to 500 if you want fewer round-trips
MAX_RECORDS = 2000  # safety cap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_ticker_from_row(row: list) -> str | None:
    """
    Extract the ticker/mnemo symbol from a DataTables aaData row.

    Euronext aaData column layout (pd_feed POST response):
      [0]  Company name  — HTML anchor, e.g. "<a href='/en/product/equities/NO0010096985-XOSL'>Equinor ASA</a>"
      [1]  Mnemo/ticker  — e.g. "EQNR"
      [2]  ISIN          — e.g. "NO0010096985"
      [3]  Market/MIC    — e.g. "XOSL"
      [4]  Currency      — e.g. "NOK"
      [5+] Price fields  — not needed here
    """
    if not row or len(row) < 2:
        return None
    ticker = str(row[1]).strip().upper()
    # Strip any HTML tags (shouldn't be present in col 1, but guard anyway)
    ticker = re.sub(r"<[^>]+>", "", ticker).strip()
    if not ticker or ticker == "-":
        return None
    return ticker


def _rows_to_tickers(rows: list[list]) -> list[str]:
    """Convert aaData rows to sorted, deduplicated TICKER.OL strings."""
    seen: set[str] = set()
    result: list[str] = []
    for row in rows:
        raw = _extract_ticker_from_row(row)
        if raw:
            yf_ticker = f"{raw}.OL"
            if yf_ticker not in seen:
                seen.add(yf_ticker)
                result.append(yf_ticker)
    return sorted(result)


def _parse_datatables_json(text: str) -> list[list]:
    """Parse Euronext DataTables JSON response into aaData rows."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response is not valid JSON: {e}\n\nFirst 500 chars:\n{text[:500]}")

    if "aaData" not in data:
        raise ValueError(
            f"JSON response has no 'aaData' key. Keys present: {list(data.keys())}\n"
            f"First 500 chars:\n{text[:500]}"
        )
    return data["aaData"]


# ---------------------------------------------------------------------------
# Strategy 1: POST to pd_feed (primary, most reliable)
# ---------------------------------------------------------------------------

def fetch_via_pd_feed_post(mics: str, timeout: int = 30) -> list[str]:
    """
    Fetch equity list via POST to the Euronext pd_feed DataTables endpoint.

    This is the endpoint called by the browser when you visit:
    https://live.euronext.com/en/products/equities/list?mics=XOSL

    The response is a DataTables server-side JSON:
    {
        "iTotalRecords": 215,
        "iTotalDisplayRecords": 215,
        "sEcho": "1",
        "aaData": [
            ["<a href='...'>Company Name</a>", "TICKER", "ISIN", "XOSL", "NOK", ...],
            ...
        ]
    }
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    session.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

    def _post(start: int, length: int, echo: int) -> dict:
        payload = {
            "mics": mics,
            "start": str(start),
            "length": str(length),
            "iDisplayStart": str(start),
            "iDisplayLength": str(length),
            "iSortCol_0": "0",
            "sSortDir_0": "asc",
            "sSearch": "",
            "sEcho": str(echo),
        }
        r = session.post(PD_FEED_URL, data=payload, timeout=timeout)
        r.raise_for_status()
        return json.loads(r.text)

    # --- Probe: get total count ---
    probe = _post(start=0, length=1, echo=1)
    total = int(probe.get("iTotalRecords", probe.get("iTotalDisplayRecords", 0)))
    if total <= 0:
        raise ValueError(f"pd_feed probe returned total={total}; response: {probe}")

    print(f"[pd_feed] Total records reported: {total}", file=sys.stderr)

    # --- Fetch all pages ---
    all_rows: list[list] = []
    page = 0
    while len(all_rows) < min(total, MAX_RECORDS):
        start = page * PAGE_SIZE
        data = _post(start=start, length=PAGE_SIZE, echo=page + 2)
        rows = data.get("aaData", [])
        if not rows:
            break
        all_rows.extend(rows)
        page += 1
        if len(rows) < PAGE_SIZE:
            break  # last page
        time.sleep(0.25)  # be polite

    print(f"[pd_feed] Fetched {len(all_rows)} rows across {page} page(s)", file=sys.stderr)
    return _rows_to_tickers(all_rows)


# ---------------------------------------------------------------------------
# Strategy 2: GET pd/data/stocks (newer endpoint, same JSON schema)
# ---------------------------------------------------------------------------

def fetch_via_pd_data_get(mics: str, timeout: int = 30) -> list[str]:
    """
    Fetch equity list via GET from the newer Euronext pd/data/stocks endpoint.

    URL: https://live.euronext.com/en/pd/data/stocks?mics=XOSL&start=0&length=100
    Returns same DataTables JSON format as pd_feed.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    def _get(start: int, length: int) -> dict:
        params = {
            "mics": mics,
            "start": start,
            "length": length,
        }
        r = session.get(PD_DATA_URL, params=params, timeout=timeout)
        r.raise_for_status()
        return json.loads(r.text)

    probe = _get(start=0, length=1)
    total = int(probe.get("iTotalRecords", probe.get("iTotalDisplayRecords", 0)))
    if total <= 0:
        raise ValueError(f"pd/data/stocks probe returned total={total}")

    print(f"[pd_data] Total records: {total}", file=sys.stderr)

    all_rows: list[list] = []
    page = 0
    while len(all_rows) < min(total, MAX_RECORDS):
        start = page * PAGE_SIZE
        data = _get(start=start, length=PAGE_SIZE)
        rows = data.get("aaData", [])
        if not rows:
            break
        all_rows.extend(rows)
        page += 1
        if len(rows) < PAGE_SIZE:
            break
        time.sleep(0.25)

    print(f"[pd_data] Fetched {len(all_rows)} rows across {page} page(s)", file=sys.stderr)
    return _rows_to_tickers(all_rows)


# ---------------------------------------------------------------------------
# Strategy 3: CSV download endpoint
# ---------------------------------------------------------------------------

def fetch_via_csv_download(mics: str, timeout: int = 30) -> list[str]:
    """
    Fetch equity list via the Euronext CSV download endpoint.

    POSTs to the market-data download URL. The response is a raw CSV with headers:
    Name,ISIN,Symbol,Market,Currency,Last,+/-,%Chg,Volume,Turnover
    """
    session = requests.Session()
    session.headers.update({
        **HEADERS,
        "Accept": "text/csv,text/plain,*/*",
        "Content-Type": "application/x-www-form-urlencoded",
    })

    payload = {"mics": mics}
    r = session.post(CSV_DOWNLOAD_URL, data=payload, timeout=timeout)
    r.raise_for_status()

    lines = r.text.splitlines()
    if not lines:
        raise ValueError("CSV download returned empty response")

    # Find header row
    header_idx = 0
    for i, line in enumerate(lines):
        if "ISIN" in line or "Symbol" in line or "Name" in line:
            header_idx = i
            break

    header = [h.strip().strip('"') for h in lines[header_idx].split(";")]
    try:
        symbol_col = header.index("Symbol")
    except ValueError:
        # Try comma-separated
        header = [h.strip().strip('"') for h in lines[header_idx].split(",")]
        symbol_col = header.index("Symbol")

    tickers = []
    seen: set[str] = set()
    sep = ";" if ";" in lines[header_idx] else ","

    for line in lines[header_idx + 1:]:
        if not line.strip():
            continue
        cols = [c.strip().strip('"') for c in line.split(sep)]
        if len(cols) <= symbol_col:
            continue
        ticker = cols[symbol_col].strip().upper()
        if ticker and ticker != "-" and f"{ticker}.OL" not in seen:
            seen.add(f"{ticker}.OL")
            tickers.append(f"{ticker}.OL")

    return sorted(tickers)


# ---------------------------------------------------------------------------
# Main fetch function with fallback chain
# ---------------------------------------------------------------------------

def fetch_oslo_tickers(
    mics: str = DEFAULT_MICS,
    timeout: int = 30,
) -> list[str]:
    """
    Return a sorted list of TICKER.OL strings for all equities listed
    on the specified Euronext Oslo market(s).

    Tries three strategies in order, returning on the first success.

    Args:
        mics: Comma-separated MIC codes.
              "XOSL"       = Oslo Børs main market only (default)
              "XOSL,MERK"  = Oslo Børs + Euronext Growth Oslo
              "XOSL,XOAS,MERK" = all three Oslo markets
        timeout: HTTP request timeout in seconds.

    Returns:
        List of ticker strings like ["AKER.OL", "DNB.OL", "EQNR.OL", ...]

    Raises:
        RuntimeError: if all strategies fail.
    """
    strategies = [
        ("pd_feed POST", fetch_via_pd_feed_post),
        ("pd/data GET",  fetch_via_pd_data_get),
        ("CSV download", fetch_via_csv_download),
    ]

    last_error: Exception | None = None
    for name, fn in strategies:
        try:
            print(f"[fetch] Trying strategy: {name}", file=sys.stderr)
            tickers = fn(mics=mics, timeout=timeout)
            if tickers:
                print(
                    f"[fetch] SUCCESS via '{name}': {len(tickers)} tickers for MIC={mics}",
                    file=sys.stderr,
                )
                return tickers
            print(f"[fetch] '{name}' returned 0 tickers, trying next...", file=sys.stderr)
        except Exception as e:
            print(f"[fetch] '{name}' failed: {e}", file=sys.stderr)
            last_error = e

    raise RuntimeError(
        f"All strategies failed to fetch tickers for MIC={mics}. "
        f"Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch the full list of Oslo Børs equities and write TICKER.OL format."
    )
    parser.add_argument(
        "--output", "-o",
        default="tickers.txt",
        help="Output file path (default: tickers.txt). Use '-' for stdout.",
    )
    parser.add_argument(
        "--mics",
        default=DEFAULT_MICS,
        help=(
            "Comma-separated MIC codes to include. "
            "Default: XOSL (Oslo Børs main market). "
            "Use XOSL,MERK to also include Euronext Growth Oslo."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print tickers to stdout without writing to file.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds (default: 30).",
    )
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
