# validate_tickers.py
# Leser tickers.txt, rydder og verifiserer mot Yahoo (yfinance).
# Skriver ut: valid_tickers.txt + invalid_tickers.csv

import os, time
import pandas as pd
import yfinance as yf

MIN_DAYS = int(os.getenv("MIN_HISTORY_DAYS", "1"))

YF_PAUSE = float(os.getenv("YF_PAUSE", "0.35"))

def normalize(t):
    t = t.strip().upper()
    if not t:
        return ""
    if not t.endswith(".OL"):
        t += ".OL"
    return t

def flatten(df: pd.DataFrame) -> pd.DataFrame:
    if hasattr(df, "columns") and isinstance(df.columns, pd.MultiIndex):
        lvl0 = list(df.columns.get_level_values(0))
        lvl1 = list(df.columns.get_level_values(1))
        if "Close" in lvl0 and len(set(lvl1)) == 1:
            df.columns = lvl0
        elif "Close" in lvl1 and len(set(lvl0)) == 1:
            df.columns = lvl1
    return df

def check_ticker(t: str, tries: int = 3) -> tuple[bool, str]:
    last_err = ""
    for attempt in range(1, tries + 1):
        try:
            df = yf.download(t, period="9mo", interval="1d", auto_adjust=True, progress=False, threads=False)
            df = flatten(df)
            if df is not None and not df.empty and len(df) >= MIN_DAYS and set(["Close","High","Low"]).issubset(df.columns):
                return True, "ok"
            last_err = f"insufficient_data_or_columns ({len(df) if df is not None else 0})"
        except Exception as e:
            last_err = f"error: {type(e).__name__}: {e}"
        time.sleep(YF_PAUSE * attempt)
    return False, last_err or "unknown"

def main():
    with open("tickers.txt") as f:
        raw = [line.strip() for line in f if line.strip()]
    normalized = [normalize(t) for t in raw]
    # drop duplicates while preserving order
    seen = set()
    tickers = []
    for t in normalized:
        if t and t not in seen:
            seen.add(t); tickers.append(t)

    valids, invalids = [], []
    for t in tickers:
        ok, note = check_ticker(t)
        (valids if ok else invalids).append({"ticker": t, "note": note})

    # write results
    with open("valid_tickers.txt", "w") as f:
        for row in valids:
            f.write(row["ticker"] + "\n")
    pd.DataFrame(invalids).to_csv("invalid_tickers.csv", index=False)

    print(f"Checked {len(tickers)} tickers → valid: {len(valids)}, invalid: {len(invalids)}")
    print("Wrote valid_tickers.txt and invalid_tickers.csv")

if __name__ == "__main__":
    main()
