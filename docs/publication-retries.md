# Overnight retries and report preservation

The daily workflow attempts the completed Oslo session at 19:37 and 23:37 UTC
on weekdays, then 03:37 UTC Tuesday through Saturday. GitHub can delay schedules;
these times leave more room before the next Oslo opening than the old 06:15 UTC
run. They do not guarantee data availability or delivery time.

Before downloading, the job captures the committed report. After building and
validating a candidate, it skips the main commit and Pages deployment if that
candidate is blocked or has fewer current stocks than a still-valid report for
the same session. Both the attempted bundle and the decision remain available
as workflow artifacts. A blocked data attempt still fails its source-health
check, even when a good prior report is retained.

Retention requires the full previous bundle to validate at the current time,
including its hashes, CSV observations, report, landing page and expiry. It also
requires the same universe, source, coverage gate and producer inputs. The input
comparison uses the commit that produced the prior report, not a later code
commit. This prevents an old result hiding stricter validation or changed rules.
An expired or unverifiable prior report cannot suppress a new blocked report.
Equal or improved coverage permits fresh corrections to be published.

Only main may publish. Branch dispatches create review artifacts. If main moves
while a report is being built, the non-forced push fails instead of rebasing a
report onto changed inputs or overwriting a newer publication.

This preserves reports that satisfy the existing validation contract; it does
not independently certify Yahoo's historical observations. The original 90%
coverage requirement and current 202-stock production universe remain unchanged.
The wider universe and history-recovery proposal in PR #16 still needs separate
live source acceptance. No new data source is enabled by this change.
