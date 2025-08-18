# scripts/build_v231_report.py
# Leser latest.csv, gjør v2.3.1-klassifisering, sjekker ferskhet, verifiserer én pris,
# og skriver Markdown-rapport til summaries/daily_v231_<YYYY-MM-DD>.md

import os, sys, random, datetime as dt, math, pathlib
import pandas as pd
import numpy as np
import yfinance as yf

CSV_PATH = "latest.csv"
OUT_DIR = pathlib.Path("summaries")
OUT_DIR.mkdir(exist_ok=True)

# --- Hjelpefunksjoner ---------------------------------------------------------
def last_ose_trading_day(today=None):
    """Forenklet: antatt man–fre, hopper over helg. (Norske helligdager kan legges til senere.)"""
    tz = dt.timezone(dt.timedelta(hours=2))  # sommertid (CET/CEST for enkelhet)
    today = today or dt.datetime.now(tz).date()
    d = today
    # hvis lørdag/søndag, rull bakover
    while d.weekday() >= 5:  # 5=lør, 6=søn
        d = d - dt.timedelta(days=1)
    return d

def fetch_prev_close(ticker, date_str):
    """Hent close for dagen før CSV-datoen fra Yahoo."""
    d = dt.date.fromisoformat(date_str)
    start = d - dt.timedelta(days=10)
    end = d + dt.timedelta(days=1)
    try:
        hist = yf.download(ticker, start=start.isoformat(), end=end.isoformat(),
                           interval="1d", auto_adjust=True, progress=False)
        if hist.empty or "Close" not in hist:
            return np.nan, np.nan
        # finn raden for d og dagen før
        hist.index = pd.to_datetime(hist.index).date
        if d not in hist.index:
            # velg siste dag <= d
            dates = [x for x in hist.index if x <= d]
            if not dates:
                return np.nan, np.nan
            d0 = max(dates)
        else:
            d0 = d
        prev_dates = [x for x in hist.index if x < d0]
        if not prev_dates:
            return np.nan, np.nan
        pday = max(prev_dates)
        return float(hist.loc[pday, "Close"]), float(hist.loc[d0, "Close"])
    except Exception:
        return np.nan, np.nan

def icon_macd(macd, bias):
    if pd.isna(macd): return "◻️"
    if -0.05 <= macd <= 0.05: return "◻️"
    if bias=="BUY": return "✅" if macd>0 else "❌"
    if bias=="SELL": return "✅" if macd<0 else "❌"
    return "◻️"

def icon_sma(pct_above, bias):
    if pd.isna(pct_above): return "◻️"
    if bias=="BUY":
        if pct_above >= 0.2: return "✅"
        if pct_above <= -0.2: return "❌"
        return "◻️"
    if bias=="SELL":
        if pct_above <= -0.2: return "✅"
        if pct_above >= 0.2: return "❌"
        return "◻️"
    return "◻️"

def adx_flag(v):
    if pd.isna(v): return "⚪"
    if v >= 25: return "🟢"
    if 20 <= v < 25: return "⚪"
    return "⚠️"

def mfi_flag(v, bias):
    if pd.isna(v): return "⚪"
    if bias=="BUY":
        if v > 50: return "🟢"
        if 40 <= v <= 60: return "⚪"
        return "🔴"
    if bias=="SELL":
        if v < 50: return "🟢"
        if 40 <= v <= 60: return "⚪"
        return "🔴"
    return "⚪"

def rsi6_flag(v, bias):
    if pd.isna(v): return "⚪"
    if bias=="BUY":
        if v < 10: return "🟢"
        if 10 <= v < 20: return "⚠️"
        if v > 90: return "🔴"
        if 80 <= v <= 90: return "⚠️"
        return "⚪"
    if bias=="SELL":
        if v > 90: return "🟢"
        if 80 <= v <= 90: return "⚠️"
        if v < 10: return "🔴"
        if 10 <= v < 20: return "⚠️"
        return "⚪"
    return "⚪"

