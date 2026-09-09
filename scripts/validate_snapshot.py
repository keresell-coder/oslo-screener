"""Validate the complete publish bundle, including empty category files and reports."""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from market_health import evaluate_snapshot, parse_metadata

CATEGORIES = {"buy.csv": {"BUY"}, "sell.csv": {"SELL"}, "watch_buy.csv": {"BUY-watch"},
              "watch_sell.csv": {"SELL-watch"}, "signals_only.csv": {"BUY", "SELL"}}


def read_csv(path):
    text = Path(path).read_text(encoding="utf-8")
    rows = list(csv.DictReader(line for line in text.splitlines() if not line.startswith("#")))
    return rows, parse_metadata(text)


def validate_snapshot(directory=Path("."), *, require_report=False, require_landing=False, now=None):
    directory = Path(directory)
    health = json.loads((directory / "health.json").read_text())
    rows, metadata = read_csv(directory / "latest.csv")
    checked = evaluate_snapshot(rows, metadata, now)
    for key in ("schema", "snapshot_id", "generated_at", "valid_until", "status", "actionable",
                "market_data_as_of", "expected_session", "coverage", "reasons", "eligible_tickers"):
        if checked[key] != health[key]:
            raise ValueError(f"health/{key} does not match verified CSV observations")
    mandatory = {"latest.csv", *CATEGORIES}
    if require_report:
        mandatory.add("summaries/latest.md")
    if require_landing:
        mandatory.update({"index.html", ".nojekyll"})
    if not mandatory.issubset(health.get("artifacts", {})):
        raise ValueError("incomplete artifact manifest")
    for name, expected_hash in health["artifacts"].items():
        path = directory / name
        if path.resolve().parent != directory.resolve() and path.resolve().parent != (directory / "summaries").resolve():
            raise ValueError("unexpected artifact path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"artifact checksum mismatch: {name}")
    for name, labels in CATEGORIES.items():
        subset, submeta = read_csv(directory / name)
        if submeta.get("snapshot_id") != health["snapshot_id"]:
            raise ValueError(f"snapshot mismatch: {name}")
        expected = [row for row in rows if row["signal"] in labels]
        if subset != expected:
            raise ValueError(f"stale or inconsistent category: {name}")
    counts = Counter(row["signal"] for row in rows)
    if any(counts[label] != count for label, count in health["signal_counts"].items()):
        raise ValueError("signal count mismatch")
    allowed = set(checked["eligible_tickers"])
    if any(row["signal"] not in ("NEUTRAL", "WITHHELD") and row["ticker"] not in allowed for row in rows):
        raise ValueError("noncurrent row has an actionable signal")
    if require_report and f"snapshot_id={health['snapshot_id']}" not in (directory / "summaries/latest.md").read_text():
        raise ValueError("report snapshot mismatch")
    if require_landing and f"snapshot_id={health['snapshot_id']}" not in (directory / "index.html").read_text():
        raise ValueError("landing page snapshot mismatch")
    return health


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-report", action="store_true")
    parser.add_argument("--allow-blocked", action="store_true", help="Validate safe blocked publication; health remains blocked")
    args = parser.parse_args()
    try:
        health = validate_snapshot(require_report=args.require_report)
    except (ValueError, KeyError, OSError) as exc:
        sys.exit(f"Snapshot validation failed: {exc}")
    print(health["status"])
    if health["status"] == "blocked" and not args.allow_blocked:
        sys.exit("Source health blocked: " + ", ".join(health["reasons"]))
