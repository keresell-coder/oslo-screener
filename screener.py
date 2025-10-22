# screener.py – konfig-styrt versjon (RSI14/RSI6, dagsretning, SMA50, MACD-hist, ADX, MFI)
# Output: latest.csv + report_*.csv + buy/sell/watch_*.csv + konsollsummary

import os, time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf
import yaml

from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD, ADXIndicator
from ta.volume import MFIIndicator

TICKERS_FILE = os.getenv("TICKERS_FILE", "tickers.txt")
VALID_TICKERS_FILE = os.getenv("VALID_TICKERS_FILE", "valid_tickers.txt")
YF_PAUSE = float(os.getenv("YF_PAUSE", "0.35"))  # kan endres i Actions

# ---------- Konfig ----------
def load_config(path: str = "config.yaml") -> dict:
    defaults = {
        "rsi14_buy_max": 35, "rsi14_sell_min": 65,
        "require_day_up_for_buy": True, "require_day_down_for_sell": True,
        "use_sma50_support": True, "use_macd_hist_support": True,
        "adx_low_max": 20, "adx_moderate_max": 30,
        "stop_loss_low": 1.75, "stop_loss_moderate": 3.0, "stop_loss_high": 5.0,
        "position_high_conviction": 5.0, "position_moderate": 3.0, "position_low": 1.5,
        "min_history_days": 60, "rsi6_length": 6, "sma50_length": 50,
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
        "adx_length": 14, "mfi_length": 14,
    }
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        for k in defaults:
            if k in data:
                defaults[k] = data[k]
    except FileNotFoundError:
        pass
    return defaults

# ---------- Hjelp ----------
def _read_tickers_from_file(path: str) -> list[str]:
    with open(path) as f:
        return [t.strip() for t in f if t.strip()]


def load_tickers(path: str = TICKERS_FILE, validated_path: str = VALID_TICKERS_FILE):
    """Return tickers prioritising the validated list when available.

    The weekly validation job produces ``valid_tickers.txt``. When that file is
    present and non-empty we should prefer it so that the screener always runs on
    the latest validated ticker universe. If the validated file is missing or
    empty we gracefully fall back to ``tickers.txt`` which is the manually
    maintained list.
    """

    candidates: list[str] = []
    if validated_path:
        candidates.append(validated_path)
    if path and path not in candidates:
        candidates.append(path)

    for candidate in candidates:
        try:
            tickers = _read_tickers_from_file(candidate)
        except FileNotFoundError:
            continue

        if tickers:
            return tickers

    raise FileNotFoundError(
        f"Could not load tickers from any candidate file: {', '.join(candidates)}"
    )

