#!/usr/bin/env python3
"""
sync_tickers.py
Compares tickers.txt against the live Euronext Oslo Børs listing.
Adds new listings to tickers.txt; reports tickers no longer on exchange.
Run before validate_tickers.py in the weekly workflow.
"""

import os
import sys

from fetch_oslo_tickers import fetch_oslo_tickers

TICKERS_FILE = "tickers.txt"
SUMMARY_FILE = os.environ.get("GITHUB_STEP_SUMMARY", "")


def write_summary(lines: list[str]) -> None:
    if SUMMARY_FILE:
        with open(SUMMARY_FILE, "a") as f:
            f.write("\n".join(lines) + "\n\n")


def main() -> None:
    print("Fetching Oslo Børs listing from Euronext...", file=sys.stderr)
    try:
        exchange_set = set(fetch_oslo_tickers(mics="XOSL"))
    except RuntimeError as e:
        print(f"WARNING: Could not fetch Euronext list: {e}", file=sys.stderr)
        print("Skipping sync — validate_tickers.py will run on existing list.", file=sys.stderr)
        write_summary(["### Euronext sync", "", "⚠️ Could not reach Euronext — skipped."])
        sys.exit(0)

    with open(TICKERS_FILE) as f:
        current = [line.strip() for line in f if line.strip()]
    current_set = set(current)

    new_listings = sorted(exchange_set - current_set)
    not_on_exchange = sorted(current_set - exchange_set)

    if new_listings:
        updated = sorted(current_set | set(new_listings))
        with open(TICKERS_FILE, "w") as f:
            for t in updated:
                f.write(t + "\n")
        print(f"Added {len(new_listings)} new ticker(s) to {TICKERS_FILE}:", file=sys.stderr)
        for t in new_listings:
            print(f"  + {t}", file=sys.stderr)
    else:
        print("No new listings found on Euronext.", file=sys.stderr)

    summary = [
        "### Euronext Oslo Børs sync",
        "",
        f"Exchange reports **{len(exchange_set)}** listed equities on XOSL.  ",
        f"Our list had **{len(current_set)}** tickers.",
        "",
    ]
    if new_listings:
        summary.append(f"**{len(new_listings)} new listing(s) added to tickers.txt:**")
        summary.append("")
        for t in new_listings:
            summary.append(f"- `{t}`")
        summary.append("")
    else:
        summary.append("No new listings detected.")
        summary.append("")

    if not_on_exchange:
        summary.append(
            f"**{len(not_on_exchange)} ticker(s) in our list not found on exchange** "
            f"(may be delisted — validate_tickers.py will confirm via Yahoo Finance):"
        )
        summary.append("")
        for t in not_on_exchange:
            summary.append(f"- `{t}`")
        summary.append("")

    write_summary(summary)
    print(
        f"\nSync complete: {len(new_listings)} new, "
        f"{len(not_on_exchange)} possibly delisted.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
