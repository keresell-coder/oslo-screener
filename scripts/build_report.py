"""Build daily technical report from latest.csv → summaries/daily_YYYY-MM-DD.md

Reads the signal column that screener.py already computed — no re-classification,
no extra Yahoo Finance calls per ticker.  One random spot-check call is made to
verify price data freshness.
"""

from __future__ import annotations

import random
import sys
import pathlib as pl
import datetime as dt

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = pl.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.trading_calendar import last_ose_trading_day

OUT_DIR = pl.Path("summaries")


# ---------- Data loading ----------

def load_csv(path: pl.Path) -> pd.DataFrame:
    df = pd.read_csv(path, comment="#")
    df.columns = [c.strip().lower() for c in df.columns]
    if "ticker" not in df.columns:
        raise ValueError(f"'ticker' column missing in {path}")
    return df


# ---------- Price spot-check ----------

def _spot_check(df: pd.DataFrame, csv_date: dt.date) -> str:
    """Fetch one ticker from Yahoo and compare its close to the CSV value.

    Tries up to 3 randomly-selected candidates so that a single unavailable
    ticker doesn't silently fail the whole freshness check.
    """
    cands = df.loc[df["signal"].isin(["BUY", "SELL"]), "ticker"].dropna().unique().tolist()
    if not cands:
        cands = df["ticker"].dropna().unique().tolist()
    if not cands:
        return "Pris-sjekk: ingen data"

    rng = random.Random(csv_date.toordinal())
    sample = cands.copy()
    rng.shuffle(sample)
    sample = sample[:3]

    start = (csv_date - dt.timedelta(days=5)).isoformat()
    end = (csv_date + dt.timedelta(days=1)).isoformat()

    for t in sample:
        try:
            hist = yf.download(t, start=start, end=end, interval="1d",
                               auto_adjust=True, progress=False)
            if hist.empty:
                continue
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            idx_dates = [x.date() for x in hist.index.to_pydatetime()]
            days = [d for d in idx_dates if d <= csv_date]
            if not days:
                continue
            d0 = max(days)
            yahoo_close = float(hist["Close"].iloc[idx_dates.index(d0)])
            csv_row = df.loc[df["ticker"] == t]
            if csv_row.empty:
                continue
            csv_close = float(csv_row["close"].iloc[0])
            if csv_close > 0 and yahoo_close > 0:
                dev = abs(csv_close - yahoo_close) / max(csv_close, yahoo_close) * 100.0
                if dev > 0.5:
                    print(f"ADVARSEL – prisavvik {dev:.2f}% >0,5% for {t} "
                          f"(CSV={csv_close:.3f} vs Yahoo={yahoo_close:.3f})")
                status = "OK" if dev <= 0.5 else "⚠️ avvik høy"
                return f"Pris-sjekk: {t} CSV={csv_close:.3f} vs Yahoo={yahoo_close:.3f} – avvik {dev:.2f}% ({status})"
        except Exception:
            continue

    return f"Pris-sjekk: {sample[0] if sample else '?'} – Yahoo data utilgjengelig"


# ---------- Icon helpers ----------

def _icon_macd(macd: float, bias: str) -> str:
    if pd.isna(macd) or -0.05 <= macd <= 0.05:
        return "◻️"
    if bias == "BUY":  return "✅" if macd > 0 else "❌"
    if bias == "SELL": return "✅" if macd < 0 else "❌"
    return "◻️"


def _icon_sma(pct: float, bias: str) -> str:
    if pd.isna(pct):
        return "◻️"
    if bias == "BUY":
        return "✅" if pct >= 0.2 else ("❌" if pct <= -0.2 else "◻️")
    if bias == "SELL":
        return "✅" if pct <= -0.2 else ("❌" if pct >= 0.2 else "◻️")
    return "◻️"


def _adx_icon(v: float) -> str:
    if pd.isna(v): return "⚪"
    return "🟢" if v >= 25 else ("⚪" if v >= 20 else "⚠️")


def _mfi_icon(v: float, bias: str) -> str:
    if pd.isna(v): return "⚪"
    if bias == "BUY":  return "🟢" if v > 50 else ("⚪" if 40 <= v <= 60 else "🔴")
    if bias == "SELL": return "🟢" if v < 50 else ("⚪" if 40 <= v <= 60 else "🔴")
    return "⚪"


def _rsi6_icon(v: float, bias: str) -> str:
    if pd.isna(v): return "⚪"
    if bias == "BUY":
        if v < 10:  return "🟢"
        if v <= 20: return "⚠️"
        if v > 90:  return "🔴"
    if bias == "SELL":
        if v > 90:  return "🟢"
        if v >= 80: return "⚠️"
        if v < 10:  return "🔴"
    return "⚪"


