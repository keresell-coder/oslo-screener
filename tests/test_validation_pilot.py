import copy
from datetime import date, timedelta
import json
import pytest
from validation.ledger import SCHEMA, DAILY_SURFACE, WEEKLY_COHORT, IntegrityError, append, audit, canonical, digest, read
from validation.conventions import reference_close, daily_endpoint, weekly_endpoint, volume_state, buy_net, sell_avoided, outcome_state


def daily(status="NEUTRAL", data_status="current", session="2026-10-23", available="2026-10-23T15:00:00Z"):
    artifact = (f"# expected_session={session} methodology_version=fixture-v1\n"
                "ticker,date,data_status,signal,close,rsi14\n" + f"NOD.OL,{session},{data_status},{status},100,40\n").encode()
    return manifest(artifact, available, session), artifact


def manifest(artifact, available, session=None):
    return {"schema": SCHEMA, "kind": "daily", "source_url": DAILY_SURFACE, "artifact_sha256": digest(artifact),
            "economic_method": "fixture-v1", "method_version": "fixture-v1", "schema_version": "fixture-v1",
            "source_session": session, "observed_at": "2026-10-25T12:00:00Z", "available_at": available,
            "availability_evidence": "synthetic fixture, not authenticated public observation" if available else None,
            "source_cutoff": None, "source_published_at": None, "universe": None, "code_revision": None, "identities": {}}


def weekly(status="near", version="2.1.0", available="2026-10-25T10:00:00Z", run_date="2026-10-25"):
    artifact = canonical([{"security": "YAR.OL", "status": status}])
    m = manifest(artifact, available)
    m.update(kind="weekly", source_url="https://example.org/synthetic-report", method_version=version,
             economic_method=WEEKLY_COHORT, run_date=run_date, report_sha256=digest(b"synthetic report"))
    return m, artifact


def test_neutral_original_not_later_buy_and_dedup(tmp_path):
    m, a = daily()
    assert append(tmp_path, m, a)["appended"] == 1
    assert append(tmp_path, m, a)["appended"] == 0
    original_bytes = (tmp_path / "observations.jsonl").read_bytes()
    m2, a2 = daily("BUY", available="2026-10-23T16:00:00Z")
    m2["revision_reason"] = "synthetic later publication"
    append(tmp_path, m2, a2)
    first, second = read(tmp_path)
    assert first["classification"] == "NEUTRAL" and first["role"] == "original"
    assert second["role"] == "revision" and second["original_id"] == first["observation_id"]
    assert (tmp_path / "observations.jsonl").read_bytes().startswith(original_bytes)


@pytest.mark.parametrize("original", ["BUY-watch", "SELL-watch", "SELL", "BUY"])
def test_all_usable_classifications_lock(tmp_path, original):
    m, a = daily(original)
    append(tmp_path, m, a)
    assert read(tmp_path)[0]["role"] == "original"


def test_withheld_then_usable_and_unknown_preserved(tmp_path):
    m, a = daily("WITHHELD", "stale", available=None)
    append(tmp_path, m, a)
    m, a = daily("BUY")
    m["revision_reason"] = "usable follow-up"
    append(tmp_path, m, a)
    first, second = read(tmp_path)
    assert first["role"] == "withheld" and first["available_at"] is None
    assert second["role"] == "original"


def test_unknown_usable_blocks_primary_chronology(tmp_path):
    m, a = daily(available=None)
    append(tmp_path, m, a)
    m, a = daily("BUY")
    m["revision_reason"] = "later known publication"
    append(tmp_path, m, a)
    assert [r["role"] for r in read(tmp_path)] == ["timing_unverified", "timing_unverified"]


def test_out_of_order_atomic_reject(tmp_path):
    m, a = daily("BUY", available="2026-10-23T16:00:00Z")
    append(tmp_path, m, a)
    before = (tmp_path / "observations.jsonl").read_bytes()
    m, a = daily(available="2026-10-23T15:00:00Z")
    m["revision_reason"] = "earlier discovered original"
    with pytest.raises(IntegrityError, match="out-of-order"):
        append(tmp_path, m, a)
    assert (tmp_path / "observations.jsonl").read_bytes() == before


def test_unknown_not_retrieval_and_bad_metadata(tmp_path):
    m, a = daily(available=None)
    append(tmp_path, m, a)
    assert read(tmp_path)[0]["available_at"] is None
    for field, value in [("available_at", "2026-10-26T00:00:00Z"), ("source_session", "2026-10-22"), ("source_url", "https://example.org/dashboard"), ("observed_at", "2026-10-25T12:00:00")]:
        broken = copy.deepcopy(m); broken[field] = value
        with pytest.raises(IntegrityError): append(tmp_path / field, broken, a)