def flatten(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        lvl0 = list(df.columns.get_level_values(0))
        lvl1 = list(df.columns.get_level_values(1))
        if "Close" in lvl0 and len(set(lvl1)) == 1:
            df.columns = lvl0
        elif "Close" in lvl1 and len(set(lvl0)) == 1:
            df.columns = lvl1
    return df

def fetch_ohlc_single(ticker: str, tries: int = 3) -> pd.DataFrame | None:
    last_exc = None
    for attempt in range(1, tries + 1):
        try:
            df = yf.download(
                ticker, period="9mo", interval="1d",
                auto_adjust=True, progress=False, threads=False
            )
            df = flatten(df)
            if df is not None and not df.empty and len(df) >= 60:
                return df
        except Exception as e:
            last_exc = e
        time.sleep(YF_PAUSE * attempt)
    return None

def adx_band_with_cfg(adx_val: float, cfg: dict):
    if pd.isna(adx_val): return ("UNKNOWN", np.nan, "UNKNOWN")
    if adx_val < cfg["adx_low_max"]:
        return ("LOW", cfg["stop_loss_low"], "LOW")
    if adx_val <= cfg["adx_moderate_max"]:
        return ("MODERATE", cfg["stop_loss_moderate"], "MODERATE")
    return ("HIGH", cfg["stop_loss_high"], "HIGH")

def position_from_primary_and_adx(primary_count: int, adx_val: float, cfg: dict):
    # High conviction hvis 3/3 + ADX >= 25 (terskel kan evt. gjøres konfigurerbar senere)
    if primary_count >= 3 and adx_val >= 25:
        return cfg["position_high_conviction"]
    elif primary_count >= 2:
        return cfg["position_moderate"]
    elif primary_count >= 1:
        return cfg["position_low"]
    else:
        return 0.0

def classify(long_gate: bool, short_gate: bool, day_up: bool, day_down: bool,
             price: float, sma50: float, macd_hist: float, cfg: dict):
    use_sma = cfg["use_sma50_support"]
    use_macd = cfg["use_macd_hist_support"]

    if long_gate:
        trend_support = (
            (use_sma and (not pd.isna(sma50) and price > sma50)) or
            (use_macd and (not pd.isna(macd_hist) and macd_hist > 0))
        )
        need_day = cfg["require_day_up_for_buy"]
        primary_count = int(True) + int(day_up if need_day else True) + int(trend_support)
        label = "BUY" if (day_up or not need_day) else "BUY-watch"
        return label, primary_count

    if short_gate:
        trend_support = (
            (use_sma and (not pd.isna(sma50) and price < sma50)) or
            (use_macd and (not pd.isna(macd_hist) and macd_hist < 0))
        )
        need_day = cfg["require_day_down_for_sell"]
        primary_count = int(True) + int(day_down if need_day else True) + int(trend_support)
        label = "SELL" if (day_down or not need_day) else "SELL-watch"
        return label, primary_count

    return "NEUTRAL", 0

# ---------- Hovedløp ----------
def run():
    cfg = load_config()
    tickers = load_tickers()
    rows = []

    for t in tickers:
        try:
            df = fetch_ohlc_single(t)
            if df is None or df.empty or len(df) < cfg["min_history_days"]:
                rows.append({"ticker": t, "note": "download_failed_or_insufficient_data"})
                continue

            close = df["Close"]; high = df["High"]; low = df["Low"]; vol = df.get("Volume")
            c0, c1 = close.iloc[-1], close.iloc[-2]
            day_up, day_down = c0 > c1, c0 < c1

            rsi14_series = RSIIndicator(close=close, window=14).rsi()  # 14 beholdes som standard
            rsi6_series  = RSIIndicator(close=close, window=cfg["rsi6_length"]).rsi()
            sma50_series = SMAIndicator(close=close, window=cfg["sma50_length"]).sma_indicator()

            macd_obj = MACD(close=close,
                            window_fast=cfg["macd_fast"],
                            window_slow=cfg["macd_slow"],
                            window_sign=cfg["macd_signal"])
            macd_hist_series = macd_obj.macd_diff()

            adx_obj = ADXIndicator(high=high, low=low, close=close, window=cfg["adx_length"])
            adx_series = adx_obj.adx()

            mfi_series = None
            if vol is not None and not vol.isna().all():
                mfi_series = MFIIndicator(high=high, low=low, close=close, volume=vol, window=cfg["mfi_length"]).money_flow_index()

            rsi14_now = float(rsi14_series.iloc[-1])
            rsi14_prev = float(rsi14_series.iloc[-2]) if not pd.isna(rsi14_series.iloc[-2]) else rsi14_now
            rsi_dir = rsi14_now - rsi14_prev
            rsi6_now = float(rsi6_series.iloc[-1]) if not pd.isna(rsi6_series.iloc[-1]) else np.nan
            sma50_now = float(sma50_series.iloc[-1]) if not pd.isna(sma50_series.iloc[-1]) else np.nan
            macd_hist_now = float(macd_hist_series.iloc[-1]) if not pd.isna(macd_hist_series.iloc[-1]) else np.nan
            adx_now = float(adx_series.iloc[-1]) if not pd.isna(adx_series.iloc[-1]) else np.nan
            mfi_now = float(mfi_series.iloc[-1]) if (mfi_series is not None and not pd.isna(mfi_series.iloc[-1])) else np.nan

            long_gate  = rsi14_now <= cfg["rsi14_buy_max"]
            short_gate = rsi14_now >= cfg["rsi14_sell_min"]

            label, primary_count = classify(
                long_gate, short_gate, day_up, day_down,
                price=float(c0), sma50=sma50_now, macd_hist=macd_hist_now, cfg=cfg
            )

            risk_text, stop_loss_pct, risk_label = adx_band_with_cfg(adx_now, cfg)
            pos_pct = position_from_primary_and_adx(primary_count, adx_now if not np.isnan(adx_now) else 0.0, cfg)

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

    if "signal" not in out.columns:
        out["signal"] = "NEUTRAL"

    signal_order = {"BUY": 0, "SELL": 1, "BUY-watch": 2, "SELL-watch": 3, "NEUTRAL": 4}
    out["signal_rank"] = out["signal"].map(signal_order).fillna(9)
    if "rsi14" in out.columns:
        out.sort_values(["signal_rank", "rsi14"], ascending=[True, True], inplace=True)
    else:
        out.sort_values(["signal_rank"], ascending=[True], inplace=True)
    out.drop(columns=["signal_rank"], inplace=True)

    counts = out["signal"].value_counts(dropna=False).to_dict()
    buy_df        = out[out["signal"] == "BUY"]
    sell_df       = out[out["signal"] == "SELL"]
    buy_watch_df  = out[out["signal"] == "BUY-watch"]
    sell_watch_df = out[out["signal"] == "SELL-watch"]
    
    # --- Signals-only (kun endelige BUY/SELL, ikke watch/neutral) ---
    signals_only = pd.concat([buy_df, sell_df], axis=0) if not buy_df.empty or not sell_df.empty else pd.DataFrame(columns=out.columns)
    if not signals_only.empty:
        # Velg de viktigste kolonnene for hurtiglesing
        cols = [c for c in ["ticker","date","close","rsi14","rsi_dir","macd_hist","sma50","pct_above_sma50","adx14","mfi14","rsi6","signal","primary_count","stop_loss_pct","position_pct","risk"] if c in signals_only.columns]
        signals_only[cols].to_csv("signals_only.csv", index=False)

    if not buy_df.empty:        buy_df.to_csv("buy.csv", index=False)
    if not sell_df.empty:       sell_df.to_csv("sell.csv", index=False)
    if not buy_watch_df.empty:  buy_watch_df.to_csv("watch_buy.csv", index=False)
    if not sell_watch_df.empty: sell_watch_df.to_csv("watch_sell.csv", index=False)

    def _c(d, k): return int(d.get(k, 0))
    print(
        f"Summary — BUY:{_c(counts,'BUY')}  SELL:{_c(counts,'SELL')}  "
        f"BUY-watch:{_c(counts,'BUY-watch')}  SELL-watch:{_c(counts,'SELL-watch')}  "
        f"NEUTRAL:{_c(counts,'NEUTRAL')}"
    )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    outname = f"report_{stamp}.csv"
    out.to_csv(outname, index=False)
    out.to_csv("latest.csv", index=False)
    print(f"Wrote {outname} and latest.csv with {len(out)} rows")

if __name__ == "__main__":
    run()
