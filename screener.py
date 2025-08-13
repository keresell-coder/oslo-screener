## screener.py — versjon med 'ta' (ikke pandas_ta)
import time, os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timezone

# nye imports fra 'ta'
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD, ADXIndicator
from ta.volume import MFIIndicator

TICKERS_FILE = "tickers.txt"
# Pause mellom forespørsler til yfinance (sekunder). Juster ved behov.
YF_PAUSE = float(os.getenv("YF_PAUSE", "0.35"))

def load_tickers(path=TICKERS_FILE):
    with open(path) as f:
        return [t.strip() for t in f if t.strip()]
def fetch_ohlc_single(ticker: str, tries: int = 3) -> pd.DataFrame | None:
    """
    Hent OHLCV for én ticker med noen forsøk. Returnerer None hvis mislykket.
    """
    last_exc = None
    for attempt in range(1, tries + 1):
        try:
            df = yf.download(
                ticker, period="9mo", interval="1d",
                auto_adjust=True, progress=False, threads=False
            )
            # Flatten MultiIndex hvis nødvendig
            if isinstance(df.columns, pd.MultiIndex):
                lvl0 = list(df.columns.get_level_values(0))
                lvl1 = list(df.columns.get_level_values(1))
                if "Close" in lvl0 and len(set(lvl1)) == 1:
                    df.columns = lvl0
                elif "Close" in lvl1 and len(set(lvl0)) == 1:
                    df.columns = lvl1
            # Godta kun «brukbar» historikk
            if df is not None and not df.empty and len(df) >= 60:
                return df
        except Exception as e:
            last_exc = e
        # Backoff-pause (litt lenger per forsøk)
        time.sleep(YF_PAUSE * attempt)
    # Alle forsøk feilet
    return None

def adx_band(adx_val: float):
    if pd.isna(adx_val):
        return ("UNKNOWN", np.nan, "UNKNOWN")
    if adx_val < 20:
        return ("LOW", 1.75, "LOW")
    if adx_val <= 30:
        return ("MODERATE", 3.0, "MODERATE")
    return ("HIGH", 5.0, "HIGH")

def classify(long_gate: bool, short_gate: bool, day_up: bool, day_down: bool,
             price: float, sma50: float, macd_hist: float):
    if long_gate:
        trend_support = ((not pd.isna(sma50) and price > sma50) or (not pd.isna(macd_hist) and macd_hist > 0))
        primary_count = int(True) + int(day_up) + int(trend_support)
        label = "BUY" if day_up else "BUY-watch"
        return label, primary_count
    elif short_gate:
        trend_support = ((not pd.isna(sma50) and price < sma50) or (not pd.isna(macd_hist) and macd_hist < 0))
        primary_count = int(True) + int(day_down) + int(trend_support)
        label = "SELL" if day_down else "SELL-watch"
        return label, primary_count
    else:
        return "NEUTRAL", 0