def test_identity_and_weekly_doc_cohort(tmp_path):
    m, a = weekly()
    append(tmp_path, m, a, b"synthetic report")
    m, a = weekly("qualified", "2.1.1", "2026-10-25T11:00:00Z")
    m["revision_reason"] = "synthetic correction; original near retained"
    append(tmp_path, m, a, b"synthetic report")
    first, second = read(tmp_path)
    assert first["classification"] == "near" and second["classification"] == "qualified"
    assert second["original_id"] == first["observation_id"] and second["role"] == "followup"
    m["economic_method"] = "invented-new-cohort"
    with pytest.raises(IntegrityError, match="does not restart"): append(tmp_path, m, a, b"synthetic report")


def test_weekly_repeated_occurrence_not_new_episode(tmp_path):
    m, a = weekly()
    append(tmp_path, m, a, b"synthetic report")
    m, a = weekly(run_date="2026-11-01", available="2026-11-01T10:00:00Z")
    m.update(observed_at="2026-11-01T12:00:00Z", revision_reason="next weekly occurrence")
    append(tmp_path, m, a, b"synthetic report")
    assert [r["role"] for r in read(tmp_path)] == ["original", "followup"]


@pytest.mark.parametrize("status", ["qualified", "near", "watch", "rejected", "unreviewed", "unavailable"])
def test_weekly_states_distinct(tmp_path, status):
    m, a = weekly(status)
    rows = json.loads(a); rows[0].update(reason="synthetic evidence", watch_scope="report")
    a = canonical(rows); m["artifact_sha256"] = digest(a)
    append(tmp_path, m, a, b"synthetic report")
    assert read(tmp_path)[0]["classification"] == status


def test_tampering_truncation_and_single_writer(tmp_path):
    m, a = daily(); append(tmp_path, m, a)
    path = tmp_path / "blobs" / digest(a); path.write_bytes(b"changed")
    with pytest.raises(IntegrityError, match="source blob"): audit(tmp_path)
    path.write_bytes(a)
    journal = tmp_path / "observations.jsonl"; good = journal.read_bytes(); journal.write_bytes(good[:-1])
    with pytest.raises(IntegrityError, match="truncated"): audit(tmp_path)
    journal.write_bytes(good)
    (tmp_path / ".writer.lock").touch()
    with pytest.raises(IntegrityError, match="single writer"): append(tmp_path, m, a)


def test_timing_holidays_equality_and_endpoints():
    # Synthetic explicit session sequence: missing dates are holidays, not missing prices.
    dates = [date(2026, 4, 1)] + [date(2026, 4, 7) + timedelta(days=i) for i in range(25)]
    closes = [f"{d}T16:30:00+02:00" for d in dates]
    closes[0] = "2026-04-01T13:10:00+02:00"
    entry = reference_close("2026-04-01T13:10:00+02:00", closes)
    assert entry.date() == date(2026, 4, 7)
    assert daily_endpoint(entry, 5, closes).date() == date(2026, 4, 12)
    assert reference_close(None, closes) is None
    assert daily_endpoint(entry, 20, closes).date() == date(2026, 4, 27)
    target, endpoint = weekly_endpoint(date(2026, 1, 31), 3, ["2026-04-30T16:30:00+02:00"])
    assert target == date(2026, 4, 30) == endpoint.date()
    assert weekly_endpoint(date(2026, 1, 31), 6, ["2026-08-03T16:30:00+02:00"])[1].date() == date(2026, 8, 3)


def test_zero_missing_capacity_costs_and_terminal_outcomes():
    assert volume_state([1]*59+[0])["status"] == "fails_zero_trade"
    assert volume_state([1]*59+[None])["status"] == "unverified"
    assert volume_state([1]*60)["capacity"] == "unverified"
    assert buy_net(.1, .0025, .0025) == pytest.approx(.0945137157107)
    assert sell_avoided(-.1, .0025) == pytest.approx(.0975)
    assert sell_avoided(.1, .0025) == pytest.approx(-.1025)
    assert outcome_state(delisted=True) == outcome_state(suspended=True) == "unresolved"
    assert outcome_state(delisted=True, consideration={"cash": 0}) == "requires_consideration_audit"


def test_audit_replay_and_provenance_correction_same_source(tmp_path):
    m, a = daily(available=None); append(tmp_path, m, a)
    original = read(tmp_path)[0]
    correction = copy.deepcopy(m)
    correction.update(available_at="2026-10-23T15:00:00Z", availability_evidence="synthetic newly authenticated source",
                      revision_reason="availability metadata correction; original remains unknown",
                      provenance_revisions={"NOD.OL": original["observation_id"]})
    append(tmp_path, correction, a)
    assert append(tmp_path, correction, a)["appended"] == 0
    assert read(tmp_path)[1]["role"] == "provenance_revision"
    result = audit(tmp_path)
    assert result["timing_ambiguous_groups"] == 1
    assert result["records"] == 2


