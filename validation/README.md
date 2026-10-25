# Manual Sprint 3 observation pilot

This isolated stdlib module imports observations; it does not fetch data, calculate
signals, run outcomes/backtests, place trades or change any production gate. No
workflow imports it. No capture schedule is installed. Production CSVs, reports,
selection and Energy are untouched. The primary daily surface is pinned to
`https://keresell-coder.github.io/oslo-screener/latest.csv`; weekly uses the delivered
report plus frozen case array. The dashboard is not an alternative timing source.

## Manual use

Run from the repository root with an **external, private pilot directory**:

```
python -m validation.ledger import --ledger /absolute/pilot-ledger \
  --manifest tests/fixtures/validation/producer_2026-10-25.manifest.json \
  --artifact tests/fixtures/validation/producer_2026-10-25.csv
python -m validation.ledger audit --ledger /absolute/pilot-ledger
python -m pytest -q tests/test_validation_pilot.py
```

The real public CSV fixture is frozen at Git `9b3dc1a50b6fc17768b3e2ff04a9a214a0dc317e`,
not regenerated. It has 201 rows: 199 current, two withheld, four BUY and two SELL.
Availability, historical membership, stable security identity and authenticated
generator commit remain unknown. The result is 199 timing-unverified records,
two retained withheld records and **zero timed original events**. Import time is
not substituted for publication time. Reimport is idempotent. This reconciles a
bounded existing sample; it does not validate returns or original availability.

For weekly import use `--report /path/delivered-report` as well. `--artifact` is a
JSON array of frozen case objects with `security` and `status` (qualified, near,
watch, rejected, unreviewed, unavailable). Watch requires `watch_scope` (e.g. report
or broader); rejected/unavailable requires `reason`. All supplied case fields are
preserved. Reports are content-addressed too; their SHA256 must match the manifest.
A summary of unreviewed counts is not evidence of individual named rejections.
Only import identified frozen records; do not manufacture 266 named cases from a
population count. No historical weekly AI cases are reconstructed by this pilot.

## Manifest and provenance

Use the fixture manifest as the daily schema example. Every input explicitly
supplies schema, kind, source URL, artifact SHA256, economic method, documented
method/schema versions, observed_at, available_at, availability_evidence,
source_published_at, source_cutoff, universe, code_revision and identities.
Unknown values are **null**, not download/generation substitutes. A known
available_at requires a reference to the authenticated observation/delivery
record. This importer validates structure/chronology, not the truth of a caller's
attestation. Record generated/retrieved timestamps separately in extra fields;
the source CSV and full manifest remain immutable blobs.

Daily method must match the CSV methodology_version and economic_method; source
session must match CSV expected_session. Non-withheld rows require current date,
positive finite close and finite RSI; source classifications are captured, not
recalculated from rounded exported values. Stable identities, if known, are an
identities mapping from ticker to `{isin, share_class}`; other identity fields may
be retained. Provided identities are explicitly **not authenticated** by this
module. Unknown identity uses an unverified symbol namespace; merging aliases or
changing identity inside an episode is blocked pending a separately audited
identity reconciliation. The ledger does not establish a point-in-time universe.

Weekly additionally requires run_date and report_sha256. Methods 2.1.0/2.1.1
belong to economic_method `weekly-2026-10-25`. Documentation 2.1.1 does not reset the
cohort. Earlier/broken methods need explicitly distinct cohort identifiers.
Repeated names retain one first episode per economic cohort. Later occurrences,
including a near→qualified correction, preserve the original classification and
link as follow-ups. A genuine re-entry uses a new `episode`, `reentry_of` original
observation ID and revision_reason; it cannot replace the first episode.

## Original and revision semantics

The daily grouping is security/share class (or visibly unverified symbol), source
session and economic method. First usable **known-availability** publication locks
the original, including neutral/watch. Earlier withheld rows remain retained; a
later usable publication may start an original only at its actual availability.
Later publications are linked revisions, never extra original events.