# --- Les CSV ------------------------------------------------------------------
if not pathlib.Path(CSV_PATH).exists():
    print("STOPPET – latest.csv mangler")
    sys.exit(1)

df = pd.read_csv(CSV_PATH)
if df.empty:
    print("STOPPET – latest.csv har 0 rader")
    sys.exit(1)

# Kolonnenavn
cols = [c.strip().lower() for c in df.columns]
df.columns = cols

# Ferskhet
csv_dates = pd.to_datetime(df["date"]).dt.date
csv_last = csv_dates.max()
last_trading = last_ose_trading_day()
if csv_last < last_trading:
    print("STOPPET – data er utdatert")
    sys.exit(1)

# Finn en tilfeldig ticker for prisverifikasjon
random.seed(42)
sample_row = df.sample(1, random_state=42).iloc[0]
tick = sample_row["ticker"]
prev_close, day_close = fetch_prev_close(tick, csv_last.isoformat())
price_check = ""
if not (math.isnan(prev_close) or math.isnan(day_close)):
    csv_close = float(sample_row["close"])
    deviation = abs(csv_close - day_close) / max(1e-9, day_close) * 100
    if deviation > 0.1:
        print("STOPPET – prisavvik >0,1 %")
        sys.exit(1)
    price_check = f"Pris-sjekk: {tick} CSV={csv_close:.3f} vs Yahoo={day_close:.3f} → avvik {deviation:.2f}% (OK)"
else:
    price_check = f"Pris-sjekk: {tick} – data unavailable (kunne ikke hente gårsdagens close)"

# --- Klassifisering v2.3.1 ----------------------------------------------------
need_rsi_dir = "rsi_dir" in df.columns
notes = []

# Hent bare for kandidater i RSI-sonene (mye raskere og mer stabilt)
candidates = df[(df["rsi14"] <= 35) | (df["rsi14"] >= 65)]["ticker"].dropna().unique().tolist()
# Hent kun for kandidater i RSI-sonene (raskere og mer stabilt)
candidates = df[(df["rsi14"] <= 35) | (df["rsi14"] >= 65)]["ticker"].dropna().unique().tolist()
prev_map = {}
for t in candidates:
    p, dclose = fetch_prev_close(t, csv_last.isoformat())
    prev_map[t] = (p, dclose)

def classify_row(r):
    t = r["ticker"]
    rsi14 = r.get("rsi14", np.nan)
    macd = r.get("macd_hist", np.nan)
    pct = r.get("pct_above_sma50", np.nan)
    adx = r.get("adx14", np.nan)
    rsi6 = r.get("rsi6", np.nan)
    mfi = r.get("mfi14", np.nan)
    rdir = r.get("rsi_dir", np.nan) if need_rsi_dir else np.nan

    # Opp-/ned-dag via gårsdagens close
    prev_c, today_c = prev_map.get(t, (np.nan, np.nan))
    day_up = (not math.isnan(prev_c) and not math.isnan(today_c) and today_c > prev_c)
    day_down = (not math.isnan(prev_c) and not math.isnan(today_c) and today_c < prev_c)

    bias = "NEUTRAL"
    if (not pd.isna(rsi14)) and rsi14 <= 35 and day_up:
        bias = "BUY"
    elif (not pd.isna(rsi14)) and rsi14 >= 65 and day_down:
        bias = "SELL"

    macd_icon = icon_macd(macd, bias)
    sma_icon = icon_sma(pct, bias)
    adx_icon = adx_flag(adx)

    # RSI-dir ikon per spesifikasjon
    if math.isnan(rdir):
        rdir_cell = "◻️"
    else:
        if bias=="BUY":
            rdir_cell = "✅" if rdir >= 0.5 else ("❌" if rdir <= -0.5 else "◻️")
        elif bias=="SELL":
            rdir_cell = "✅" if rdir <= -0.5 else ("❌" if rdir >= 0.5 else "◻️")
        else:
            rdir_cell = "◻️"

    # Rank = antall støttende hovedsignaler
    rank = 0
    if macd_icon == "✅": rank += 1
    if sma_icon == "✅": rank += 1
    if adx_icon == "🟢": rank += 1

    # Sekundære flagg
    mfi_f = mfi_flag(mfi, bias)
    rsi6_f = rsi6_flag(rsi6, bias)

    # Nærmeste terskel (for watch)
    closest = ""
    if bias=="NEUTRAL":
        if not pd.isna(rsi14):
            # velg retning nærmest sone + MACD→0 + SMA→±0.2
            candidates = []
            candidates.append(("RSI14→35", abs(rsi14-35)))
            candidates.append(("RSI14→65", abs(rsi14-65)))
            if not pd.isna(macd): candidates.append(("MACD→0", abs(macd)))
            if not pd.isna(pct):  candidates.append(("SMA→±0.2%", min(abs(pct-0.2), abs(pct+0.2))))
            lab, dv = sorted(candidates, key=lambda x: x[1])[0]
            closest = f"{lab} (Δ={dv:.2f})"

    return {
        "ticker": t,
        "close": r.get("close", np.nan),
        "rsi14": rsi14,
        "macd": macd,
        "pct": pct,
        "adx": adx,
        "rsi6": rsi6,
        "mfi": mfi,
        "bias": bias,
        "macd_icon": macd_icon,
        "sma_icon": sma_icon,
        "adx_icon": adx_icon,
        "rdir_cell": rdir_cell,
        "rank": rank,
        "closest": closest
    }

