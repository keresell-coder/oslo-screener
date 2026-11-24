# Oslo Børs – Teknisk dagsrapport

Research-only rebound setups. SELL denotes an existing-holder reduction/exit review, never a short instruction. Fixed stop distances and position percentages are legacy heuristics, not executable stops, recommended allocations or loss budgets. Separate KE activity/capacity evidence follows each list. Execution suitability remains unverified; no new liquidity cutoff is introduced.

<!-- snapshot_id=5b30fb8874a042b096af24fa7c2d893d -->

**Forventet avsluttet handelssesjon:** 24.11.2026

**Datastatus:** DEGRADED · 192/198 aktuelle rader

**Generert:** 2026-11-24T17:35:26Z · snapshot 5b30fb8874a042b096af24fa7c2d893d


**Samlet prosentkrav er midlertidig suspendert. Bare aksjer med aktuelle, gyldige data kan gi signaler.**

**Utelatte aksjer:** 6. Full liste med årsaker står nedenfor.

**Telling:** BUY 3 | SELL 2 | BUY-watch 28 | SELL-watch 8


## Rebound setups — review (legacy BUY codes)

| Context count (heuristic) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|---:|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| 1 | ENSU.OL | 0.44 | 32.06 | +1.43 | -0.01 ◻️ | -19.22 ❌ | 37 🟢 | RSI6 37 ⚪ · MFI 23 🔴 |
| 0 | PEN.OL | 27.30 | 33.37 | +0.41 | -0.34 ❌ | -10.91 ❌ | 25 ⚪ | RSI6 23 ⚪ · MFI 28 🔴 |
| 0 | VOW.OL | 2.20 | 29.07 | +3.24 | -0.06 ❌ | -21.75 ❌ | 24 ⚪ | RSI6 25 ⚪ · MFI 24 🔴 |

**ENSU.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 537,584; NOK 100k / 500k orders = 18.60% / 93.01% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**PEN.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 18,410,810; NOK 100k / 500k orders = 0.54% / 2.72% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**VOW.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 2,305,594; NOK 100k / 500k orders = 4.34% / 21.69% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


**Example rule qualification (not a validated priority)**

ENSU.OL kvalifiserte via gatekeeper (RSI≤35 & opp-dag). ADX≥25 (🟢).


## Reduction/exit review setups — not short (legacy SELL codes)

| Context count (heuristic) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|---:|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| 1 | 2020.OL | 20.48 | 74.89 | -11.31 | 1.18 ❌ | 123.69 ❌ | 50 🟢 | RSI6 77 ⚪ · MFI 95 🔴 |
| 1 | ENDUR.OL | 141.00 | 66.13 | -6.01 | 0.32 ❌ | 15.82 ❌ | 43 🟢 | RSI6 55 ⚪ · MFI 72 🔴 |

**2020.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 15,753,682; NOK 100k / 500k orders = 0.63% / 3.17% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**ENDUR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 15,768,808; NOK 100k / 500k orders = 0.63% / 3.17% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


**Example rule qualification (not a validated priority)**

2020.OL kvalifiserte via gatekeeper (RSI≥65 & ned-dag). ADX≥25 (🟢).


## BUY-watch — rebound review (alphabetical, not proximity-ranked)

