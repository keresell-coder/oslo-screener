# Free-data acceptance

The code and report-builder fixes are tested. A reliable, unattended free-data
replacement is **not yet accepted for production**.

## Current acceptance policy — 14 November 2026

PR #16 incorporates current main and the temporary `coverage_policy: per_stock`
implementation from PR #18. Every included stock must pass its own history,
session, price and indicator checks. List every excluded instrument and its
reason; exclusions and coverage below 90% do not block the remaining valid
stocks. Zero eligible stocks and failed snapshot integrity still block a report.
The percentage gate is restored only by explicitly selecting `minimum`.

The refreshed exchange directory contains 290 mapped stocks: 194 Oslo Børs,
10 Expand and 86 Growth. This is the attempted universe, not a claim of complete
price coverage. The recovery fetcher retains unadjusted closes for main's
turnover proxy while technical indicators continue to use adjusted prices.

Before recommending a merge, obtain validated previous-session report bundles
and complete exclusion lists before the next Oslo opening for three consecutive
trading sessions. Independently check prices, volume and corporate actions across
all three markets. Current-head software tests must pass and current main must
merge cleanly. Repeated attempts for one session do not extend the streak.
The historical-website backup remains disabled; the MiFID service remains an
audit source until the additional source requirements below are satisfied.

## Historical live tests — September 2026

| Test | Result for the 18 September session | Meaning |
| --- | --- | --- |
| Yahoo-only, full GitHub runner | 29/293 current; 9.9%; blocked | Later scheduling and exact-session retries recover some observations, but do not repair the missing 17 September history. |
| Yahoo plus experimental historical CSV backup, local and GitHub | 268/293 current; 91.5%; degraded and actionable under the existing 90% gate | An unattended HTTP path works technically. Its source terms still prevent treating it as an unrestricted production feed. |
| Separately licensed MiFID trade file, local and GitHub | 163,661 events across XOSL, XOAS and MERK, including two cancellations | One free file covers trades from all three markets without a browser or API key. |
| MiFID order-book price comparison | All four prices matched previously downloaded exchange daily observations for all 277 comparable stocks | Encouraging single-session evidence, not full source acceptance. |
| Yahoo one-minute reconstruction, four stocks | Incomplete closing-auction activity and volume, also with `prepost=True` | Rejected as daily-price recovery. |

GitHub evidence:
- [Yahoo-only run: report builds, data acceptance fails](https://github.com/keresell-coder/oslo-screener/actions/runs/35430701637).
- [Experimental historical-CSV run: completed successfully](https://github.com/keresell-coder/oslo-screener/actions/runs/35432097709).
- [Separately licensed MiFID source audit: completed successfully](https://github.com/keresell-coder/oslo-screener/actions/runs/35433199537).

Both full runs used all 293 mapped instruments: 197 Oslo Børs, 10 Expand and
86 Growth. The previously configured 202 tickers were not broadly delisted;
the configuration omitted much of Expand and Growth. Incomplete or unseasoned
stocks remain explicit rows with signals withheld.

## Two different Euronext services

The historical CSV reader accesses `live.euronext.com`. The
[general website terms](https://www.euronext.com/en/terms-use) restrict systematic
and automated retrieval without permission. It is disabled in both production
and automatic PR acceptance. The successful development run establishes
technical access; it does not establish permission for recurring collection.

The [MiFID delayed trade service](https://marketdata.euronext.com/data-reporting-service/trades-file)
has separate [free-use terms](https://www.euronext.com/sites/default/files/stld/terms_and_conditions_for_delayed_data.pdf).
Euronext documents CSV downloads, a maximum 15-minute publication delay and
availability for at least 24 hours. It provides trades, not a ready-made adjusted
daily history, dividends or split factors. Its advertised selections do not
offer the old sessions needed to backfill the current Yahoo gaps.
Both previous-day and since-previous-day selections returned only 18 September
trades when checked on 19 September; neither supplied the missing 17 September.

The audit cancels matching trades, withholds unresolved amendments/conflicting
identifiers, and keeps off-book and dark-market observations out of provisional
order-book prices. It reports absent instruments without calling them delisted.
The provisional last trade is not certified as an official reference close.

Volume is still unresolved: after cancellation handling, summing all trades
matched the reference daily volume for 266/277 comparable stocks. Summing only
order-book trades matched 218/277. Neither rule can silently replace the existing
volume series. The audit deliberately calls its quantity `lit_volume`.

## Remaining work before production acceptance

1. Require complete, valid history with an appropriate right of use for every
   included stock. Keep unresolved stocks excluded with reasons; they do not
   block the other stocks under the owner's temporary policy. Repeating requests
   cannot create observations the provider does not return.
2. Validate official closing-price and volume definitions, corporate actions,
   illiquid/no-trade sessions and corrections across multiple sessions.
3. Establish a persistent daily archive for the short-lived free trade files.
   The current GitHub job is a source audit, not an operating historical store.
4. Pass full-universe GitHub attempts under the current per-stock policy and the
   three-session acceptance rule above, then review the branch. Incomplete Yahoo
   histories remain excluded; a successful partial report is not full coverage.

The branch adds paced retries, bounded parallel downloads, three overnight
attempts, complete-universe mapping, retained diagnostics and the original
sorted-CSV/health ordering fix. It applies the owner's temporary per-stock policy
without weakening individual checks, fabricating observations or enabling the
historical-website backup.