def _fmt(v: float, nd: int = 2) -> str:
    return "—" if pd.isna(v) else f"{v:.{nd}f}"


def _safe_float(val) -> float:
    try:
        f = float(val)
        return f if not np.isnan(f) else np.nan
    except (TypeError, ValueError):
        return np.nan


# ---------- Row enrichment ----------

def _enrich(r: pd.Series) -> dict:
    signal = str(r.get("signal", "NEUTRAL"))
    bucket = signal if signal in ("BUY", "SELL", "BUY-watch", "SELL-watch") else "NEUTRAL"
    bias = "BUY" if "BUY" in bucket else ("SELL" if "SELL" in bucket else "NEUTRAL")
    active = bucket in ("BUY", "SELL")

    r14  = _safe_float(r.get("rsi14"))
    r6   = _safe_float(r.get("rsi6"))
    mfi  = _safe_float(r.get("mfi14"))
    macd = _safe_float(r.get("macd_hist"))
    pct  = _safe_float(r.get("pct_above_sma50"))
    adx  = _safe_float(r.get("adx14"))
    rdir = _safe_float(r.get("rsi_dir"))
    close = _safe_float(r.get("close"))

    macd_ic = _icon_macd(macd, bias)
    sma_ic  = _icon_sma(pct, bias)
    adx_ic  = _adx_icon(adx)
    mfi_ic  = _mfi_icon(mfi, bias if active else "NEUTRAL")
    rsi6_ic = _rsi6_icon(r6, bias if active else "NEUTRAL")

    rank = (
        (1 if macd_ic == "✅" else 0) +
        (1 if sma_ic  == "✅" else 0) +
        (1 if not np.isnan(adx) and adx >= 25 else 0)
    )

    closest = "—"
    closest_delta = np.nan
    if bucket.endswith("watch"):
        opts: list[tuple[str, float]] = []
        if not np.isnan(r14):
            opts.append(("RSI→35", abs(35 - r14)) if r14 <= 35 else ("RSI→65", abs(r14 - 65)))
        if not np.isnan(macd):
            opts.append(("MACD→0", abs(macd)))
        if not np.isnan(pct):
            # Directional distance: how far pct must move to cross the ±0.2% SMA support threshold.
            # BUY needs pct ≥ +0.2; SELL needs pct ≤ −0.2.
            if bias == "BUY":
                opts.append(("SMA50", max(0.0, 0.2 - pct)))
            elif bias == "SELL":
                opts.append(("SMA50", max(0.0, pct + 0.2)))
        if opts:
            lab, dv = sorted(opts, key=lambda x: x[1])[0]
            closest = f"{lab} (Δ={dv:.2f})"
            closest_delta = dv

    return dict(
        bucket=bucket, rank=rank,
        ticker=str(r.get("ticker", "")), close=close,
        rsi14=r14, rdir=rdir, macd=macd, pct=pct,
        adx=adx, rsi6=r6, mfi=mfi,
        macd_ic=macd_ic, sma_ic=sma_ic, adx_ic=adx_ic,
        mfi_ic=mfi_ic, rsi6_ic=rsi6_ic, closest=closest, closest_delta=closest_delta,
    )


# ---------- Table builders ----------

def _main_table(sub: pd.DataFrame) -> str:
    if sub.empty:
        return "_Ingen i dag._"
    lines = [
        "| Rk | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |",
        "|---:|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|",
    ]
    for _, r in sub.head(40).iterrows():
        delta   = "—" if np.isnan(r["rdir"]) else f"{r['rdir']:+.2f}"
        sec     = f"RSI6 {_fmt(r['rsi6'],0)} {r['rsi6_ic']} · MFI {_fmt(r['mfi'],0)} {r['mfi_ic']}"
        adx_cel = f"{_fmt(r['adx'],0)} {r['adx_ic']}"
        lines.append(
            f"| {int(r['rank'])} | {r['ticker']} | {_fmt(r['close'])} | {_fmt(r['rsi14'])} | "
            f"{delta} | {_fmt(r['macd'])} {r['macd_ic']} | {_fmt(r['pct'])} {r['sma_ic']} | "
            f"{adx_cel} | {sec} |"
        )
    return "\n".join(lines)


