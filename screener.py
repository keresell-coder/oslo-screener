# screener.py
# Oslo Børs screener med RSI14/RSI6, dagsretning, SMA50, MACD, ADX, MFI
# Output: latest.csv + tidsstemplet rapport_*.csv

import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
from datetime import datetime, timezone

TICKERS_FILE = "tickers.txt"

def load_tickers(path=TICKERS_FILE):
    with open(path) as f:
        return [t.strip() for t in f if t.strip()]

def adx_band(adx_val: float):
    # Ditt oppsett:
    # <20  => Low risk, 1.75% SL
    # 20-30 => Moderate, 3.0% SL
    # >30  => High, 5.0% SL
    if pd.isna(adx_val):
        return ("UNKNOWN", np.nan, "UNKNOWN")
    if adx_val < 20:
        return ("LOW", 1.75, "LOW")
    if adx_val <= 30:
        return ("MODERATE", 3.0, "MODERATE")
    return ("HIGH", 5.0, "HIGH")

def classify(long_gate: bool, short_gate: bool, day_up: bool, day_down: bool,
             price: float, sma50: float, macd_hist: float):
    """
    Primærlogikk:
    - Gatekeeper: RSI14 <=35 (long) eller >=65 (short)
    - Dagsretning: LONG krever opp-dag, SHORT krever ned-dag
    - Trendstøtte: minst ÉN av (pris over/under SMA50 i riktig retning) eller (MACD-hist >0/<0 i riktig retning)
    """
    if long_gate:
        trend_support = ((not pd.isna(sma50) and price > sma50) or (not pd.isna(macd_hist) and macd_hist > 0))
        primary_count = int(True) + int(day_up) + int(trend_support)  # gatekeeper = 1
        if day_up:
            label = "BUY"
        else:
            label = "BUY-watch"
        return label, primary_count
    elif short_gate:
        trend_support = ((not pd.isna(sma50) and price < sma50) or (not pd.isna(macd_hist) and macd_hist < 0))
        primary_count = int(True) + int(day_down) + int(trend_support)
        if day_down:
            label = "SELL"
        else:
            label = "SELL-watch"
        return label, primary_count
    else:
        return "NEUTRAL", 0

def position_from_primary_and_adx(primary_count: int, adx_val: float):
    """
    Ditt regime:
    - High conviction: 3/3 + ADX >= ~25  -> opptil 5%
    - Moderate:       2/3                -> 2-3% (vi setter 3.0% fast for enkelhet nå)
    - Low:            1/3                -> 1-1.5% (vi setter 1.5%)
    """
    if primary_count >= 3 and adx_val >= 25:
        return 5.0
    elif primary_count >= 2:
        return 3.0
    elif primary_count >= 1:
        return 1.5
    else:
        return 0.0

def run():
    tickers = load_tickers()
    rows = []

    for t in tickers:
        try:
            df = yf.download(t, period="9mo", interval="1d", auto_adjust=True, progress=False)
            if df.empty or len(df) < 60:
                rows.append({"ticker": t, "note": "insufficient data"})
                continue

            # Indikatorer
            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            vol = df.get("Volume")

            rsi14 = ta.rsi(close, length=14)
            rsi6  = ta.rsi(close, length=6)
            sma50 = ta.sma(close, length=50)

            macd = ta.macd(close)  # MACD_12_26_9, MACDs_12_26_9, MACDh_12_26_9
            macd_hist = macd["MACDh_12_26_9"] if macd is not None and "MACDh_12_26_9" in macd else pd.Series(index=close.index, dtype=float)

            adx_df = ta.adx(high, low, close, length=14)  # ADX_14
            adx_val = adx_df["ADX_14"].iloc[-1] if adx_df is not None and "ADX_14" in adx_df else np.nan

            mfi = ta.mfi(high, low, close, vol, length=14)

            # Dagsdata
            c0, c1 = close.iloc[-1], close.iloc[-2]
            day_up, day_down = c0 > c1, c0 < c1

            # RSI målinger
            rsi14_now = float(rsi14.iloc[-1])
            rsi14_prev = float(rsi14.iloc[-2]) if not pd.isna(rsi14.iloc[-2]) else rsi14_now
            rsi_dir = rsi14_now - rsi14_prev
            rsi6_now = float(rsi6.iloc[-1]) if not pd.isna(rsi6.iloc[-1]) else np.nan

            sma50_now = float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else np.nan
            macd_hist_now = float(macd_hist.iloc[-1]) if not pd.isna(macd_hist.iloc[-1]) else np.nan
            mfi_now = float(mfi.iloc[-1]) if not pd.isna(mfi.iloc[-1]) else np.nan

            long_gate = rsi14_now <= 35
            short_gate = rsi14_now >= 65

            label, primary_count = classify(
                long_gate, short_gate, day_up, day_down,
                price=float(c0), sma50=sma50_now, macd_hist=macd_hist_now
            )

            # ADX-bånd og risiko/SL
            risk_text, stop_loss_pct, risk_label = adx_band(adx_val)

            # Posisjonsstørrelse fra primærsignaler + ADX
            pos_pct = position_from_primary_and_adx(primary_count, float(adx_val) if not pd.isna(adx_val) else 0.0)

            rows.append({
                "ticker": t,
                "date": df.index[-1].date().isoformat(),
                "close": round(float(c0), 4),
                "rsi14": round(rsi14_now, 2),
                "rsi_dir": round(rsi_dir, 2),
                "macd_hist": round(macd_hist_now, 4) if not np.isnan(macd_hist_now) else np.nan,
                "sma50": round(sma50_now, 4) if not np.isnan(sma50_now) else np.nan,
                "pct_above_sma50": round((float(c0) / sma50_now - 1) * 100, 2) if not np.isnan(sma50_now) and sma50_now != 0 else np.nan,
                "adx14": round(float(adx_val), 2) if not pd.isna(adx_val) else np.nan,
                "mfi14": round(mfi_now, 2) if not np.isnan(mfi_now) else np.nan,
                "rsi6": round(rsi6_now, 2) if not np.isnan(rsi6_now) else np.nan,
                "signal": label,
                "primary_count": primary_count,
                "stop_loss_pct": stop_loss_pct,
                "position_pct": pos_pct,
                "risk": risk_label
            })

        except Exception as e:
            rows.append({"ticker": t, "note": f"error: {e}"})

    out = pd.DataFrame(rows)

    # Sortér: først signal, deretter “mest interessant” (BUY/SELL øverst, så watch)
    signal_order = {"BUY": 0, "SELL": 1, "BUY-watch": 2, "SELL-watch": 3, "NEUTRAL": 4}
    out["signal_rank"] = out["signal"].map(signal_order).fillna(9)
    out.sort_values(["signal_rank", "rsi14"], ascending=[True, True], inplace=True)
    out.drop(columns=["signal_rank"], inplace=True)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    outname = f"report_{stamp}.csv"
    out.to_csv(outname, index=False)
    out.to_csv("latest.csv", index=False)
    print(f"Wrote {outname} and latest.csv with {len(out)} rows")

if __name__ == "__main__":
    run()
