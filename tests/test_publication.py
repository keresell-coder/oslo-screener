"""Exercise the real branch bundle and rendered reader health guard."""
import copy
import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import screener
from scripts import build_report
from scripts.prepare_publication import prepare_publication, publication_files, stage_publication, validate_publication
from scripts.validate_snapshot import validate_snapshot

NOW = dt.datetime.fromisoformat("2026-09-08T18:00:00+02:00")
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    row = dict(ticker="A.OL", date="2026-09-08", data_status="current", signal="BUY",
               close=100, rsi14=30, rsi_dir=1, macd_hist=.1, sma50=105,
               pct_above_sma50=-4.76, adx14=24, rsi6=25, mfi14=30,
               stop_loss_pct=3, position_pct=3, primary_count=3, risk="MODERATE", snapshot_id="test")
    screener.publish_snapshot([row], 1, NOW, NOW, NOW, "test")
    monkeypatch.setattr(build_report, "validate_snapshot", lambda: validate_snapshot(now=NOW))
    assert build_report.main() == 0
    health = prepare_publication(now=NOW)
    return tmp_path, health


def test_git_branch_round_trip_contains_every_declared_artifact_and_same_landing(bundle):
    root, health = bundle
    (root / ".gitignore").write_text("report_*.csv\n/site\n")
    (root / "report_unrelated_old.csv").write_text("retain unrelated archive")
    (root / "summaries/unrelated_old.md").write_text("retain unrelated report")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    archived = ["report_2026-08-01T120000Z.csv", "summaries/daily_2026-08-01.md"]
    for name in archived:
        (root / name).write_text("previously published " + name)
    subprocess.run(["git", "add", "-f", "--", ".gitignore", *archived], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "archive baseline"], cwd=root, check=True)
    # A dirty historical file must not leak into the custom Pages artifact.
    (root / archived[0]).write_text("unrelated local modification")
    prepare_publication(root, now=NOW)
    stage_publication(root, now=NOW)
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=root).decode().rstrip("\0").split("\0")
    assert set(staged) == set(publication_files(health))
    timestamped = [name for name in staged if name.startswith("report_")]
    assert len(timestamped) == 1
    restored = root / "branch-deployment"
    restored.mkdir()
    subprocess.run(["git", "checkout-index", "--all", f"--prefix={restored}/"], cwd=root, check=True)
    assert validate_snapshot(restored, require_report=True, require_landing=True, now=NOW)["status"] == "current"
    for name in [*publication_files(health), *archived]:
        assert (restored / name).read_bytes() == (root / "site" / name).read_bytes()
    assert (root / "site" / archived[0]).read_text() == "previously published " + archived[0]
    assert (root / archived[0]).read_text() == "unrelated local modification"
    assert (root / "report_unrelated_old.csv").read_text() == "retain unrelated archive"
    assert (root / "summaries/unrelated_old.md").read_text() == "retain unrelated report"


@pytest.mark.parametrize("damage", ["delete", "tamper"])
def test_previously_published_archives_cannot_disappear_or_change_on_custom_pages(bundle, damage):
    root, _ = bundle
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    name = "summaries/daily_2026-08-01.md"
    (root / name).write_text("published history")
    subprocess.run(["git", "add", "--", name], cwd=root, check=True)
    prepare_publication(root, now=NOW)
    if damage == "delete":
        (root / "site" / name).unlink()
    else:
        (root / "site" / name).write_text("changed history")
    with pytest.raises((ValueError, OSError)):
        validate_publication(root, now=NOW)


@pytest.mark.parametrize("surface,artifact,damage", [
    (".", "timestamp", "delete"), ("site", "timestamp", "delete"),
    (".", "index.html", "tamper"), ("site", "index.html", "tamper"),
    ("site", "latest.csv", "tamper"), ("site", "health.json", "tamper"),
    (".", ".nojekyll", "delete"),
])
def test_incomplete_or_tampered_publication_cannot_be_staged(bundle, surface, artifact, damage):
    root, health = bundle
    if artifact == "timestamp":
        artifact = next(name for name in health["artifacts"] if name.startswith("report_"))
    target = root / surface / artifact
    if damage == "delete":
        target.unlink()
    else:
        target.write_text(target.read_text() + "tampered")
    with pytest.raises((ValueError, OSError)):
        stage_publication(root, now=NOW)


def test_prepare_rejects_missing_timestamp_before_creating_landing(bundle):
    root, health = bundle
    # Reproduce the actual legacy branch failure: manifest survives, CSV omitted.
    (root / next(name for name in health["artifacts"] if name.startswith("report_"))).unlink()
    with pytest.raises(OSError):
        prepare_publication(root, now=NOW)


