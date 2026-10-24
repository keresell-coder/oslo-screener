"""Keep a still-valid report when a later download for its session deteriorates."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.validate_snapshot import read_csv, validate_snapshot

# A report produced with different prices, rules, dependencies or universe must
# not override a new result merely because its old health percentage was higher.
INPUTS = (
    "screener.py", "yahoo_history.py", "euronext_daily.py", "market_health.py",
    "config.yaml", "universe.yaml", "tickers.txt", "valid_tickers.txt",
    "instruments.csv", "requirements.txt", "scripts/build_report.py",
    "scripts/validate_snapshot.py", "scripts/prepare_publication.py",
    "templates/landing.html",
)


def git_bytes(directory, *args):
    return subprocess.check_output(["git", *args], cwd=directory, stderr=subprocess.PIPE)


def input_digest(directory, revision=None):
    digest = hashlib.sha256()
    for name in INPUTS:
        try:
            value = (git_bytes(directory, "show", f"{revision}:{name}") if revision
                     else (Path(directory) / name).read_bytes())
        except (FileNotFoundError, subprocess.CalledProcessError):
            value = b"<absent>"
        digest.update(name.encode() + b"\0" + hashlib.sha256(value).digest())
    return digest.hexdigest()


def capture_published(directory, destination):
    """Copy only the committed publication, before any fetch changes its files."""
    directory, destination = Path(directory), Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        health = json.loads(git_bytes(directory, "show", "HEAD:health.json"))
        revision = git_bytes(directory, "log", "-1", "--format=%H", "--", "health.json").decode().strip()
        if not revision:
            raise ValueError("no recorded publication commit")
        for name in ["health.json", *health["artifacts"]]:
            target = destination / name
            if target.resolve().parent not in (destination.resolve(), (destination / "summaries").resolve()):
                raise ValueError("unexpected artifact path")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git_bytes(directory, "show", f"HEAD:{name}"))
        context = {"publication_commit": revision, "input_digest": input_digest(directory, revision)}
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        context = {"unavailable": type(error).__name__}
    (destination / "policy-context.json").write_text(json.dumps(context) + "\n")


def choose_publication(candidate, published, *, now=None):
    candidate, published = Path(candidate), Path(published)
    now = now or dt.datetime.now(dt.timezone.utc)
    # A broken candidate is never publishable, even if a prior report exists.
    new = validate_snapshot(candidate, require_report=True, require_landing=True, now=now)
    result = {"publish": True, "reason": "publish_new_snapshot", "candidate_status": new["status"],
              "expected_session": new["expected_session"], "candidate_snapshot_id": new["snapshot_id"],
              "candidate_current": new["coverage"]["current"]}
    try:
        context = json.loads((published / "policy-context.json").read_text())
        old = validate_snapshot(published, require_report=True, require_landing=True, now=now)
        if not old["actionable"] or old["status"] not in ("current", "degraded"):
            raise ValueError("previous report is blocked")
        if context.get("input_digest") != input_digest(candidate):
            raise ValueError("report inputs changed")
        previous_rows, _ = read_csv(published / "latest.csv")
        new_rows, _ = read_csv(candidate / "latest.csv")
        if {r["ticker"] for r in previous_rows} != {r["ticker"] for r in new_rows}:
            raise ValueError("universe changed")
        if (old["source"] != new["source"] or old["expected_session"] != new["expected_session"]
                or old["coverage"]["min_current_ratio"] != new["coverage"]["min_current_ratio"]):
            raise ValueError("source, session or coverage policy changed")
    except (ValueError, KeyError, OSError, TypeError) as error:
        return {**result, "prior_not_retained": str(error)}
    result.update(previous_snapshot_id=old["snapshot_id"], previous_current=old["coverage"]["current"])
    if new["status"] == "blocked" or new["coverage"]["current"] < old["coverage"]["current"]:
        result.update(publish=False, reason="retain_valid_same_session_snapshot")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--published", type=Path)
    parser.add_argument("--output", type=Path, default=Path("publication-decision.json"))
    args = parser.parse_args()
    if bool(args.capture) == bool(args.published):
        parser.error("choose exactly one of --capture or --published")
    if args.capture:
        capture_published(Path.cwd(), args.capture)
        return
    decision = choose_publication(Path.cwd(), args.published)
    args.output.write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write("publish=" + str(decision["publish"]).lower() + "\n")
    if not decision["publish"]:
        print("::warning::Download quality deteriorated; retaining the validated report for "
              + decision["expected_session"] + ". Commit and Pages deployment are skipped.")


if __name__ == "__main__":
    main()
