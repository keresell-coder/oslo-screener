"""Partial publication keeps stock-level and snapshot-level checks intact."""
import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

import screener
from market_health import evaluate_snapshot
from scripts import build_report
from scripts.prepare_publication import prepare_publication, validate_publication
from scripts.validate_snapshot import read_csv, validate_snapshot
from test_publication import NODE_READER
from test_snapshot_health import NOW, meta, row


@pytest.mark.parametrize("current,total", [(1, 10), (8, 10), (255, 293), (10, 10)])
def test_per_stock_mode_retains_valid_signals_at_any_positive_coverage(tmp_path, monkeypatch, current, total):
    monkeypatch.chdir(tmp_path)
    rows = [row(f"T{i}.OL", signal="BUY" if i % 2 else "SELL") for i in range(current)]
    rows += [dict(ticker=f"T{i}.OL", data_status="missing", note="download_failed")
             for i in range(current, total)]
    health = screener.publish_snapshot(rows, total, NOW, NOW, NOW, "test", coverage_policy="per_stock")
    assert health["coverage"]["current"] == current
    assert health["coverage"]["min_current_ratio"] == 1 / total
    assert health["status"] == ("current" if current == total else "degraded")
    assert len(health["eligible_tickers"]) == current
    assert len(health["excluded"]) == total - current
    assert len(read_csv("signals_only.csv")[0]) == current
    assert validate_snapshot(now=NOW)["coverage_policy"] == "per_stock"


