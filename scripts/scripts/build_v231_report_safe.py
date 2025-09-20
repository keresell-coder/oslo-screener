#!/usr/bin/env python3
# scripts/build_v231_report_safe.py

import os, sys, subprocess, datetime as dt

CSV = "latest.csv"
ALIAS = "summaries/latest_v231.md"
DAILY_DIR = "summaries"

def write_fallback(reason: str):
    os.makedirs(DAILY_DIR, exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    md = []
    md.append(f"# Oslo Børs – Teknisk dagsrapport (v2.3.1)")
    md.append(f"**Dato:** {today}")
    md.append("")
    md.append("**Telling:** BUY 0 | SELL 0 | BUY-watch 0 | SELL-watch 0")
    md.append("")
    md.append("## BUY (rangert)")
    md.append("(ingen kandidater – " + reason + ")")
    md.append("")
    md.append("## SELL (rangert)")
    md.append("(ingen kandidater – " + reason + ")")
    md.append("")
    md.append("## BUY-watch (nærmest trigger)")
    md.append("(—)")
    md.append("")
    md.append("## SELL-watch (nærmest trigger)")
    md.append("(—)")
    md.append("")
    md.append("---")
    md.append("**Kontroller:**")
    md.append("- Pris-sjekk: KUNNE IKKE VERIFISERES.")
    md.append("- Ferskhet: KUNNE IKKE VERIFISERES (fallbackrapport).")
    content = "\n".join(md)
    with open(ALIAS, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[SAFE] Wrote fallback alias report → {ALIAS}")

def csv_rows(path: str) -> int:
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

def main():
    rows = csv_rows(CSV)
    print(f"[SAFE] latest.csv rows (incl. header if any): {rows}")

    # Normal path: bygg med eksisterende script når CSV ser brukbar ut
    if rows > 1:
        print("[SAFE] Running scripts/build_v231_report.py ...")
        try:
            subprocess.run([sys.executable, "scripts/build_v231_report.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[SAFE][WARN] build_v231_report.py failed: {e}. Writing fallback.")
            write_fallback("byggeskript feilet")
            return

        # Sikre at alias finnes. Hvis ikke, lag fallback.
        if not os.path.exists(ALIAS):
            print("[SAFE][WARN] Alias-rapport mangler etter bygg. Skriver fallback.")
            write_fallback("alias manglet etter bygg")
        else:
            print(f"[SAFE] Alias-rapport OK → {ALIAS}")
        return

    # Fallback path: tom/manglende CSV
    reason = "CSV var tom eller manglet"
    write_fallback(reason)

if __name__ == "__main__":
    main()
