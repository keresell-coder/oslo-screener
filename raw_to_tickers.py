# raw_to_tickers.py
# Leser raw_tickers.txt, normaliserer til TICKER.OL, dedupliserer og sikrer HUNT.OL

import re

RAW_FILE = "raw_tickers.txt"
OUT_FILE = "tickers.txt"

def normalize_token(tok: str) -> str | None:
    t = tok.strip().upper()
    if not t:
        return None
    # Fjern eventuell .OL hvis noen allerede har det
    if t.endswith(".OL"):
        t = t[:-3]
    # Bare en enkel sanity: behold A–Z, 0–9 og bindestrek
    t = re.sub(r"[^A-Z0-9\-]", "", t)
    if not t:
        return None
    return f"{t}.OL"

def main():
    with open(RAW_FILE, "r") as f:
        raw = f.read()

    # Del på whitespace, komma, semikolon, pipe
    tokens = re.split(r"[\s,;|]+", raw)
    seen = set()
    out = []
    for tok in tokens:
        norm = normalize_token(tok)
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)

    # Særtilfellet HUNT.OL som du vil ha med
    if "HUNT.OL" not in seen:
        out.append("HUNT.OL")

    with open(OUT_FILE, "w") as f:
        for x in out:
            f.write(x + "\n")

    print(f"Wrote {OUT_FILE} with {len(out)} tickers")

if __name__ == "__main__":
    main()