| Missing setup conditions (not ranked) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|:-------|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | ABG.OL | 6.75 | 26.14 | -9.73 | -0.03 ◻️ | -6.20 ❌ | 17 ⚠️ | RSI6 13 ⚪ · MFI 25 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | AKER.OL | 1032.00 | 34.84 | -6.10 | 4.70 ✅ | -16.03 ❌ | 39 🟢 | RSI6 35 ⚪ · MFI 37 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | AKRBP.OL | 300.30 | 26.85 | -1.91 | -3.07 ❌ | -13.25 ❌ | 36 🟢 | RSI6 14 ⚪ · MFI 13 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | AKSO.OL | 35.10 | 33.49 | -3.29 | -0.02 ◻️ | -9.91 ❌ | 22 ⚪ | RSI6 21 ⚪ · MFI 40 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | BNOR.OL | 507.00 | 26.86 | -0.46 | -5.09 ❌ | -12.34 ❌ | 34 🟢 | RSI6 16 ⚪ · MFI 22 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | BWE.OL | 45.50 | 27.81 | -1.09 | 0.05 ◻️ | -19.74 ❌ | 42 🟢 | RSI6 23 ⚪ · MFI 38 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | CAVEN.OL | 3.92 | 30.76 | -0.97 | -0.07 ❌ | -22.34 ❌ | 14 ⚠️ | RSI6 19 ⚪ · MFI 49 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | CONTX.OL | 3.82 | 30.46 | -1.51 | -0.07 ❌ | -18.69 ❌ | 24 ⚪ | RSI6 15 ⚪ · MFI 32 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | COSH.OL | 121.00 | 24.75 | -4.54 | -0.89 ❌ | -8.60 ❌ | 18 ⚠️ | RSI6 12 ⚪ · MFI 28 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | ELABS.OL | 2.17 | 27.97 | -2.66 | -0.05 ❌ | -28.82 ❌ | 20 ⚠️ | RSI6 17 ⚪ · MFI 27 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | EQVA.OL | 2.15 | 25.03 | -3.91 | -0.02 ◻️ | -18.10 ❌ | 53 🟢 | RSI6 12 ⚪ · MFI 18 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | GENO.OL | 14.50 | 29.84 | -4.93 | -0.32 ❌ | -24.37 ❌ | 28 🟢 | RSI6 20 ⚪ · MFI 17 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | GSF.OL | 21.10 | 30.70 | -7.20 | -0.07 ❌ | -10.19 ❌ | 33 🟢 | RSI6 21 ⚪ · MFI 51 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | HAFNI.OL | 84.80 | 34.36 | -3.16 | -0.66 ❌ | -9.44 ❌ | 15 ⚠️ | RSI6 22 ⚪ · MFI 29 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | HAUTO.OL | 157.40 | 32.53 | -7.36 | -0.97 ❌ | -10.42 ❌ | 20 ⚪ | RSI6 22 ⚪ · MFI 37 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | HYPRO.OL | 0.18 | 22.31 | -1.11 | -0.01 ◻️ | -54.92 ❌ | 31 🟢 | RSI6 12 ⚪ · MFI 5 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | IOX.OL | 1.70 | 23.48 | -2.72 | -0.03 ◻️ | -28.93 ❌ | 18 ⚠️ | RSI6 9 ⚪ · MFI 39 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | NHY.OL | 64.00 | 29.93 | -2.41 | 0.04 ◻️ | -13.79 ❌ | 37 🟢 | RSI6 25 ⚪ · MFI 36 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | OTEC.OL | 16.62 | 33.14 | -2.18 | -0.04 ◻️ | -12.11 ❌ | 29 🟢 | RSI6 24 ⚪ · MFI 56 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | PHO.OL | 40.10 | 30.52 | -2.00 | -0.06 ❌ | -15.19 ❌ | 36 🟢 | RSI6 30 ⚪ · MFI 17 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | PRS.OL | 3.60 | 27.87 | -0.08 | -0.07 ❌ | -21.75 ❌ | 33 🟢 | RSI6 20 ⚪ · MFI 27 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | REACH.OL | 4.21 | 19.90 | -1.15 | -0.16 ❌ | -29.42 ❌ | 37 🟢 | RSI6 15 ⚪ · MFI 26 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | SCATC.OL | 81.30 | 34.49 | -1.76 | -0.24 ❌ | -12.62 ❌ | 16 ⚠️ | RSI6 19 ⚪ · MFI 22 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | TOM.OL | 79.55 | 22.36 | -8.96 | -2.00 ❌ | -14.70 ❌ | 34 🟢 | RSI6 10 ⚪ · MFI 17 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | VAR.OL | 44.65 | 27.11 | -0.12 | -0.56 ❌ | -13.00 ❌ | 36 🟢 | RSI6 15 ⚪ · MFI 16 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | VOIM.OL | 0.11 | 32.71 | -0.10 | 0.00 ◻️ | -53.07 ❌ | 19 ⚠️ | RSI6 31 ⚪ · MFI 42 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | WSTEP.OL | 11.05 | 33.26 | -1.41 | -0.04 ◻️ | -9.80 ❌ | 33 🟢 | RSI6 28 ⚪ · MFI 21 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | YAR.OL | 372.40 | 29.33 | -1.79 | -2.15 ❌ | -9.27 ❌ | 27 🟢 | RSI6 16 ⚪ · MFI 44 ⚪ |

