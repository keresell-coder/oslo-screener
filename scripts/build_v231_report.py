# scripts/build_v231_report.py
# v2.3.1 — Bygger teknisk dagsrapport fra latest.csv til summaries/daily_v231_<YYYY-MM-DD>.md
# - Ferskhetssjekk (virkedag, helg-hopp; helligdager kan legges til senere)
# - En tilfeldig prisverifisering mot Yahoo (±0.1 %)
# - Klassifisering:
#     Gatekeeper: RSI14 <=35 eller >=65
#     BUY:  RSI14<=35 og (RSI_dir>0 hvis finnes, ellers dagsclose>forrige close)
#     SELL: RSI14>=65 og (RSI_dir<0 hvis finnes, ellers dagsclose<forrige close)
#     Ellers BUY-watch/SELL-watch hvis i gate men feil retning; resten utelates
# - Hovedsignal-ikoner: MACD-hist (±0.05 nøytral), SMA50 ±0.2%, ADX>=25
# - Sekundære flagg: MFI, RSI6 tolket relativt til bias
# - Markdown-tabbeller: BUY, SELL, BUY-watch, SELL-watch
# - Ingen OpenAI-kall og ingen exec_summary her

from __future__ import annotations

import sys, math, random
import pathlib as pl
import datetime as dt
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf


CSV_PATH = "latest.csv"
OUT_DIR  = pl.Path("summaries")
OUT_DIR.mkdir(exist_ok=True)

# ---------- Hjelp: siste OSE-handelsdag (forenklet: hopper over helg) ----------
def last_ose_trading_day(today: dt.date | None = None) -> dt.date:
    tz = ZoneInfo("Europe/Oslo")
    if today is None:
        today = dt.datetime.now(tz).date()
    d = today
    # Lørdag/søndag -> rull tilbake
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d
# (Du kan senere legge til norsk helligdagsfil og hoppe over disse også.)

# ---------- Yahoo-hjelp: finn forrige og dagens close rundt CSV-dato ----------
def fetch_prev_and_day_close(ticker: str, csv_date: dt.date) -> tuple[float | float("nan"), float | float("nan")]:
    """
    Henter daglige kurser fra Yahoo; returnerer (forrige_close, dags_close) for dato <= csv_date.
    Dersom csv_date ikke finnes i data (f.eks. stengt), tas nærmeste siste handelsdag <= csv_date.
    """
    try:
        # Hent et lite vindu rundt csv_date
        start = (csv_date - dt.timedelta(days=10)).isoformat()
        end   = (csv_date + dt.timedelta(days=1)).isoformat()
        hist = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=True, progress=False)
        if hist.empty or "Close" not in hist:
            return np.nan, np.nan

        # Normaliser index til date (naiv)
        idx_dates = [x.date() for x in hist.index.to_pydatetime()]
        ser = pd.Series(hist["Close"].values, index=idx_dates).sort_index()

        # Finn nærmeste handelsdag <= csv_date
        days = [d for d in ser.index if d <= csv_date]
        if not days:
            return np.nan, np.nan
        d0 = max(days)  # handelsdagen vi sammenligner mot
        prev_days = [d for d in ser.index if d < d0]
        if not prev_days:
            return np.nan, float(ser.loc[d0])
        pday = max(prev_days)
        return float(ser.loc[pday]), float(ser.loc[d0])

    except Exception:
        return np.nan, np.nan

# ---------- Ikon/logikkhjelp ----------
def icon_macd(macd: float, bias: str) -> str:
    if pd.isna(macd): return "◻️"
    if -0.05 <= macd <= 0.05: return "◻️"
    if bias == "BUY":  return "✅" if macd > 0 else "❌"
    if bias == "SELL": return "✅" if macd < 0 else "❌"
    return "◻️"

def icon_sma(pct_above: float, bias: str) -> str:
    if pd.isna(pct_above): return "◻️"
    if bias == "BUY":
        if pct_above >= 0.2:  return "✅"
        if pct_above <= -0.2: return "❌"
        return "◻️"
    if bias == "SELL":
        if pct_above <= -0.2: return "✅"
        if pct_above >= 0.2:  return "❌"
        return "◻️"
    return "◻️"

def adx_flag(v: float) -> tuple[str, str]:
    if pd.isna(v): return "—", "⚪"
    if v >= 25: return f"{int(v)}", "🟢"
    if 20 <= v < 25: return f"{int(v)}", "⚪"
    return f"{int(v)}", "⚠️"

