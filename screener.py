# screener.py – konfig-styrt versjon (RSI14/RSI6, dagsretning, SMA50, MACD-hist, ADX, MFI)
# Output: latest.csv + report_*.csv + buy/sell/watch_*.csv + konsollsummary

import os, time
import hashlib, json, uuid
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf
import yaml

from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD, ADXIndicator
from ta.volume import MFIIndicator
from market_health import SCHEMA, evaluate_snapshot, last_ose_trading_day, finite

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


def load_tickers(path: str = VALID_TICKERS_FILE) -> list[str]:
    """Return tickers from the validated list used by the screener."""

    if not path:
        raise FileNotFoundError("No validated tickers file configured")

    tickers = _read_tickers_from_file(path)
    if not tickers:
        raise ValueError(f"Validated tickers file '{path}' is empty")

    return tickers

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
                auto_adjust=True, progress=False, threads=False, timeout=12
            )
            df = flatten(df)
            if df is not None and not df.empty:
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

OUTPUT_COLUMNS = ["ticker", "date", "source_latest_date", "last_valid_ohlc_date", "data_status", "note", "close", "rsi14",
                  "rsi_dir", "macd_hist", "sma50", "pct_above_sma50", "adx14", "mfi14", "rsi6",
                  "signal", "primary_count", "stop_loss_pct", "position_pct", "risk", "snapshot_id"]


def completed_history(df, expected_session):
    """Discard partial current-session bars before any indicator is calculated."""
    df = df.sort_index()
    if df.index.has_duplicates:
        raise ValueError("duplicate_price_dates")
    return df.loc[[stamp.date() <= expected_session for stamp in df.index]].copy()


def publish_snapshot(rows, universe_count, fetch_started_at, fetch_completed_at,
                     generated_at=None, snapshot_id=None):
    generated_at = generated_at or datetime.now(timezone.utc)
    snapshot_id = snapshot_id or uuid.uuid4().hex
    out = pd.DataFrame(rows).reindex(columns=OUTPUT_COLUMNS)
    out["snapshot_id"] = snapshot_id
    out["signal"] = out["signal"].fillna("WITHHELD")
    out["data_status"] = out["data_status"].fillna("missing")
    expected = last_ose_trading_day(generated_at).isoformat()
    def iso(value):
        return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    metadata = dict(schema=SCHEMA, snapshot_id=snapshot_id, data_fetch_started=iso(fetch_started_at),
                    data_fetch_completed=iso(fetch_completed_at), generated_at=iso(generated_at),
                    expected_session=expected, universe_count=str(universe_count),
                    min_coverage_ratio=os.getenv("MIN_CURRENT_COVERAGE", "0.9"))
    health = evaluate_snapshot(out.to_dict("records"), metadata, generated_at)
    allowed = set(health["eligible_tickers"])
    for excluded in health["excluded"]:
        out.loc[out["ticker"] == excluded["ticker"], ["data_status", "note"]] = [excluded["data_status"], excluded["reason"]]
    out.loc[~out["ticker"].isin(allowed), ["signal", "primary_count", "position_pct"]] = ["WITHHELD", 0, 0.0]
    metadata.update(status=health["status"], market_data_as_of=health["market_data_as_of"] or "unavailable")
    order = {"BUY": 0, "SELL": 1, "BUY-watch": 2, "SELL-watch": 3, "NEUTRAL": 4, "WITHHELD": 5}
    out = out.assign(_rank=out["signal"].map(order)).sort_values(["_rank", "rsi14"], na_position="last").drop(columns="_rank")
    def write(frame, path):
        header = "# oslo-screener report=" + path + " " + " ".join(f"{k}={v}" for k, v in metadata.items())
        content = header + "\n# columns=" + ",".join(frame.columns) + "\n" + frame.to_csv(index=False, lineterminator="\n")
        Path(path).write_text(content, encoding="utf-8")
        return hashlib.sha256(content.encode()).hexdigest()
    stamp = generated_at.strftime("%Y-%m-%dT%H%M%SZ")
    artifacts = {"latest.csv": out, f"report_{stamp}.csv": out,
                 "buy.csv": out[out.signal == "BUY"], "sell.csv": out[out.signal == "SELL"],
                 "watch_buy.csv": out[out.signal == "BUY-watch"], "watch_sell.csv": out[out.signal == "SELL-watch"],
                 "signals_only.csv": out[out.signal.isin(["BUY", "SELL"])]}
    health["artifacts"] = {name: write(frame, name) for name, frame in artifacts.items()}
    health["signal_counts"] = {label: int((out.signal == label).sum()) for label in order}
    health["source"] = "Yahoo Finance adjusted daily OHLC via yfinance"
    Path("health.json").write_text(json.dumps(health, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Snapshot {snapshot_id}: {health['status']}; completed session {expected}; {health['coverage']}")
    return health


# ---------- Hovedløp ----------
def run():
    cfg = load_config()
    tickers = load_tickers()
    rows = []
    fetch_started_at = datetime.now(timezone.utc)
    expected_session = last_ose_trading_day(fetch_started_at)

    for t in tickers:
        context = {"ticker": t}
        try:
            df = fetch_ohlc_single(t)
            if df is None or df.empty:
                rows.append({"ticker": t, "data_status": "missing", "note": "download_failed"})
                continue
            source_latest_date = df.index.max().date().isoformat()
            df = completed_history(df, expected_session)
            if df.empty:
                rows.append({"ticker": t, "data_status": "missing", "source_latest_date": source_latest_date,
                             "note": "no_completed_session_bars"})
                continue
            observed = df.index[-1].date()
            context.update(date=observed.isoformat(), source_latest_date=source_latest_date)
            if not all(col in df for col in ("Close", "High", "Low")):
                raise ValueError("missing_ohlc_columns")
            valid_prices = pd.Series(True, index=df.index)
            for col in ("Close", "High", "Low"):
                valid_prices &= df[col].map(finite) & (df[col] > 0)
            if valid_prices.any():
                context["last_valid_ohlc_date"] = df.index[valid_prices][-1].date().isoformat()
            if observed != expected_session:
                rows.append({**context,
                             "data_status": "stale", "note": "missing_expected_completed_session"})
                continue
            required_history = max(cfg["min_history_days"], cfg["sma50_length"],
                                   cfg["macd_slow"] + cfg["macd_signal"], 2 * cfg["adx_length"])
            if len(df) < required_history:
                rows.append({**context, "data_status": "invalid", "note": "insufficient_indicator_warmup"})
                continue
            if not valid_prices.iloc[-1]:
                bad_columns = [col for col in ("Close", "High", "Low")
                               if not finite(df[col].iloc[-1]) or df[col].iloc[-1] <= 0]
                raise ValueError("missing_or_invalid_required_session_ohlc:" + ",".join(bad_columns))
            if not valid_prices.all():
                raise ValueError("incomplete_historical_ohlc:" + df.index[~valid_prices][0].date().isoformat())

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
                **context,
                "ticker": t,
                "date": df.index[-1].date().isoformat(),
                "source_latest_date": source_latest_date,
                "data_status": "current",
                "note": "mfi_unavailable" if not finite(mfi_now) else "",
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
            rows.append({**context, "data_status": "invalid", "note": f"error: {type(e).__name__}: {e}"})

    return publish_snapshot(rows, len(tickers), fetch_started_at, datetime.now(timezone.utc))

if __name__ == "__main__":
    run()