**ABG.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 1,723,927; NOK 100k / 500k orders = 5.80% / 29.00% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**AKER.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 107,151,098; NOK 100k / 500k orders = 0.09% / 0.47% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**AKRBP.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 492,874,419; NOK 100k / 500k orders = 0.02% / 0.10% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**AKSO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 11,820,598; NOK 100k / 500k orders = 0.85% / 4.23% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**BNOR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 45,322,672; NOK 100k / 500k orders = 0.22% / 1.10% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**BWE.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 11,046,037; NOK 100k / 500k orders = 0.91% / 4.53% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**CAVEN.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 83,772; NOK 100k / 500k orders = 119.37% / 596.86% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**CONTX.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 380,352; NOK 100k / 500k orders = 26.29% / 131.46% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**COSH.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 17,232,125; NOK 100k / 500k orders = 0.58% / 2.90% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**ELABS.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 531,884; NOK 100k / 500k orders = 18.80% / 94.01% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**EQVA.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 118,978; NOK 100k / 500k orders = 84.05% / 420.25% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**GENO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 4,176,910; NOK 100k / 500k orders = 2.39% / 11.97% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**GSF.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 4,336,945; NOK 100k / 500k orders = 2.31% / 11.53% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HAFNI.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 60,393,701; NOK 100k / 500k orders = 0.17% / 0.83% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HAUTO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 53,746,838; NOK 100k / 500k orders = 0.19% / 0.93% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HYPRO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 234,959; NOK 100k / 500k orders = 42.56% / 212.80% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**IOX.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 123,740; NOK 100k / 500k orders = 80.81% / 404.07% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NHY.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 285,210,239; NOK 100k / 500k orders = 0.04% / 0.18% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**OTEC.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 1,601,050; NOK 100k / 500k orders = 6.25% / 31.23% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**PHO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 3,635,681; NOK 100k / 500k orders = 2.75% / 13.75% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**PRS.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 5,629,714; NOK 100k / 500k orders = 1.78% / 8.88% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**REACH.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 1,549,552; NOK 100k / 500k orders = 6.45% / 32.27% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**SCATC.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 70,701,604; NOK 100k / 500k orders = 0.14% / 0.71% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**TOM.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 62,072,706; NOK 100k / 500k orders = 0.16% / 0.81% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**VAR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 290,227,271; NOK 100k / 500k orders = 0.03% / 0.17% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**VOIM.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 98,356; NOK 100k / 500k orders = 101.67% / 508.36% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**WSTEP.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 226,760; NOK 100k / 500k orders = 44.10% / 220.50% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**YAR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 180,664,767; NOK 100k / 500k orders = 0.06% / 0.28% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


## SELL-watch — reduction/exit review, not short (alphabetical)

| Missing setup conditions (not ranked) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|:-------|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | IDEX.OL | 10.65 | 75.04 | +7.11 | 0.19 ❌ | 46.02 ❌ | 36 🟢 | RSI6 80 ⚪ · MFI 81 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | IWS.OL | 64.60 | 67.56 | +5.51 | 0.20 ❌ | 6.24 ❌ | 23 ⚪ | RSI6 82 ⚪ · MFI 56 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | KID.OL | 146.40 | 66.84 | +0.72 | -0.46 ✅ | 11.13 ❌ | 46 🟢 | RSI6 61 ⚪ · MFI 57 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | MEDI.OL | 326.00 | 72.86 | +1.80 | -0.42 ✅ | 14.55 ❌ | 36 🟢 | RSI6 80 ⚪ · MFI 66 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | MORLD.OL | 27.40 | 66.99 | +5.09 | 0.03 ◻️ | 13.86 ❌ | 25 🟢 | RSI6 71 ⚪ · MFI 70 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | NKR.OL | 20.70 | 76.09 | +2.05 | 0.07 ❌ | 26.76 ❌ | 50 🟢 | RSI6 80 ⚪ · MFI 83 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | SAGA.OL | 1.67 | 71.09 | +0.44 | 0.02 ◻️ | 8.53 ❌ | 48 🟢 | RSI6 88 ⚪ · MFI 80 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | STECH.OL | 92.40 | 67.14 | +5.98 | 0.17 ❌ | 8.23 ❌ | 22 ⚪ | RSI6 74 ⚪ · MFI 68 ⚪ |

**IDEX.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 1,581,098; NOK 100k / 500k orders = 6.32% / 31.62% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**IWS.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 144,942; NOK 100k / 500k orders = 68.99% / 344.97% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**KID.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 9,370,657; NOK 100k / 500k orders = 1.07% / 5.34% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**MEDI.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 4,918,545; NOK 100k / 500k orders = 2.03% / 10.17% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**MORLD.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 8,510,448; NOK 100k / 500k orders = 1.18% / 5.88% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NKR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 3,392,992; NOK 100k / 500k orders = 2.95% / 14.74% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**SAGA.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 33,329; NOK 100k / 500k orders = 300.04% / 1500.21% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**STECH.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-02 to 2026-11-24, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 755,483; NOK 100k / 500k orders = 13.24% / 66.18% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


## Aksjer uten nødvendige data

Disse aksjene er ikke med i signallistene. Manglende data betyr ikke at en aksje er avnotert.

| Aksje | Datastatus | Observasjonsdato | Årsak |
|---|---|---|---|
| CADLR.OL | stale | 2026-11-05 | missing_expected_completed_session |
| HSPG.OL | stale | 2026-11-23 | missing_expected_completed_session |
| ININ.OL | stale | 2026-11-23 | missing_expected_completed_session |
| OUTLT.OL | invalid | 2026-11-24 | insufficient_indicator_warmup |
| PYRUM.OL | stale | 2026-11-23 | missing_expected_completed_session |
| TRSB.OL | stale | 2026-11-23 | missing_expected_completed_session |


---

**Kontroller:** Datakontroll: avsluttet handelssesjon, raddekning og snapshot-integritet verifisert. Datastatus degraded; begrensninger: ingen strukturelle avvik.

_Event- og fundamentaldekning: ikke tilgjengelig i denne tekniske screeningen. BUY/SELL er tekniske oppsett, ikke verifiserte handelsanbefalinger._