def test_reentry_requires_link_and_identity_cannot_duplicate_event(tmp_path):
    m, a = weekly(); append(tmp_path, m, a, b"synthetic report")
    first = read(tmp_path)[0]
    m.update(episode="second", revision_reason="synthetic genuine re-entry")
    with pytest.raises(IntegrityError, match="re-entry"): append(tmp_path, m, a, b"synthetic report")
    m["reentry_of"] = first["observation_id"]
    append(tmp_path, m, a, b"synthetic report")
    assert read(tmp_path)[1]["reentry_of"] == first["observation_id"]
    assert audit(tmp_path)["records"] == 2


def test_actions_missing_fields_retained_without_outcomes(tmp_path):
    m, a = weekly()
    rows = json.loads(a)
    rows[0].update(raw_close=100, adjusted_close=50, split=2, dividend=2, volume=None,
                   suspension=True, terminal_consideration=None)
    a = canonical(rows); m["artifact_sha256"] = digest(a)
    append(tmp_path, m, a, b"synthetic report")
    assert read(tmp_path)[0]["row"] == rows[0]
    assert audit(tmp_path)["outcomes"].startswith("not collected")


def test_equal_time_conflict_missing_price_and_changed_identity(tmp_path):
    m, a = daily(); append(tmp_path, m, a)
    m2, a2 = daily("BUY"); m2["revision_reason"] = "ambiguous concurrent publication"
    with pytest.raises(IntegrityError, match="equal-time"): append(tmp_path, m2, a2)
    broken = a.replace(b",100,40", b",,40"); m2 = copy.deepcopy(m); m2["artifact_sha256"] = digest(broken)
    with pytest.raises(IntegrityError, match="price/RSI"): append(tmp_path, m2, broken)
    m2, a2 = daily("BUY", available="2026-10-23T16:00:00Z")
    m2.update(identities={"NOD.OL": {"isin": "synthetic", "share_class": "ordinary"}}, revision_reason="identity change")
    with pytest.raises(IntegrityError, match="identity changed"): append(tmp_path, m2, a2)


def test_frozen_real_producer_fixture_unknown_availability(tmp_path):
    from pathlib import Path
    base = Path(__file__).parent / "fixtures" / "validation" / "producer_2026-10-25"
    m = json.loads(base.with_suffix(".manifest.json").read_text())
    artifact = base.with_suffix(".csv").read_bytes()
    assert append(tmp_path, m, artifact)["appended"] == 201
    result = audit(tmp_path)
    assert result["records"] == 201 and result["timing_ambiguous_groups"] == 199
    records = read(tmp_path)
    assert sum(r["classification"] == "BUY" for r in records) == 4
    assert sum(r["classification"] == "SELL" for r in records) == 2
    assert sum(r["role"] == "withheld" for r in records) == 2
    assert not any(r["role"] == "original" for r in records)
    assert append(tmp_path, m, artifact)["appended"] == 0


def test_missing_provenance_parent_rejected(tmp_path):
    m, a = daily()
    m.update(provenance_revisions={"NOD.OL": "not-a-prior-observation"}, revision_reason="invalid parent")
    with pytest.raises(IntegrityError, match="revision link"):
        append(tmp_path, m, a)
    assert not (tmp_path / "observations.jsonl").exists()


def test_equal_instants_with_different_offsets_rejected(tmp_path):
    m, a = daily(available="2026-10-23T15:00:00Z")
    append(tmp_path, m, a)
    before = (tmp_path / "observations.jsonl").read_bytes()
    m, a = daily("BUY", available="2026-10-23T17:00:00+02:00")
    m["revision_reason"] = "same instant with another offset"
    with pytest.raises(IntegrityError, match="equal-time"):
        append(tmp_path, m, a)
    assert (tmp_path / "observations.jsonl").read_bytes() == before


def test_alias_tickers_same_resolved_security_rejected_atomically(tmp_path):
    m, a = daily()
    a += b"ALIAS.OL,2026-10-23,current,BUY,100,40\n"
    m["artifact_sha256"] = digest(a)
    m["identities"] = {"NOD.OL": {"isin": "synthetic-shared-isin", "share_class": "ordinary", "name": "name one"},
                       "ALIAS.OL": {"isin": "synthetic-shared-isin", "share_class": "ordinary", "name": "name two"}}
    with pytest.raises(IntegrityError, match="duplicate resolved security"):
        append(tmp_path, m, a)
    assert not (tmp_path / "observations.jsonl").exists()