def _watch_table(sub: pd.DataFrame) -> str:
    if sub.empty:
        return "_Ingen i dag._"
    lines = [
        "| Closest | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |",
        "|:-------|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|",
    ]
    for _, r in sub.head(40).iterrows():
        delta   = "—" if np.isnan(r["rdir"]) else f"{r['rdir']:+.2f}"
        sec     = f"RSI6 {_fmt(r['rsi6'],0)} {r['rsi6_ic']} · MFI {_fmt(r['mfi'],0)} {r['mfi_ic']}"
        adx_cel = f"{_fmt(r['adx'],0)} {r['adx_ic']}"
        lines.append(
            f"| {r['closest']} | {r['ticker']} | {_fmt(r['close'])} | {_fmt(r['rsi14'])} | "
            f"{delta} | {_fmt(r['macd'])} {r['macd_ic']} | {_fmt(r['pct'])} {r['sma_ic']} | "
            f"{adx_cel} | {sec} |"
        )
    return "\n".join(lines)


def _reason_top(sub: pd.DataFrame, side: str) -> str:
    if sub.empty:
        return f"_Ingen {side} i dag._"
    r = sub.iloc[0]
    gate = "RSI≤35 & opp-dag" if side == "BUY" else "RSI≥65 & ned-dag"
    parts = [f"{r['ticker']} kvalifiserte via gatekeeper ({gate})."]
    if r["macd_ic"] == "✅": parts.append("MACD støtter (✅).")
    if r["sma_ic"]  == "✅": parts.append("SMA50-støtte (✅).")
    if not np.isnan(r["adx"]) and r["adx"] >= 25: parts.append("ADX≥25 (🟢).")
    return " ".join(parts)


# ---------- Main ----------

def main() -> int:
    csv_path = pl.Path("latest.csv")
    if not csv_path.exists():
        print("STOPPET – latest.csv mangler")
        return 1

    try:
        df = load_csv(csv_path)
    except Exception as e:
        print(f"STOPPET – kunne ikke lese latest.csv: {e}")
        return 1

    for col in ("date", "signal"):
        if col not in df.columns:
            print(f"STOPPET – '{col}'-kolonne mangler")
            return 1

    csv_dates = pd.to_datetime(df["date"], errors="coerce").dropna().dt.date
    if csv_dates.empty:
        print("STOPPET – ingen gyldige datoer")
        return 1
    csv_last = csv_dates.max()

    last_trading = last_ose_trading_day()
    if csv_last < last_trading:
        print(f"STOPPET – data er utdatert (CSV={csv_last}, forventet>={last_trading})")
        return 1

    # Enrich signal rows with display icons and ranking
    signal_rows = df[df["signal"].isin(["BUY", "SELL", "BUY-watch", "SELL-watch"])]
    enriched = pd.DataFrame([_enrich(r) for _, r in signal_rows.iterrows()])

    def bucket(name: str) -> pd.DataFrame:
        if enriched.empty:
            return pd.DataFrame()
        sub = enriched[enriched["bucket"] == name].copy()
        if name in ("BUY", "SELL") and not sub.empty:
            sub = sub.sort_values(["rank", "adx", "macd", "pct"],
                                  ascending=[False, False, False, False])
        elif name in ("BUY-watch", "SELL-watch") and not sub.empty:
            sub = sub.sort_values("closest_delta", ascending=True, na_position="last")
        return sub

    BUY       = bucket("BUY")
    SELL      = bucket("SELL")
    BUY_watch = bucket("BUY-watch")
    SELL_watch = bucket("SELL-watch")

    price_check = _spot_check(df, csv_last)

    OUT_DIR.mkdir(exist_ok=True)
    out_path  = OUT_DIR / f"daily_{csv_last.isoformat()}.md"
    latest_md = OUT_DIR / "latest.md"

    md = [
        "# Oslo Børs – Teknisk dagsrapport\n",
        f"**Dato:** {csv_last.strftime('%d.%m.%Y')}\n",
        f"**Telling:** BUY {len(BUY)} | SELL {len(SELL)} "
        f"| BUY-watch {len(BUY_watch)} | SELL-watch {len(SELL_watch)}\n",

        "\n## BUY (rangert)\n",
        _main_table(BUY),
        f"\n\n**Hvorfor toppnavn kvalifiserte**\n\n{_reason_top(BUY, 'BUY')}\n",

        "\n## SELL (rangert)\n",
        _main_table(SELL),
        f"\n\n**Hvorfor toppnavn kvalifiserte**\n\n{_reason_top(SELL, 'SELL')}\n",

        "\n## BUY-watch (nærmest trigger)\n",
        _watch_table(BUY_watch),

        "\n\n## SELL-watch (nærmest trigger)\n",
        _watch_table(SELL_watch),

        "\n\n---\n",
        f"**Kontroller:** {price_check}. Ferskhet OK (CSV-dato er siste handelsdag).\n",
        "_Event/Fundamentale flagg_: pending nyhets- og fundamentals-API.\n",
    ]

    content = "\n".join(md)
    out_path.write_text(content, encoding="utf-8")
    latest_md.write_text(content, encoding="utf-8")
    print(f"Wrote {out_path} and {latest_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