def test_policy_can_be_restored_without_changing_individual_data(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rows = [row("A.OL"), dict(ticker="B.OL", data_status="missing", note="download_failed")]
    for policy, status, eligible in [("per_stock", "degraded", ["A.OL"]), ("minimum", "blocked", [])]:
        health = screener.publish_snapshot(rows, 2, NOW, NOW, NOW, "test", coverage_policy=policy)
        assert health["status"] == status and health["eligible_tickers"] == eligible
        assert validate_snapshot(now=NOW)["status"] == status


def test_partial_report_and_landing_list_each_rejected_stock(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bad = [row("STALE.OL", date="2026-09-04"), row("INVALID.OL", close=float("nan")),
           dict(ticker="MISSING.OL", data_status="missing", note="download_failed")]
    health = screener.publish_snapshot([row("GOOD.OL"), *bad], 4, NOW, NOW, NOW, "test", coverage_policy="per_stock")
    assert health["eligible_tickers"] == ["GOOD.OL"]
    assert {x["ticker"] for x in health["excluded"]} == {"STALE.OL", "INVALID.OL", "MISSING.OL"}
    assert {x["ticker"] for x in read_csv("buy.csv")[0]} == {"GOOD.OL"}
    for item in read_csv("latest.csv")[0][1:]:
        assert item["signal"] == "WITHHELD" and float(item["position_pct"]) == 0
    monkeypatch.setattr(build_report, "validate_snapshot", lambda: validate_snapshot(now=NOW))
    assert build_report.main() == 0
    prepare_publication(now=NOW)
    report = Path("summaries/latest.md").read_text()
    page = Path("index.html").read_text()
    assert "Samlet prosentkrav er midlertidig suspendert" in report
    assert "Stocks without required data (3)" in page
    for item in health["excluded"]:
        assert f"| {item['ticker']} |" in report
        assert f"<td>{item['ticker']}</td>" in page
        assert item["reason"] in report and item["reason"] in page
    assert validate_publication(now=NOW)["status"] == "degraded"


@pytest.mark.parametrize("damage", ["remove_excluded", "replace_reason", "policy"])
def test_partial_manifest_tampering_is_rejected(tmp_path, monkeypatch, damage):
    monkeypatch.chdir(tmp_path)
    health = screener.publish_snapshot([row(), dict(ticker="B.OL", data_status="missing", note="download_failed")],
                                     2, NOW, NOW, NOW, "test", coverage_policy="per_stock")
    if damage == "remove_excluded":
        health["excluded"] = []
    elif damage == "replace_reason":
        health["excluded"][0]["reason"] = "no problem"
    else:
        health["coverage_policy"] = "minimum"
    Path("health.json").write_text(json.dumps(health))
    with pytest.raises(ValueError, match="health/(excluded|coverage_policy)"):
        validate_snapshot(now=NOW)


@pytest.mark.parametrize("rows,changes", [
    ([row(date="2026-09-04")], {}),
    ([row(close=float("inf"))], {}),
    ([dict(ticker="A.OL", data_status="missing")], {}),
    ([row(), row()], {"universe_count": 2, "min_coverage_ratio": .5}),
    ([row()], {"generated_at": "2026-09-09T12:00:00+02:00"}),
    ([row()], {"expected_session": "2026-09-04"}),
    ([row()], {"coverage_policy": "unknown"}),
    ([row()], {"min_coverage_ratio": 0}),
    ([row()], {"min_coverage_ratio": .5}),
])
def test_partial_policy_never_promotes_invalid_or_empty_snapshots(rows, changes):
    metadata = meta(coverage_policy="per_stock", min_coverage_ratio=1)
    metadata.update(changes)
    health = evaluate_snapshot(rows, metadata, NOW)
    assert health["status"] == "blocked"
    assert health["eligible_tickers"] == [] and not health["actionable"]


def test_runtime_uses_requested_policy_from_config(tmp_path, monkeypatch):
    class Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz) if tz else NOW
    dates = pd.bdate_range(end="2026-09-08", periods=100)
    prices = [100 + i * .1 for i in range(100)]
    frame = pd.DataFrame(dict(Close=prices, High=[x + 1 for x in prices],
                             Low=[x - 1 for x in prices], Volume=1000), index=dates)
    monkeypatch.chdir(tmp_path)
    Path("config.yaml").write_text("coverage_policy: per_stock\n")
    monkeypatch.setattr(screener, "datetime", Frozen)
    monkeypatch.setattr(screener, "load_tickers", lambda: ["GOOD.OL", "MISSING.OL"])
    monkeypatch.setattr(screener, "fetch_ohlc_single", lambda symbol: frame if symbol == "GOOD.OL" else None)
    health = screener.run()
    assert health["status"] == "degraded" and health["eligible_tickers"] == ["GOOD.OL"]
    assert validate_snapshot(now=NOW)["coverage_policy"] == "per_stock"


def test_temporary_configuration_is_explicit_and_default_is_unchanged(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    assert screener.load_config(root / "config.yaml")["coverage_policy"] == "per_stock"
    monkeypatch.chdir(tmp_path)
    assert screener.load_config()["coverage_policy"] == "minimum"
    Path("config.yaml").write_text("coverage_policy: typo\n")
    with pytest.raises(ValueError, match="coverage_policy"):
        screener.load_config()


@pytest.mark.parametrize("policy,expected", [("per_stock", "degraded"), ("minimum", "degraded"), ("unknown", "blocked")])
def test_rendered_reader_accepts_partial_contract_and_rejects_unknown_policy(tmp_path, monkeypatch, policy, expected):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is installed in CI")
    monkeypatch.chdir(tmp_path)
    health = screener.publish_snapshot([row(), dict(ticker="B.OL", data_status="missing")],
                                      2, NOW, NOW, NOW, "test", coverage_policy="per_stock")
    monkeypatch.setattr(build_report, "validate_snapshot", lambda: validate_snapshot(now=NOW))
    assert build_report.main() == 0
    prepare_publication(now=NOW)
    script = re.search(r"<script>([\s\S]*?)</script>", Path("index.html").read_text()).group(1)
    if policy == "minimum":
        health.pop("coverage_policy")  # older readers already support the effective ratio
    else:
        health["coverage_policy"] = policy
    result = subprocess.run([node, "-e", NODE_READER],
        input=json.dumps(dict(script=script, health=health, now=NOW.isoformat(), mode="current")),
        text=True, capture_output=True, check=True, timeout=10)
    assert json.loads(result.stdout)["status"] == expected