enriched = pd.DataFrame([classify_row(r) for _, r in df.iterrows()])

BUY = enriched[enriched["bias"]=="BUY"].copy()
SELL = enriched[enriched["bias"]=="SELL"].copy()
WATCH = enriched[enriched["bias"]=="NEUTRAL"].copy()

# Sortering
BUY = BUY.sort_values(["rank","adx","macd","pct"], ascending=[False,False,False,False])
SELL = SELL.sort_values(["rank","adx","macd","pct"], ascending=[False,False,True,True])

# Header-tall
header_counts = {
    "BUY": len(BUY),
    "SELL": len(SELL),
    "BUY-watch": int(((df["rsi14"]<=35).fillna(False)).sum()) - len(BUY),
    "SELL-watch": int(((df["rsi14"]>=65).fillna(False)).sum()) - len(SELL),
    "NEUTRAL": len(WATCH)
}

# Markdown-tabeller
def fmt_val(v, nd=3):
    return "data unavailable" if pd.isna(v) else (f"{v:.{nd}f}" if isinstance(v,(float,int,np.floating)) else str(v))

def mk_buy_sell_table(sub):
    lines = ["| Rk | Ticker | Close | RSI14 | MACD | SMA% | ΔRSI | ADX | Sec. | Event |",
             "|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for _,r in sub.head(10).iterrows():
        sec = f"RSI6 {fmt_val(r['rsi6'],0)} {rsi6_flag(r['rsi6'], r['bias'])} · MFI {fmt_val(r['mfi'],0)} {mfi_flag(r['mfi'], r['bias'])}"
        lines.append("| {rank} | {t} | {c} | {rsi} | {macd} {mi} | {pct}% {si} | {rdir} | {adx} {ai} | {sec} | — |".format(
            rank=int(r['rank']),
            t=r['ticker'],
            c=fmt_val(r['close']),
            rsi=fmt_val(r['rsi14'],1),
            macd=("+" if r['macd']>=0 else "")+fmt_val(r['macd'],4) if not pd.isna(r['macd']) else "data unavailable",
            mi=r['macd_icon'],
            pct=fmt_val(r['pct'],2) if not pd.isna(r['pct']) else "data unavailable",
            si=r['sma_icon'],
            rdir=r['rdir_cell'] if need_rsi_dir else "◻️",
            adx=fmt_val(r['adx'],0),
            ai=r['adx_icon'],
            sec=sec
        ))
    return "\n".join(lines)

def mk_watch_table(sub):
    lines = ["| Closest | Ticker | Close | RSI14 | MACD | SMA% | ΔRSI | ADX | Sec. | Event |",
             "|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    sub = sub.copy()
    # Ta med bare de som er i RSI-soner men ikke besto gate → nærmest trigger
    for _,r in sub.head(40).iterrows():
        sec = f"RSI6 {fmt_val(r['rsi6'],0)} {rsi6_flag(r['rsi6'], r['bias'])} · MFI {fmt_val(r['mfi'],0)} {mfi_flag(r['mfi'], r['bias'])}"
        lines.append("| {closest} | {t} | {c} | {rsi} | {macd} {mi} | {pct}% {si} | {rdir} | {adx} {ai} | {sec} | — |".format(
            closest=r['closest'] or "—",
            t=r['ticker'],
            c=fmt_val(r['close']),
            rsi=fmt_val(r['rsi14'],1),
            macd=("+" if r['macd']>=0 else "")+fmt_val(r['macd'],4) if not pd.isna(r['macd']) else "data unavailable",
            mi=r['macd_icon'],
            pct=fmt_val(r['pct'],2) if not pd.isna(r['pct']) else "data unavailable",
            si=r['sma_icon'],
            rdir=r['rdir_cell'] if need_rsi_dir else "◻️",
            adx=fmt_val(r['adx'],0),
            ai=r['adx_icon'],
            sec=sec
        ))
    return "\n".join(lines)

buy_tbl = mk_buy_sell_table(BUY)
sell_tbl = mk_buy_sell_table(SELL)
watch_tbl = mk_watch_table(WATCH)

# Kort tekst for toppnavn
def reason_top(sub, side):
    if sub.empty: return f"- Ingen {side} i dag."
    r = sub.iloc[0]
    parts = []
    parts.append(f"**{r['ticker']}** kvalifiserer via gatekeeper ({'RSI≤35 & opp-dag' if side=='BUY' else 'RSI≥65 & ned-dag'}).")
    if r['macd_icon']=='✅': parts.append("MACD støtter (✅).")
    if r['sma_icon']=='✅': parts.append("SMA50-støtte (✅).")
    if r['adx_icon']=='🟢': parts.append("ADX≥25 (🟢).")
    if not parts: parts.append("Hovedsignal-støtte er svak/nøytral (◻️).")
    parts.append(f"Sekundært: RSI6 {fmt_val(r['rsi6'],0)} / MFI {fmt_val(r['mfi'],0)}.")
    return " - " + " ".join(parts)

buy_reason = reason_top(BUY, "BUY")
sell_reason = reason_top(SELL, "SELL")

# Skriv markdown
out_name = f"daily_v231_{csv_last.isoformat()}.md"
out_path = OUT_DIR / out_name
md = []
md.append(f"# Oslo Børs — Teknisk dagsrapport (v2.3.1)\n")
md.append(f"**Dato:** {csv_last.strftime('%d.%m.%Y')}")
md.append(f"\n**Telling:** BUY {header_counts['BUY']} | SELL {header_counts['SELL']} | BUY-watch {header_counts['BUY-watch']} | SELL-watch {header_counts['SELL-watch']} | NEUTRAL {header_counts['NEUTRAL']}\n")
if not need_rsi_dir:
    md.append("\n*Merk: `rsi_dir` mangler i CSV → ΔRSI vises som ◻️ og vurderes som data unavailable.*\n")

md.append("\n## BUY (rangert)\n" + buy_tbl)
md.append("\n## SELL (rangert)\n" + sell_tbl)
md.append("\n## WATCH (nærmest trigger)\n" + watch_tbl)

md.append("\n### Hvorfor toppnavn kvalifiserte\n" + buy_reason + "\n" + sell_reason)
md.append("\n### Event/Fundamentale flagg\n*Pending nyhetsmodul og fundamentals-API; alt markert ⚪ i dag.*")
md.append(f"\n\n**Kontroller:** {price_check}. Ferskhet OK (CSV-dato er siste handelsdag).\n")

out_path.write_text("\n".join(md), encoding="utf-8")
print(f"Wrote {out_path}")
