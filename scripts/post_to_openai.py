# scripts/post_to_openai.py
import os, pathlib
from openai import OpenAI

PROMPT = """ROLE
Du er en nøktern aksjeanalytiker for Oslo Børs-screeneren. Kun observasjoner fra data + verifiserte kilder. Ingen råd. Europe/Oslo. Skille fakta/analyse.
TASK
1) Oppsummer antall per klasse.
2) Topp 3 BUY og topp 3 SELL etter intern conviction (gate + dagsfilter + trendstøtte + ADX). Si eksplisitt hvis felt mangler/NaN.
3) 3–5 watch-triggere (nær terskler).
4) Kort market color (2–4 punkt).
FORMAT
Kompakt markdown. Norske datoer (DD.MM.YYYY).
DATA
CSV nedenfor:
"""

def main():
    csv_text = pathlib.Path("latest.csv").read_text(encoding="utf-8")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=f"{PROMPT}\n```\n{csv_text}\n```",
    )
    pathlib.Path("exec_summary.md").write_text(resp.output_text, encoding="utf-8")
    print("Wrote exec_summary.md")

if __name__ == "__main__":
    main()