def mfi_flag(v: float, bias: str) -> str:
    if pd.isna(v): return "⚪"
    if bias == "BUY":
        if v > 50: return "🟢"
        if 40 <= v <= 60: return "⚪"
        return "🔴"
    if bias == "SELL":
        if v < 50: return "🟢"
        if 40 <= v <= 60: return "⚪"
        return "🔴"
    return "⚪"

def rsi6_flag(v: float, bias: str) -> str:
    if pd.isna(v): return "⚪"
    if bias == "BUY":
        if v < 10: return "🟢"
        if 10 <= v <= 20: return "⚠️"
        if v > 90: return "🔴"
        return "⚪"
    if bias == "SELL":
        if v > 90: return "🟢"
        if 80 <= v <= 90: return "⚠️"
        if v < 10: return "🔴"
        return "⚪"
    return "⚪"

def fmt_val(v: float, nd=2) -> str:
    return "—" if pd.isna(v) else f"{v:.{nd}f}"

# ---------- Laster CSV og gjør kvalitetssjekker ----------
if not pl.Path(CSV_PATH).exists():
    print("KUNNE IKKE HENTE latest.csv")
    sys.exit(1)

df = pd.read_csv(CSV_PATH)
if df.empty:
    print("KUNNE IKKE HENTE latest.csv")
    sys.exit(1)

# Kolonnenavn til små bokstaver
df.columns = [c.strip().lower() for c in df.columns]

# Ferskhet: robust konvertering til datoer (dropp NaT før max -> unngår TypeError)
if "date" not in df.columns:
    print("STOPPET – data er utdatert (date-felt mangler).")
    sys.exit(1)

csv_dates = pd.to_datetime(df["date"], errors="coerce").dropna().dt.date
if csv_dates.empty:
    print("STOPPET – data er utdatert (kun ugyldige datoer).")
    sys.exit(1)

csv_last: dt.date = csv_dates.max()
last_trading = last_ose_trading_day()
if csv_last < last_trading:
    print("STOPPET – data er utdatert.")
    sys.exit(1)

# Finn kandidater i RSI-sonene (reduserer Yahoo-kall)
rsi_col = "rsi14" if "rsi14" in df.columns else None
if rsi_col is None:
    print("STOPPET – rsi14 mangler i CSV.")
    sys.exit(1)

# Map for (prev_close, day_close) per ticker for csv_last
prev_map: dict[str, tuple[float, float]] = {}
cands = df.loc[(df[rsi_col] <= 35) | (df[rsi_col] >= 65), "ticker"].dropna().unique().tolist()
for t in cands:
    p, dclose = fetch_prev_and_day_close(str(t), csv_last)
    prev_map[str(t)] = (p, dclose)

# Trekk én tilfeldig ticker for prisverifisering
random.seed(42)
if len(cands) > 0:
    sample_t = random.choice(cands)
else:
    sample_t = str(df["ticker"].iloc[0])
pclose, dclose = prev_map.get(sample_t, (np.nan, np.nan))
price_check = "Pris-sjekk: data unavailable"
if not (pd.isna(pclose) or pd.isna(dclose)):
    # Sjekk dagens close i CSV mot Yahoo sin dagsclose (±0,1 %)
    row = df.loc[df["ticker"] == sample_t].head(1)
    if not row.empty and "close" in row:
        csv_close = float(row["close"].iloc[0])
        if csv_close > 0 and dclose > 0:
            dev = abs(csv_close - dclose) / max(csv_close, dclose) * 100.0
            if dev > 0.1:
                print("STOPPET – prisavvik >0,1 %")
                sys.exit(1)
            price_check = f"Pris-sjekk: {sample_t} CSV={csv_close:.3f} vs Yahoo {dclose:.3f} – avvik {dev:.2f}% (OK)"
else:
    price_check = f"Pris-sjekk: {sample_t} data unavailable (kunne ikke hente dagsclose)"

need_rsi_dir = "rsi_dir" in df.columns