def position_from_primary_and_adx(primary_count: int, adx_val: float):
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
            df = fetch_ohlc_single(t)
            if df is None:
                rows.append({"ticker": t, "note": "download_failed_or_insufficient_data"})
                continue

            if isinstance(df.columns, pd.MultiIndex):
                lvl0 = list(df.columns.get_level_values(0))
                lvl1 = list(df.columns.get_level_values(1))
                # Vanligst hos deg: ('Close','KOG.OL') -> ta nivå 0
                if "Close" in lvl0 and len(set(lvl1)) == 1:
                    df.columns = lvl0
                # Alternativt om rekkefølgen er ('KOG.OL','Close') -> ta nivå 1
                elif "Close" in lvl1 and len(set(lvl0)) == 1:
                    df.columns = lvl1
            if df.empty or len(df) < 60:
                rows.append({"ticker": t, "note": "insufficient data"})
                continue

            close = df["Close"]; high = df["High"]; low = df["Low"]; vol = df.get("Volume")

            # --- Indikatorer via 'ta' ---
            rsi14_series = RSIIndicator(close=close, window=14).rsi()
            rsi6_series  = RSIIndicator(close=close, window=6).rsi()
            sma50_series = SMAIndicator(close=close, window=50).sma_indicator()

            macd_obj = MACD(close=close)  # 12,26,9 default
            macd_hist_series = macd_obj.macd_diff()

            adx_obj = ADXIndicator(high=high, low=low, close=close, window=14)
            adx_series = adx_obj.adx()

            mfi_series = None
            if vol is not None and not vol.isna().all():
                mfi_series = MFIIndicator(high=high, low=low, close=close, volume=vol, window=14).money_flow_index()


            # --- Dagsdata ---
            c0, c1 = close.iloc[-1], close.iloc[-2]
            day_up, day_down = c0 > c1, c0 < c1

            rsi14_now = float(rsi14_series.iloc[-1])
            rsi14_prev = float(rsi14_series.iloc[-2]) if not pd.isna(rsi14_series.iloc[-2]) else rsi14_now
            rsi_dir = rsi14_now - rsi14_prev

            rsi6_now = float(rsi6_series.iloc[-1]) if not pd.isna(rsi6_series.iloc[-1]) else np.nan
            sma50_now = float(sma50_series.iloc[-1]) if not pd.isna(sma50_series.iloc[-1]) else np.nan
            macd_hist_now = float(macd_hist_series.iloc[-1]) if not pd.isna(macd_hist_series.iloc[-1]) else np.nan
            adx_now = float(adx_series.iloc[-1]) if not pd.isna(adx_series.iloc[-1]) else np.nan
            mfi_now = float(mfi_series.iloc[-1]) if mfi_series is not None and not pd.isna(mfi_series.iloc[-1]) else np.nan

            long_gate = rsi14_now <= 35
            short_gate = rsi14_now >= 65

            label, primary_count = classify(
                long_gate, short_gate, day_up, day_down,
                price=float(c0), sma50=sma50_now, macd_hist=macd_hist_now
            )

            risk_text, stop_loss_pct, risk_label = adx_band(adx_now)
            pos_pct = position_from_primary_and_adx(primary_count, adx_now if not np.isnan(adx_now) else 0.0)

            rows.append({
                "ticker": t,
                "date": df.index[-1].date().isoformat(),
                "close": round(float(c0), 4),
                "rsi14": round(rsi14_now, 2),
                "rsi_dir": round(rsi_dir, 2),
                "macd_hist": round(macd_hist_now, 4) if not np.isnan(macd_hist_now) else np.nan,
                "sma50": round(sma50_now, 4) if not np.isnan(sma50_now) else np.nan,
                "pct_above_sma50": round((float(c0) / sma50_now - 1) * 100, 2) if not np.isnan(sma50_now) and sma50_now != 0 else np.nan,
                "adx14": round(adx_now, 2) if not np.isnan(adx_now) else np.nan,
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

    # Hvis signal-kolonne mangler (f.eks. bare note-rader), sett NEUTRAL
    if "signal" not in out.columns:
        out["signal"] = "NEUTRAL"

    # Sortering: prioriter signal, deretter laveste RSI14
    signal_order = {"BUY": 0, "SELL": 1, "BUY-watch": 2, "SELL-watch": 3, "NEUTRAL": 4}
    out["signal_rank"] = out["signal"].map(signal_order).fillna(9)
    if "rsi14" in out.columns:
        out.sort_values(["signal_rank", "rsi14"], ascending=[True, True], inplace=True)
    else:
        out.sort_values(["signal_rank"], ascending=[True], inplace=True)
    out.drop(columns=["signal_rank"], inplace=True)

    # --- Executive Summary + delte lister ---
    counts = out["signal"].value_counts(dropna=False).to_dict()
    buy_df        = out[out["signal"] == "BUY"]
    sell_df       = out[out["signal"] == "SELL"]
    buy_watch_df  = out[out["signal"] == "BUY-watch"]
    sell_watch_df = out[out["signal"] == "SELL-watch"]

    # Lag egne CSV-er (kun hvis ikke tomme)
    if not buy_df.empty:        buy_df.to_csv("buy.csv", index=False)
    if not sell_df.empty:       sell_df.to_csv("sell.csv", index=False)
    if not buy_watch_df.empty:  buy_watch_df.to_csv("watch_buy.csv", index=False)
    if not sell_watch_df.empty: sell_watch_df.to_csv("watch_sell.csv", index=False)

    # Skriv kort oppsummering
    def _c(d, k): return int(d.get(k, 0))
    print(
        f"Summary — BUY:{_c(counts,'BUY')}  SELL:{_c(counts,'SELL')}  "
        f"BUY-watch:{_c(counts,'BUY-watch')}  SELL-watch:{_c(counts,'SELL-watch')}  "
        f"NEUTRAL:{_c(counts,'NEUTRAL')}"
    )

    # Skriv hovedfiler
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    outname = f"report_{stamp}.csv"
    out.to_csv(outname, index=False)
    out.to_csv("latest.csv", index=False)
    print(f"Wrote {outname} and latest.csv with {len(out)} rows")


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