Manually import known publications in chronological order **within each group**.
An earlier publication discovered after a later import is rejected before journal
writes. Do not sort by retrieval or ingest time. Preserve the rejected source
outside the ledger and report the gap; rebuild a **separate** audited ledger from
the complete chronologically ordered inputs if necessary, retaining the old
ledger and reconciliation. Never quietly rewrite its original. Differing artifacts
at identical available_at in one group are ambiguous and rejected.

Unknown-availability usable records stay timing-unverified. They block a later
original for that group. If discovered after an original, audit flags the whole
group timing-ambiguous; the original record remains immutable but must not be
interpreted as proven earliest public classification. Unknown withheld timing does
not block later usable records. No provenance or identity claim is promoted by
successful import. Same-artifact changed metadata requires explicit
`provenance_revisions: {ticker: prior_observation_id}` and revision_reason; it adds
a provenance_revision, not a new original. It does not automatically clear an old
unknown-timing flag. Timing adjudication/identity repair is a later reviewed step.

Each original has a stable ID; later observations link original_id and
previous_observation_id. overlap_group links the same security/economic method
across sessions. No statistical independence or outcome is inferred from record
counts. Non-overlap sampling, RSI-only comparator grids, trial registries and
return evaluation remain future scope; the observations are not yet a backtest.

## Integrity and operational limits

Use one operator/process. An exclusive lock file rejects overlapping writers; a
crashed lock requires manual inspection, not automatic deletion. Immutable blobs
hold exact source bytes and canonical manifest bytes, named by SHA256. Every JSONL
record has sequence/previous-hash/checksum. Audit verifies blobs, journal chain and
replays the immutable imports to reproduce all roles/links/rows. All validation
precedes journal writes. An interrupted write is detected and blocks further
import. Orphan blobs can remain after interruption and are not observations.
Back up the complete directory, including blobs, manifest and journal. A hash
chain detects accidental mutation but is not a signature or external trust anchor;
a privileged person could rewrite everything. It cannot prove a caller's source
attestation. Preserve an independently hashed/exported evidence copy for review.

## Research conventions only

`conventions.py` encodes pure synthetic acceptance examples. Supply an ordered,
authenticated **official session-close schedule with offsets**, including holidays
and early closes; the module does not fetch/authenticate one or extrapolate 2027.
Reference close is strictly after known availability (equality goes next session),
never a claimed fill. Daily endpoints count 5/10/20 intervals, with entry index0.
Weekly endpoints clamp three/six calendar months and take the first scheduled
session on/after target. Missing schedule coverage returns unavailable; missing
security prices must not shift endpoints. No actual outcome prices are imported.

Volume diagnostics keep zero and missing separate; 60 positive sessions do not
verify NOK100k/500k capacity. BUY/SELL cost examples are research arithmetic, not
broker estimates. Raw/adjusted values, dividends and splits can be retained as
source fields but are not mixed to manufacture returns. Suspensions and delistings
stay unresolved without audited consideration; last price is not assumed cash.

## Accepted contract and next integration gate

Source: accepted 25 October design evidence (Drive file
`10tt7tLay42da4axXqAn3mR4Zw7xs8vcv`). Specification SHA256
`74eb4134407c865be867f648f7b603de8dedf56764975f58b7601ae71d5ba716`;
acceptance examples `572ed5b71a3de7400435b9ebc4b44d6df20ca375ec5770a9e96283dcd360849b`.
The user report is Library `libfile_917cbacd48748191978d8b828a9da245`.

Independent review must accept this head and manual evidence before merge.
Recurring capture is **not enabled**. Before integrating with an existing schedule,
review durable storage, chosen-surface availability evidence, identity/universe
provenance, source report/CSV hashes, backup and failure handling. Keep the weekly
readiness check unchanged. No new schedule or production output is necessary here.