# ---------- Klassifisering pr. rad ----------
def classify_row(r: pd.Series) -> dict:
    t   = str(r.get("ticker"))
    c   = float(r.get("close", np.nan)) if not pd.isna(r.get("close")) else np.nan
    r14 = float(r.get("rsi14",  np.nan))
    r6  = float(r.get("rsi6",   np.nan))
    mfi = float(r.get("mfi14",  np.nan))
    macd= float(r.get("macd_hist", np.nan))
    pct = float(r.get("pct_above_sma50", np.nan))
    adx = float(r.get("adx14",  np.nan))
    rdir= float(r.get("rsi_dir", np.nan)) if need_rsi_dir else np.nan

    # Retning via RSI_dir (om finnes) ellers via dags-opp/ned vs forrige close
    day_up = day_down = False
    if need_rsi_dir and not pd.isna(rdir):
        day_up   = (rdir > 0)
        day_down = (rdir < 0)
    else:
        p, d = prev_map.get(t, (np.nan, np.nan))
        if not (pd.isna(p) or pd.isna(d)):
            day_up   = (d > p)
            day_down = (d < p)

    bias = "NEUTRAL"
    bucket = "NEUTRAL"
    if not pd.isna(r14) and r14 <= 35:
        if day_up: 
            bias = "BUY"; bucket = "BUY"
        else:
            bucket = "BUY-watch"
    elif not pd.isna(r14) and r14 >= 65:
        if day_down: 
            bias = "SELL"; bucket = "SELL"
        else:
            bucket = "SELL-watch"

    macd_icon = icon_macd(macd, bias)
    sma_icon  = icon_sma(pct,  bias)
    adx_val, adx_ic = adx_flag(adx)
    mfi_ic    = mfi_flag(mfi, bias if bucket in ("BUY","SELL") else "NEUTRAL")
    rsi6_ic   = rsi6_flag(r6,  bias if bucket in ("BUY","SELL") else "NEUTRAL")

    # Rank: antall støttende hovedsignaler
    rank = 0
    if macd_icon == "✅": rank += 1
    if sma_icon  == "✅": rank += 1
    if not pd.isna(adx) and adx >= 25: rank += 1

    # Closest (for watch): min dist til RSI14->(35/65), MACD->0, SMA%->±0.2
    closest = "—"
    if bucket.endswith("watch"):
        opts: list[tuple[str,float]] = []
        if not pd.isna(r14):
            if r14 <= 35:
                opts.append(("RSI→35", abs(35 - r14)))
            elif r14 >= 65:
                opts.append(("RSI→65", abs(r14 - 65)))
        if not pd.isna(macd):
            opts.append(("MACD→0", abs(macd)))
        if not pd.isna(pct):
            # avstand til nærmeste terskel 0.2 i rett retning
            opts.append(("SMA→±0.2", max(0.0, 0.2 - abs(pct))))
        if opts:
            lab, dv = sorted(opts, key=lambda x: x[1])[0]
            closest = f"{lab} (Δ={dv:.2f})"

    return {
        "bucket": bucket,
        "rank":   rank,
        "ticker": t,
        "close":  c,
        "rsi14":  r14,
        "rdir":   rdir if need_rsi_dir else np.nan,
        "macd":   macd,
        "pct":    pct,
        "adx":    adx,
        "rsi6":   r6,
        "mfi":    mfi,
        "macd_ic": macd_icon,
        "sma_ic":  sma_icon,
        "adx_ic":  adx_ic,
        "mfi_ic":  mfi_ic,
        "rsi6_ic": rsi6_ic,
        "closest": closest,
        "event":   "—",  # ekte nyhetsmodul kobles inn senere
    }

enriched = pd.DataFrame([classify_row(r) for _, r in df.iterrows()])

BUY        = enriched.loc[enriched["bucket"]=="BUY"].copy()
SELL       = enriched.loc[enriched["bucket"]=="SELL"].copy()
BUY_watch  = enriched.loc[enriched["bucket"]=="BUY-watch"].copy()
SELL_watch = enriched.loc[enriched["bucket"]=="SELL-watch"].copy()

# Sortering (rank desc, deretter ADX desc, MACD/|pct| gir nyttig sekundær rekkefølge)
def sort_main(x: pd.DataFrame) -> pd.DataFrame:
    if x.empty: return x
    return x.sort_values(["rank","adx","macd","pct"], ascending=[False,False,False,False])

BUY  = sort_main(BUY)
SELL = sort_main(SELL)

# Teller til header
header_counts = {
    "BUY":        len(BUY),
    "SELL":       len(SELL),
    "BUY-watch":  len(BUY_watch),
    "SELL-watch": len(SELL_watch),
}

# --------- Tabelldeler ---------
def mk_buy_sell_table(sub: pd.DataFrame) -> str:
    if sub.empty:
        return "_Ingen i dag._"
    lines = ["| Rk | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. | Event |",
             "|---:|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|:-----|"]
    for _, r in sub.head(40).iterrows():
        sec = f"RSI6 {fmt_val(r['rsi6'],0)} {r['rsi6_ic']} · MFI {fmt_val(r['mfi'],0)} {r['mfi_ic']}"
        delta = "—" if pd.isna(r["rdir"]) else f"{r['rdir']:+.2f}"
        adx_cell = f"{fmt_val(r['adx'],0)} {r['adx_ic']}"
        lines.append(f"| {int(r['rank'])} | {r['ticker']} | {fmt_val(r['close'])} | {fmt_val(r['rsi14'])} | "
                     f"{delta} | {fmt_val(r['macd'])} {r['macd_ic']} | {fmt_val(r['pct'])} {r['sma_ic']} | "
                     f"{adx_cell} | {sec} | {r['event']} |")
    return "\n".join(lines)

