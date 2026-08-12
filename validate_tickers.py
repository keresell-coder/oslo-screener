# validate_tickers.py
# Leser tickers.txt, rydder og verifiserer mot Yahoo (yfinance).
# Skriver ut: valid_tickers.txt + invalid_tickers.csv
#
# Miljøvariabler:
#   MIN_HISTORY_DAYS      – minste antall dagsbarer (default: min_history_days fra config.yaml)
#   ALLOW_TICKER_SHRINK=1 – godta at valid-listen krymper mer enn MAX_VALID_DROP_PCT
#   MAX_VALID_DROP_PCT    – terskel for krymping i prosent (default 10)

import os, sys, time
import pandas as pd
import yfinance as yf
import yaml


def load_min_history_days() -> int:
    if os.getenv("MIN_HISTORY_DAYS"):
        return int(os.environ["MIN_HISTORY_DAYS"])
    try:
        with open("config.yaml") as f:
            cfg = yaml.safe_load(f) or {}
        return int(cfg.get("min_history_days", 30))
    except Exception:
        return 30


MIN_DAYS = load_min_history_days()

YF_PAUSE = float(os.getenv("YF_PAUSE", "0.35"))
MAX_VALID_DROP_PCT = float(os.getenv("MAX_VALID_DROP_PCT", "10"))

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


def read_previous_valid(path: str = "valid_tickers.txt") -> list[str]:
    try:
        with open(path) as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def check_shrink(previous: list[str], valids: list[str]) -> str | None:
    """Skiller mellom reelle avnoteringer og en strupet/feilende Yahoo-kjøring."""
    if not previous:
        return None
    dropped = len(set(previous) - set(valids))
    if not dropped:
        return None
    drop_pct = 100.0 * dropped / len(previous)
    if drop_pct > MAX_VALID_DROP_PCT:
        return (
            f"{dropped} av {len(previous)} tidligere gyldige tickers ({drop_pct:.1f} %) feilet nå "
            f"(MAX_VALID_DROP_PCT={MAX_VALID_DROP_PCT})"
        )
    return None


def write_summary(previous: list[str], valids: list[str], invalids: list[dict]) -> None:
    added = sorted(set(valids) - set(previous))
    removed = sorted(set(previous) - set(valids))

    lines = [
        "### Ticker validation",
        "",
        f"- Sjekket mot Yahoo med minst **{MIN_DAYS}** dagsbarer",
        f"- Gyldige: **{len(valids)}** | ugyldige: **{len(invalids)}**",
    ]
    if added:
        lines += ["", "**Nye gyldige:** " + ", ".join(added)]
    if removed:
        lines += ["", "**Falt ut:** " + ", ".join(removed)]
    if invalids:
        lines += ["", "**Ugyldige:**"] + [f"- {row['ticker']}: {row['note']}" for row in invalids]

    print("\n".join(lines))
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write("\n".join(lines) + "\n")


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

    previous = read_previous_valid()

    valids, invalids = [], []
    for t in tickers:
        ok, note = check_ticker(t)
        (valids if ok else invalids).append({"ticker": t, "note": note})

    valid_tickers = [row["ticker"] for row in valids]

    # Ikke la en feilet kjøring tømme eller barbere listen screeneren lever av.
    if not valid_tickers:
        sys.exit("Ingen gyldige tickers – beholder forrige valid_tickers.txt")

    problem = check_shrink(previous, valid_tickers)
    if problem and os.getenv("ALLOW_TICKER_SHRINK") != "1":
        sys.exit(
            f"Validering avbrutt: {problem}. "
            "Filene er uendret. Kjør på nytt med ALLOW_TICKER_SHRINK=1 hvis nedgangen er reell."
        )

    # write results
    with open("valid_tickers.txt", "w") as f:
        for ticker in valid_tickers:
            f.write(ticker + "\n")
    pd.DataFrame(invalids, columns=["ticker", "note"]).to_csv("invalid_tickers.csv", index=False)

    print(f"Checked {len(tickers)} tickers → valid: {len(valids)}, invalid: {len(invalids)}")
    print("Wrote valid_tickers.txt and invalid_tickers.csv")
    write_summary(previous, valid_tickers, invalids)

if __name__ == "__main__":
    main()
