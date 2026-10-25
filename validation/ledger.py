"""Append-only manual observation import. No fetching, signal calculation or outcomes."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, date
import hashlib
import io
import json
from math import isfinite
import tempfile
import os
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = "oslo.validation.pilot.v1"
DAILY_SURFACE = "https://keresell-coder.github.io/oslo-screener/latest.csv"
DAILY_STATES = {"BUY", "SELL", "BUY-watch", "SELL-watch", "NEUTRAL", "WITHHELD"}
WEEKLY_STATES = {"qualified", "near", "watch", "rejected", "unreviewed", "unavailable"}
WEEKLY_COHORT = "weekly-2026-10-25"


class IntegrityError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        raise IntegrityError("timestamp must be an explicit timezone-aware string")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.utcoffset() is None:
            raise ValueError()
        return result
    except ValueError as exc:
        raise IntegrityError("invalid or timezone-naive timestamp") from exc


def day(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise IntegrityError("invalid session/date") from exc


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def check_hash(value):
    require(isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value), "invalid SHA256")


def read(ledger):
    """Verify chain, content addresses, sequence, and byte-for-byte trailing newline."""
    root = Path(ledger)
    records = []
    journal = root / "observations.jsonl"
    if not journal.exists():
        return records
    raw = journal.read_bytes()
    require(not raw or raw.endswith(b"\n"), "truncated journal")
    previous = None
    for index, line in enumerate(raw.splitlines(), 1):
        try:
            record = json.loads(line)
            checksum = record.pop("record_hash")
        except (ValueError, KeyError, TypeError) as exc:
            raise IntegrityError("invalid journal record") from exc
        require(record["sequence"] == index and record["previous_hash"] == previous, "broken journal order")
        require(digest(canonical(record)) == checksum, "journal checksum mismatch")
        for key in ("artifact_sha256", "manifest_sha256", "report_sha256"):
            if record.get(key) is None:
                continue
            value = record[key]
            check_hash(value)
            blob = root / "blobs" / value
            require(blob.is_file() and digest(blob.read_bytes()) == value, "missing or changed source blob")
        record["record_hash"] = checksum
        records.append(record)
        previous = checksum
    return records


def parse(manifest, artifact):
    """Validate caller attestations, retain originals; never infer availability."""
    require(manifest.get("schema") == SCHEMA, "unsupported import schema")
    require(manifest.get("kind") in {"daily", "weekly"}, "invalid observation kind")
    observed = timestamp(manifest.get("observed_at"))
    require(digest(artifact) == manifest.get("artifact_sha256"), "source artifact checksum mismatch")
    for field in ("source_url", "economic_method", "method_version", "schema_version", "availability_evidence", "universe", "code_revision", "source_cutoff", "source_published_at", "available_at", "identities"):
        require(field in manifest, f"missing provenance field: {field}; use explicit null for unknown")
    require(isinstance(manifest["source_url"], str) and manifest["source_url"].startswith("https://"), "canonical HTTPS source required")
    require(manifest["economic_method"] and manifest["method_version"] and manifest["schema_version"], "method identity required")
    available = manifest["available_at"]
    if available is not None:
        require(timestamp(available) <= observed, "availability after capture")
        require(isinstance(manifest["availability_evidence"], str) and manifest["availability_evidence"].strip(), "known availability requires evidence")
    for field in ("source_cutoff", "source_published_at"):
        if manifest[field] is not None:
            t = timestamp(manifest[field])
            require(t <= observed, f"future {field}")
            if available is not None:
                require(t <= timestamp(available), f"{field} after availability")
    identities = manifest["identities"]
    require(isinstance(identities, dict), "identities must be an explicit mapping")
    if manifest["kind"] == "daily":
        require(manifest["source_url"] == DAILY_SURFACE, "daily primary surface is the pinned producer CSV")
        require(manifest["economic_method"] == manifest["method_version"], "daily economic method must match the pinned CSV methodology")
        source_session = manifest.get("source_session")
        require(day(source_session) <= observed.astimezone(ZoneInfo("Europe/Oslo")).date(), "future source session")
        if available is not None:
            require(day(source_session) <= timestamp(available).astimezone(ZoneInfo("Europe/Oslo")).date(), "source session after availability")
        text = artifact.decode("utf-8-sig")
        lines = text.splitlines()
        metadata = dict(part.split("=", 1) for line in lines if line.startswith("#") for part in line.split() if "=" in part)
        require(metadata.get("expected_session") == source_session, "CSV session missing or conflicts with manifest")
        require(metadata.get("methodology_version") == manifest["method_version"], "CSV method missing or conflicts with manifest")
        rows = list(csv.DictReader(io.StringIO("\n".join(line for line in lines if not line.startswith("#")))))
        require(bool(rows), "empty daily artifact")
        for row in rows:
            require(row.get("ticker") and row.get("signal") in DAILY_STATES, "invalid daily ticker/classification")
            usable = row.get("data_status") == "current" and row.get("date") == source_session and row["signal"] != "WITHHELD"
            if row["signal"] != "WITHHELD":
                require(usable, "non-withheld stale/missing daily row")
                try:
                    close, rsi = float(row["close"]), float(row["rsi14"])
                    require(isfinite(close) and close > 0 and isfinite(rsi) and 0 <= rsi <= 100, "invalid current price/RSI")
                except (KeyError, TypeError, ValueError) as exc:
                    raise IntegrityError("current row missing usable price/RSI") from exc
            row["_usable"] = usable
            row["_security"] = row["ticker"]
    else:
        require(day(manifest.get("run_date")) <= observed.astimezone(ZoneInfo("Europe/Oslo")).date(), "future weekly run")
        if available is not None:
            require(day(manifest["run_date"]) <= timestamp(available).astimezone(ZoneInfo("Europe/Oslo")).date(), "weekly run after availability")
        if manifest["method_version"] in {"2.1.0", "2.1.1"}:
            require(manifest["economic_method"] == WEEKLY_COHORT, "2.1.1 documentation does not restart October 25 cohort")
        rows = json.loads(artifact)
        require(isinstance(rows, list) and bool(rows), "weekly artifact must be nonempty frozen case array")
        for row in rows:
            require(row.get("security") and row.get("status") in WEEKLY_STATES, "invalid weekly security/status")
            require(row.get("watch_scope") if row["status"] == "watch" else True, "watch scope required")
            require(row.get("reason") if row["status"] in {"rejected", "unavailable"} else True, "rejection/unavailable reason required")
            row["_security"] = row["security"]
            row["_usable"] = True
    require(len({r["_security"] for r in rows}) == len(rows), "duplicate security in one artifact")
    return rows


def append(ledger, manifest, artifact, report=None):
    """Single-writer transaction; reject chronological backfill instead of replacing originals."""
    rows = parse(manifest, artifact)
    if manifest["kind"] == "weekly":
        require(report is not None and digest(report) == manifest.get("report_sha256"), "weekly delivered report bytes/hash required")
    root = Path(ledger)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".writer.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise IntegrityError("single writer required; inspect stale lock manually") from exc
    try:
        os.close(fd)
        records = read(root)
        manifest_bytes = canonical(manifest)
        manifest_sha = digest(manifest_bytes)
        old = {r["observation_id"]: r for r in records}
        pending = []
        resolved_groups = set()
        for row in rows:
            security = row.pop("_security")
            usable = row.pop("_usable")
            identity = manifest["identities"].get(security)
            require(identity is None or (identity.get("isin") and identity.get("share_class")), "partial security identity")
            security_key = canonical({"isin": identity["isin"], "share_class": identity["share_class"]}).decode() if identity else "unverified-symbol:" + security
            scope = manifest.get("source_session") if manifest["kind"] == "daily" else manifest.get("episode", "first")
            group = [manifest["kind"], security_key, scope, manifest["economic_method"]]
            group_key = canonical(group)
            require(group_key not in resolved_groups, "duplicate resolved security group in one artifact")
            resolved_groups.add(group_key)
            obs_id = digest(canonical([group, manifest["artifact_sha256"], security, manifest.get("run_date")]))
            provenance_parent = None
            links = manifest.get("provenance_revisions", {})
            require(isinstance(links, dict), "provenance_revisions must be a mapping")
            if security in links:
                require(obs_id in old and links[security] == obs_id and manifest.get("revision_reason"), "invalid provenance revision link")
            if obs_id in old:
                if old[obs_id]["manifest_sha256"] == manifest_sha:
                    continue
                provenance_parent = manifest.get("provenance_revisions", {}).get(security)
                require(provenance_parent == obs_id and manifest.get("revision_reason"), "same artifact has conflicting provenance; explicit provenance_revisions link/reason required")
                obs_id = digest(canonical([provenance_parent, manifest_sha]))
                if obs_id in old:
                    continue
            require(not any(r["kind"] == manifest["kind"] and r["security"] == security and r["group"][2:] == group[2:] and r["group"][1] != security_key for r in records), "identity changed within event/episode; reconcile in a separate audited ledger")
            siblings = [r for r in records if r["group"] == group]
            if manifest["kind"] == "weekly" and not siblings and scope != "first":
                prior = old.get(manifest.get("reentry_of"))
                require(prior is not None and prior["role"] == "original" and prior["group"][1] == security_key and prior["economic_method"] == manifest["economic_method"] and manifest.get("revision_reason"), "re-entry requires linked prior original and reason")
            availability = manifest["available_at"]
            known = [timestamp(r["available_at"]) for r in siblings if r["available_at"] is not None]
            if availability is not None and known:
                require(timestamp(availability) >= max(known), "out-of-order publication: rebuild a separate ledger chronologically; original unchanged")
            if siblings:
                require(manifest.get("revision_reason"), "same-group follow-up requires revision reason")
                require(availability is None or not any(r["available_at"] is not None and timestamp(r["available_at"]) == timestamp(availability) and r["artifact_sha256"] != manifest["artifact_sha256"] for r in siblings), "ambiguous equal-time publications")
            original = next((r for r in siblings if r["role"] == "original"), None)
            timing_ambiguous = any(r["usable"] and r["available_at"] is None for r in siblings)
            if provenance_parent:
                role = "provenance_revision"
            elif not usable:
                role = "withheld"
            elif availability is None or timing_ambiguous:
                role = "timing_unverified"
            elif original:
                role = "revision" if manifest["kind"] == "daily" else "followup"
            else:
                role = "original"
            status = row["signal"] if manifest["kind"] == "daily" else row["status"]
            record = {"schema": SCHEMA, "observation_id": obs_id, "kind": manifest["kind"], "group": group,
                      "security": security, "identity": identity, "identity_status": "provided_not_authenticated" if identity else "unverified",
                      "artifact_sha256": manifest["artifact_sha256"], "manifest_sha256": manifest_sha, "report_sha256": manifest.get("report_sha256"),
                      "reentry_of": manifest.get("reentry_of"), "provenance_revision_of": provenance_parent,
                      "overlap_group": digest(canonical([manifest["kind"], security_key, manifest["economic_method"]])),
                      "available_at": availability, "observed_at": manifest["observed_at"], "source_url": manifest["source_url"],
                      "method_version": manifest["method_version"], "economic_method": manifest["economic_method"],
                      "run_date": manifest.get("run_date"), "source_session": manifest.get("source_session"),
                      "classification": status, "usable": usable, "role": role,
                      "original_id": original["observation_id"] if original else (obs_id if role == "original" else None),
                      "previous_observation_id": siblings[-1]["observation_id"] if siblings else None,
                      "revision_reason": manifest.get("revision_reason"), "row": row}
            pending.append(record)
        if not pending:
            return {"appended": 0, "records": len(records)}
        # All input checks precede writes; orphan blobs after an interrupted append are harmless.
        blobs = root / "blobs"
        blobs.mkdir(exist_ok=True)
        for value in (artifact, manifest_bytes, *([report] if report is not None else [])):
            destination = blobs / digest(value)
            if destination.exists():
                require(destination.read_bytes() == value, "source blob changed")
            else:
                with destination.open("xb") as stream:
                    stream.write(value)
                    stream.flush()
                    os.fsync(stream.fileno())
        previous = records[-1]["record_hash"] if records else None
        for record in pending:
            record["sequence"] = len(records) + 1
            record["previous_hash"] = previous
            record["record_hash"] = digest(canonical(record))
            previous = record["record_hash"]
            records.append(record)
        with (root / "observations.jsonl").open("ab") as stream:
            stream.write(b"".join(canonical(r) + b"\n" for r in pending))
            stream.flush()
            os.fsync(stream.fileno())
        return {"appended": len(pending), "records": len(records)}
    finally:
        lock.unlink()


def audit(ledger):
    records = read(ledger)
    # Replay immutable imports to verify roles, links, raw rows and chronology.
    with tempfile.TemporaryDirectory(prefix="oslo-pilot-audit-") as temporary:
        seen = set()
        for record in records:
            key = record["manifest_sha256"]
            if key in seen:
                continue
            seen.add(key)
            blobs = Path(ledger) / "blobs"
            manifest = json.loads((blobs / key).read_bytes())
            report = (blobs / record["report_sha256"]).read_bytes() if record.get("report_sha256") else None
            append(temporary, manifest, (blobs / record["artifact_sha256"]).read_bytes(), report)
        require(read(temporary) == records, "journal does not reproduce immutable imports")
    counts = {}
    for r in records:
        key = r["kind"] + ":" + r["role"] + ":" + r["classification"]
        counts[key] = counts.get(key, 0) + 1
    return {"schema": SCHEMA, "records": len(records), "counts": counts,
            "unverified_identity_records": sum(r["identity"] is None for r in records),
            "timing_ambiguous_groups": len({canonical(r["group"]) for r in records if r["usable"] and r["available_at"] is None}),
            "primary_interpretation": "blocked for groups with unknown usable-publication timing; identity/provenance independently required",
            "outcomes": "not collected; no profitability or execution claim"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["import", "audit"])
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--report", type=Path, help="weekly delivered report bytes")
    args = parser.parse_args()
    try:
        if args.command == "import":
            require(args.manifest and args.artifact, "import requires manifest and artifact")
            result = append(args.ledger, json.loads(args.manifest.read_text()), args.artifact.read_bytes(), args.report.read_bytes() if args.report else None)
        else:
            result = audit(args.ledger)
        print(json.dumps(result, indent=2, sort_keys=True))
    except (IntegrityError, OSError, ValueError) as exc:
        parser.exit(2, f"pilot integrity failure: {exc}\n")


if __name__ == "__main__":
    main()