def mk_watch_table(sub: pd.DataFrame) -> str:
    if sub.empty:
        return "_Ingen i dag._"
    lines = ["| Closest | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. | Event |",
             "|:-------|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|:-----|"]
    for _, r in sub.head(40).iterrows():
        sec = f"RSI6 {fmt_val(r['rsi6'],0)} {r['rsi6_ic']} · MFI {fmt_val(r['mfi'],0)} {r['mfi_ic']}"
        delta = "—" if pd.isna(r["rdir"]) else f"{r['rdir']:+.2f}"
        adx_cell = f"{fmt_val(r['adx'],0)} {r['adx_ic']}"
        lines.append(f"| {r['closest']} | {r['ticker']} | {fmt_val(r['close'])} | {fmt_val(r['rsi14'])} | "
                     f"{delta} | {fmt_val(r['macd'])} {r['macd_ic']} | {fmt_val(r['pct'])} {r['sma_ic']} | "
                     f"{adx_cell} | {sec} | {r['event']} |")
    return "\n".join(lines)

def reason_top(sub: pd.DataFrame, side: str) -> str:
    if sub.empty: return f"_Ingen {side} i dag._"
    r = sub.iloc[0]
    parts = [f"{r['ticker']} kvalifiserte via gatekeeper "
             f"({'RSI≤35 & opp-dag' if side=='BUY' else 'RSI≥65 & ned-dag'})."]
    if r["macd_ic"] == "✅": parts.append("MACD støtter (✅).")
    if r["sma_ic"]  == "✅": parts.append("SMA50-støtte (✅).")
    if not pd.isna(r["adx"]) and r["adx"] >= 25: parts.append("ADX≥25 (🟢).")
    if not parts: parts.append("Hovedsignal-støtte er svak/nøytral (◻️).")
    return " ".join(parts)

buy_tbl  = mk_buy_sell_table(BUY)
sell_tbl = mk_buy_sell_table(SELL)
bw_tbl   = mk_watch_table(BUY_watch)
sw_tbl   = mk_watch_table(SELL_watch)

buy_reason  = reason_top(BUY,  "BUY")
sell_reason = reason_top(SELL, "SELL")

# ---------- Skriv markdown ----------
out_name = f"daily_v231_{csv_last.isoformat()}.md"
out_path = OUT_DIR / out_name

md = []
md.append(f"# Oslo Børs – Teknisk dagsrapport (v2.3.1)\n")
md.append(f"**Dato:** {csv_last.strftime('%d.%m.%Y')}\n")
md.append(f"**Telling:** BUY {header_counts['BUY']} | SELL {header_counts['SELL']} | "
          f"BUY-watch {header_counts['BUY-watch']} | SELL-watch {header_counts['SELL-watch']}\n")
if not need_rsi_dir:
    md.append("\n_⚠️ Merk:_ `rsi_dir` mangler i CSV – ΔRSI vises som «—», og retning vurderes via daglig opp/ned mot gårsdagens close.\n")

md.append("\n## BUY (rangert)\n")
md.append(buy_tbl)
md.append("\n\n**Hvorfor toppnavn kvalifiserte**\n\n" + buy_reason + "\n")

md.append("\n## SELL (rangert)\n")
md.append(sell_tbl)
md.append("\n\n**Hvorfor toppnavn kvalifiserte**\n\n" + sell_reason + "\n")

md.append("\n## BUY-watch (nærmest trigger)\n")
md.append(bw_tbl)

md.append("\n\n## SELL-watch (nærmest trigger)\n")
md.append(sw_tbl)

md.append("\n\n---\n")
md.append(f"**Kontroller:** {price_check}. Ferskhet OK (CSV-dato er siste handelsdag).\n")
md.append("_Event/Fundamentale flagg_: pending nyhets- og fundamentals-API.\n")

out_path.write_text("\n".join(md), encoding="utf-8")
print(f"Wrote {out_path}")
# ... etter out_path.write_text("\n".join(md), encoding="utf-8")
latest_md = OUT_DIR / "latest_v231.md"
latest_md.write_text((OUT_DIR / out_name).read_text(encoding="utf-8"), encoding="utf-8")
print(f"Wrote {out_path} and {latest_md}")