@pytest.mark.parametrize("key,value", [
    ("valid_until", "2099-01-01T00:00:00Z"),
    ("generated_at", "2026-09-09T09:00:00Z"),
    ("actionable", False),
])
def test_consistently_tampered_health_cannot_extend_reader_validity(bundle, key, value):
    root, original = bundle
    health = copy.deepcopy(original)
    health[key] = value
    # Identical branch/artifact JSON is insufficient: dates and eligibility must
    # also agree with the independently checked CSV observations.
    for surface in (root, root / "site"):
        (surface / "health.json").write_text(json.dumps(health))
    with pytest.raises(ValueError, match=f"health/{key}"):
        validate_publication(root, now=NOW)


def test_workflow_prepares_root_before_commit_and_uses_one_site_bundle():
    workflow = (ROOT / ".github/workflows/daily.yml").read_text()
    assert workflow.index("run: python scripts/prepare_publication.py\n") < workflow.index("python scripts/prepare_publication.py --stage")
    assert "git add " not in workflow
    assert "summaries/*.md" not in workflow and "report_*.csv" not in workflow
    assert "Path(\"site/index.html\").write_text" not in workflow
    assert "include-hidden-files: true" in workflow


NODE_READER = r"""
const fs = require('fs');
const vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
let clock = Date.parse(input.now);
class ClockDate extends Date { static now() { return clock; } }
const nodes = {};
const intervals = {};
const pending = [];
const context = vm.createContext({
  Date: ClockDate, Number, Math, Array, Error, AbortSignal,
  document: {hidden: false, getElementById: id => nodes[id] ||= {dataset: {}, textContent: ''}, addEventListener() {}},
  setInterval: (callback, delay) => { intervals[delay] = callback; },
  fetch: input.mode === 'race' ? () => new Promise(resolve => pending.push(resolve)) :
    async () => { if (input.mode === 'failure') throw new Error('offline');
      return {ok: input.mode !== 'http_failure', json: async () => {if (input.mode === 'invalid_json') throw new Error('bad JSON'); return input.health;}}; }
});
const settle = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  vm.runInContext(input.script, context);
  if (input.mode === 'race') {
    intervals[30000]();
    pending[1]({ok: true, json: async () => ({...input.health, status: 'blocked', actionable: false})});
    await settle();
    pending[0]({ok: true, json: async () => input.health});
  }
  await settle();
  const before = nodes['health-panel'].dataset.status;
  if (input.mode === 'clock_expiry') {
    clock = Date.parse(input.health.valid_until);
    intervals[1000]();
  }
  console.log(JSON.stringify({before, status: nodes['health-panel'].dataset.status,
    label: nodes['health-status'].textContent, reason: nodes['health-reason'].textContent,
    observation: nodes.observation?.textContent}));
})();
"""


@pytest.mark.parametrize("case,expected", [
    ("current", "current"), ("blocked", "blocked"), ("expired", "blocked"),
    ("failure", "unavailable"), ("http_failure", "unavailable"), ("invalid_json", "unavailable"),
    ("wrong_snapshot", "blocked"), ("missing_expiry", "blocked"), ("future_generation", "blocked"),
    ("unknown_status", "blocked"), ("zero_coverage", "blocked"),
    ("clock_expiry", "blocked"), ("race", "blocked"),
])
def test_rendered_reader_guard_fails_closed(bundle, case, expected):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for rendered reader tests; installed by both CI workflows")
    root, original = bundle
    html = (root / "index.html").read_text()
    assert '<strong id="health-status">Not verified</strong>' in html
    assert '<dd id="observation">2026-09-08</dd>' in html
    script = re.search(r"<script>([\s\S]*?)</script>", html).group(1)
    health = copy.deepcopy(original)
    overrides = {
        "blocked": dict(status="blocked", actionable=False),
        "expired": dict(valid_until=NOW.isoformat()),
        "wrong_snapshot": dict(snapshot_id="replaced"),
        "missing_expiry": dict(valid_until=None),
        "future_generation": dict(generated_at="2026-09-09T12:00:00+02:00"),
        "unknown_status": dict(status="passing"),
        "zero_coverage": dict(coverage={"current": 0}),
    }
    health.update(overrides.get(case, {}))
    result = subprocess.run([node, "-e", NODE_READER], input=json.dumps(dict(script=script, health=health, now=NOW.isoformat(), mode=case)),
                            text=True, capture_output=True, check=True, timeout=10)
    state = json.loads(result.stdout)
    assert state["status"] == expected, state
    if case == "current":
        assert state["observation"] == "2026-09-08"
    if case == "clock_expiry":
        assert state["before"] == "current" and "expired" in state["reason"]
