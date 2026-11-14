"""Offline deterministic near-trigger evidence; production outputs stay untouched."""

import json
import subprocess
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_report

BASE = "55857903582d301ed63c24ebe3715b6b4a5e35a4"
source = subprocess.check_output(
    ["git", "show", f"{BASE}:scripts/build_report.py"], cwd=ROOT, text=True
)
old = {
    "__name__": "methodology_baseline",
    "__file__": str(ROOT / "scripts/build_report.py"),
}
exec(compile(source, old["__file__"], "exec"), old)
rows = [
    dict(
        ticker="FLAT.OL",
        signal="BUY-watch",
        data_status="current",
        close=100,
        previous_close=100,
        day_direction="flat",
        rsi14=35,
        rsi_dir=1,
        macd_hist=0.001,
        pct_above_sma50=-10,
        adx14=24,
        rsi6=25,
        mfi14=30,
    ),
    dict(
        ticker="EXIT.OL",
        signal="SELL-watch",
        data_status="current",
        close=100,
        previous_close=99,
        day_direction="up",
        rsi14=65,
        rsi_dir=-1,
        macd_hist=-0.001,
        pct_above_sma50=10,
        adx14=24,
        rsi6=70,
        mfi14=80,
    ),
]
before = [old["_enrich"](pd.Series(r)) for r in rows]
after = [build_report._enrich(pd.Series(r)) for r in rows]
out = ROOT / "review-evidence"
out.mkdir(exist_ok=True)
(out / "before-after.json").write_text(
    json.dumps(
        {
            "baseline_revision": BASE,
            "fixture": "Synthetic rule-boundary examples, not market data",
            "input": rows,
            "before": before,
            "after": after,
        },
        indent=2,
        allow_nan=False,
    )
    + "\n"
)
for name, records, module in [
    ("before", before, old),
    ("after", after, vars(build_report)),
]:
    text = "# SYNTHETIC OFFLINE REVIEW — not market data\n\n"
    for bucket in ["BUY-watch", "SELL-watch"]:
        text += (
            "\n## "
            + bucket
            + "\n\n"
            + module["_watch_table"](
                pd.DataFrame([r for r in records if r["bucket"] == bucket])
            )
            + "\n"
        )
    (out / f"{name}.md").write_text(text)
(out / "README.md").write_text(
    "Run `python scripts/methodology_review.py`. The same synthetic rows go through the pinned old/new enrichment and actual Markdown watch-table renderers. A flat BUY-watch day at RSI35 lacks up-close; SELL-watch at65 with up-close lacks down-close. Old tiny MACD distances no longer imply gate proximity. Production snapshots and classification are unchanged.\n"
)
