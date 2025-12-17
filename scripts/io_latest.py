"""Robust helpers for reading latest.csv (with metadata comment lines)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests


def _read_text(source: str | Path, timeout: int = 30) -> str:
    src = str(source)
    if src.startswith(("http://", "https://")):
        resp = requests.get(src, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    return Path(src).read_text(encoding="utf-8")


def _strip_bom_and_rogue_quote(text: str) -> str:
    # Drop BOM if present and handle a stray leading quote before a comment line.
    cleaned = text.lstrip("\ufeff")
    if cleaned.startswith('"#'):
        cleaned = cleaned[1:]
    return cleaned


def load_latest_df(source: str | Path) -> pd.DataFrame:
    """
    Load latest.csv from a file path or URL, tolerating metadata comment lines.
    Raises if the 'ticker' column is missing.
    """
    text = _strip_bom_and_rogue_quote(_read_text(source))
    df = pd.read_csv(io.StringIO(text), comment="#")
    df.columns = [c.strip() for c in df.columns]
    if "ticker" not in df.columns:
        raise ValueError(f"latest.csv mangler 'ticker'-kolonne. Kolonner: {df.columns.tolist()}")
    return df


def load_latest_tickers(source: str | Path) -> list[str]:
    """Return unique tickers (order preserved) from latest.csv."""
    df = load_latest_df(source)
    seen: set[str] = set()
    tickers: list[str] = []
    for t in df["ticker"].astype(str):
        if t not in seen:
            seen.add(t)
            tickers.append(t)
    return tickers


def _preview(items: Iterable[str], n: int = 5) -> str:
    out = []
    for idx, itm in enumerate(items):
        if idx >= n:
            break
        out.append(itm)
    return "[" + ", ".join(out) + ("" if len(out) < n else ", ...") + "]"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sanity-check loader for latest.csv")
    parser.add_argument("source", nargs="?", default="latest.csv", help="Path or URL to latest.csv")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for URL fetch (seconds)")
    args = parser.parse_args()

    df = load_latest_df(args.source)
    tickers = load_latest_tickers(args.source)
    print(f"Loaded {len(df)} rows with columns: {df.columns.tolist()}")
    print(f"Tickers ({len(tickers)}): {_preview(tickers, 5)}")
