"""Prepare and stage the same complete snapshot for branch and artifact Pages."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.validate_snapshot import validate_snapshot


def publication_files(health):
    """Only these exact files may enter the generated-data commit."""
    return ["health.json", *sorted(health["artifacts"])]


def tracked_archives(directory):
    result = subprocess.run(["git", "ls-files", "-z", "--", "report_*.csv", "summaries/*.md"],
                            cwd=directory, capture_output=True, check=False)
    if result.returncode:
        if (Path(directory) / ".git").exists():
            raise ValueError("Cannot read the tracked archive inventory")
        return []  # A standalone, not-yet-staged snapshot can still be prepared.
    return [name for name in result.stdout.decode().split("\0") if name]


def archive_bytes(directory, name):
    # Read the Git index, not unrelated working-tree modifications. The current
    # manifest is copied separately from its verified newly generated files.
    return subprocess.check_output(["git", "show", f":{name}"], cwd=directory)


def validate_publication(directory=Path("."), *, now=None):
    directory = Path(directory)
    health = validate_snapshot(directory, require_report=True, require_landing=True, now=now)
    validate_snapshot(directory / "site", require_report=True, require_landing=True, now=now)
    for name in publication_files(health):
        if (directory / name).read_bytes() != (directory / "site" / name).read_bytes():
            raise ValueError(f"branch/artifact publication mismatch: {name}")
    for name in set(tracked_archives(directory)) - set(publication_files(health)):
        if (directory / "site" / name).read_bytes() != archive_bytes(directory, name):
            raise ValueError(f"branch/artifact archive mismatch: {name}")
    return health


def prepare_publication(directory=Path("."), *, now=None):
    directory = Path(directory)
    health = validate_snapshot(directory, require_report=True, now=now)
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]))
    page = env.get_template("landing.html").render(health=health)
    (directory / "index.html").write_text(page, encoding="utf-8")
    (directory / ".nojekyll").write_bytes(b"")
    for name in ("index.html", ".nojekyll"):
        health["artifacts"][name] = hashlib.sha256((directory / name).read_bytes()).hexdigest()
    (directory / "health.json").write_text(json.dumps(health, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for name in set(tracked_archives(directory)) - set(publication_files(health)):
        destination = directory / "site" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive_bytes(directory, name))
    for name in publication_files(health):
        destination = directory / "site" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(directory / name, destination)
    return validate_publication(directory, now=now)


def stage_publication(directory=Path("."), *, now=None):
    directory = Path(directory)
    health = validate_publication(directory, now=now)
    # Timestamp CSVs are ignored for ordinary local runs. Force-add only this
    # verified manifest, never a report_*.csv or summaries/*.md wildcard.
    subprocess.run(["git", "add", "--force", "--", *publication_files(health)], cwd=directory, check=True)
    return health


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--stage", action="store_true")
    args = parser.parse_args()
    try:
        action = stage_publication if args.stage else validate_publication if args.verify else prepare_publication
        print(action()["status"])
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit(f"Publication validation failed: {exc}")
