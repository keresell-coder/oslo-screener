"""Replay good and deteriorated publications without contacting a price source."""
import datetime as dt
import json
from pathlib import Path
import subprocess

import pytest

import screener
from scripts import build_report
from scripts.prepare_publication import prepare_publication, publication_files
from scripts.publication_policy import capture_published, choose_publication
from scripts.validate_snapshot import validate_snapshot

EVENING = dt.datetime.fromisoformat("2026-09-21T21:00:00+02:00")
MORNING = dt.datetime.fromisoformat("2026-09-22T05:00:00+02:00")
AFTER_CLOSE = dt.datetime.fromisoformat("2026-09-22T21:00:00+02:00")


def make_snapshot(root, current, at, monkeypatch, *, prefix="A", source=None):
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(root)
    session = screener.last_ose_trading_day(at).isoformat()
    rows = [dict(ticker=f"{prefix}{i}.OL", date=session, data_status="current", signal="BUY",
                 close=100, rsi14=30, rsi_dir=1, macd_hist=.1, sma50=105,
                 pct_above_sma50=-4.76, adx14=24, rsi6=25, mfi14=30,
                 stop_loss_pct=3, position_pct=3, primary_count=3, risk="MODERATE")
            if i < current else dict(ticker=f"{prefix}{i}.OL", data_status="missing", note="download_failed")
            for i in range(20)]
    screener.publish_snapshot(rows, 20, at, at, at)
    monkeypatch.setattr(build_report, "validate_snapshot", lambda: validate_snapshot(now=at))
    assert build_report.main() == 0
    health = prepare_publication(now=at)
    if source:
        health["source"] = source
        for directory in (root, root / "site"):
            (directory / "health.json").write_text(json.dumps(health))
    return health


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def published_report(tmp_path, monkeypatch, current=20):
    root = tmp_path / "repo"
    health = make_snapshot(root, current, EVENING, monkeypatch)
    (root / "config.yaml").write_text("min_history_days: 60\n")
    git(root, "init", "-q")
    git(root, "add", "--", "config.yaml", *publication_files(health))
    git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "Published report")
    baseline = tmp_path / "previous"
    capture_published(root, baseline)
    return root, baseline


@pytest.mark.parametrize("new_current", [16, 19])
def test_worse_retry_keeps_valid_report_and_does_not_modify_either_bundle(tmp_path, monkeypatch, new_current):
    root, prior = published_report(tmp_path, monkeypatch)
    make_snapshot(root, new_current, MORNING, monkeypatch)
    old_bytes = (prior / "health.json").read_bytes()
    new_bytes = (root / "health.json").read_bytes()
    decision = choose_publication(root, prior, now=MORNING)
    assert decision["publish"] is False
    assert decision["reason"] == "retain_valid_same_session_snapshot"
    assert decision["previous_current"] == 20
    assert decision["candidate_current"] == new_current
    assert (prior / "health.json").read_bytes() == old_bytes
    assert (root / "health.json").read_bytes() == new_bytes


@pytest.mark.parametrize("old_current,new_current", [(19, 20), (20, 20), (16, 17)])
def test_better_equal_or_previously_blocked_report_is_published(tmp_path, monkeypatch, old_current, new_current):
    root, prior = published_report(tmp_path, monkeypatch, old_current)
    make_snapshot(root, new_current, MORNING, monkeypatch)
    assert choose_publication(root, prior, now=MORNING)["publish"] is True


def test_previous_session_cannot_be_kept_after_its_expiry(tmp_path, monkeypatch):
    root, prior = published_report(tmp_path, monkeypatch)
    make_snapshot(root, 16, AFTER_CLOSE, monkeypatch)
    assert choose_publication(root, prior, now=AFTER_CLOSE)["publish"] is True


@pytest.mark.parametrize("change", ["config", "new_fetcher", "universe", "source", "threshold"])
def test_changed_report_contract_cannot_preserve_old_signals(tmp_path, monkeypatch, change):
    root, prior = published_report(tmp_path, monkeypatch)
    if change == "threshold":
        monkeypatch.setenv("MIN_CURRENT_COVERAGE", "0.95")
    make_snapshot(root, 18, MORNING, monkeypatch,
                  prefix="B" if change == "universe" else "A",
                  source="different source" if change == "source" else None)
    if change == "config":
        (root / "config.yaml").write_text("min_history_days: 120\n")
    if change == "new_fetcher":
        (root / "yahoo_history.py").write_text("# new historical validation\n")
    decision = choose_publication(root, prior, now=MORNING)
    assert decision["publish"] is True
    assert decision["prior_not_retained"]


@pytest.mark.parametrize("damage", ["missing", "tampered", "bad_json", "missing_context"])
def test_unverifiable_prior_does_not_hide_a_new_blocked_report(tmp_path, monkeypatch, damage):
    root, prior = published_report(tmp_path, monkeypatch)
    make_snapshot(root, 16, MORNING, monkeypatch)
    if damage == "missing":
        (prior / "latest.csv").unlink()
    elif damage == "tampered":
        (prior / "summaries/latest.md").write_text("untrusted replacement")
    elif damage == "bad_json":
        (prior / "health.json").write_text("{")
    else:
        (prior / "policy-context.json").unlink()
    assert choose_publication(root, prior, now=MORNING)["publish"] is True


def test_invalid_candidate_is_never_approved(tmp_path, monkeypatch):
    root, prior = published_report(tmp_path, monkeypatch)
    make_snapshot(root, 16, MORNING, monkeypatch)
    (root / "latest.csv").write_text("invalid")
    with pytest.raises((ValueError, KeyError)):
        choose_publication(root, prior, now=MORNING)


def test_capture_reads_committed_artifacts_and_original_producer_inputs(tmp_path, monkeypatch):
    root, prior = published_report(tmp_path, monkeypatch)
    original = (prior / "health.json").read_bytes()
    (root / "health.json").write_text("uncommitted download")
    (root / "config.yaml").write_text("min_history_days: 120\n")
    # The latest code commit is newer than the report, so using HEAD's input
    # hash would incorrectly certify the old result under the changed rules.
    git(root, "add", "config.yaml")
    git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "Changed rules without refreshing report")
    recaptured = tmp_path / "recaptured"
    capture_published(root, recaptured)
    assert (recaptured / "health.json").read_bytes() == original
    assert json.loads((recaptured / "policy-context.json").read_text())["input_digest"] == json.loads(
        (prior / "policy-context.json").read_text())["input_digest"]
    make_snapshot(root, 16, MORNING, monkeypatch)
    assert choose_publication(root, recaptured, now=MORNING)["publish"] is True


def test_no_prior_publication_is_a_publishable_first_run(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    prior = tmp_path / "prior"
    capture_published(root, prior)
    make_snapshot(root, 20, MORNING, monkeypatch)
    assert choose_publication(root, prior, now=MORNING)["publish"] is True


def test_workflow_never_commits_or_deploys_retained_or_branch_attempts():
    import yaml
    workflow = yaml.safe_load((Path(__file__).resolve().parents[1] / ".github/workflows/daily.yml").read_text())
    job = workflow["jobs"]["run"]
    steps = job["steps"]
    commit = next(s for s in steps if s["name"].startswith("Commit the complete"))
    upload = next(s for s in steps if s["name"] == "Upload site artifact")
    for step in [commit, upload]:
        assert "github.ref == 'refs/heads/main'" in step["if"]
        assert "steps.publication.outputs.publish == 'true'" in step["if"]
    assert "git pull" not in commit["run"] and "--force" not in commit["run"]
    deploy = workflow["jobs"]["deploy"]
    assert "github.ref == 'refs/heads/main'" in deploy["if"]
    assert "needs.run.outputs.publish == 'true'" in deploy["if"]
    assert job["outputs"]["publish"] == "${{ steps.publication.outputs.publish }}"
    assert workflow["jobs"]["source-health"]["if"] == "needs.run.outputs.data_status == 'blocked'"
