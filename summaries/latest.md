# Oslo Børs – Teknisk dagsrapport

Research-only rebound setups. SELL denotes an existing-holder reduction/exit review, never a short instruction. Fixed stop distances and position percentages are legacy heuristics, not executable stops, recommended allocations or loss budgets. Separate KE activity/capacity evidence follows each list. Execution suitability remains unverified; no new liquidity cutoff is introduced.

<!-- snapshot_id=118165541c7e4ec4a449992c4164568f -->

**Forventet avsluttet handelssesjon:** 25.11.2026

**Datastatus:** DEGRADED · 192/198 aktuelle rader

**Generert:** 2026-11-25T17:07:19Z · snapshot 118165541c7e4ec4a449992c4164568f


**Samlet prosentkrav er midlertidig suspendert. Bare aksjer med aktuelle, gyldige data kan gi signaler.**

**Utelatte aksjer:** 6. Full liste med årsaker står nedenfor.

**Telling:** BUY 4 | SELL 2 | BUY-watch 33 | SELL-watch 6


## Rebound setups — review (legacy BUY codes)

| Context count (heuristic) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|---:|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| 2 | BWE.OL | 46.10 | 30.86 | +3.05 | 0.11 ✅ | -18.32 ❌ | 42 🟢 | RSI6 32 ⚪ · MFI 42 ⚪ |
| 1 | AKRBP.OL | 302.00 | 28.56 | +1.71 | -2.79 ❌ | -12.42 ❌ | 37 🟢 | RSI6 20 ⚠️ · MFI 15 🔴 |
| 1 | GSF.OL | 21.22 | 32.54 | +1.84 | -0.09 ❌ | -9.33 ❌ | 34 🟢 | RSI6 26 ⚪ · MFI 48 ⚪ |
| 1 | YAR.OL | 377.30 | 34.55 | +5.23 | -2.01 ❌ | -7.74 ❌ | 29 🟢 | RSI6 30 ⚪ · MFI 42 ⚪ |

**BWE.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 11,046,037; NOK 100k / 500k orders = 0.91% / 4.53% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**AKRBP.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 504,276,843; NOK 100k / 500k orders = 0.02% / 0.10% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**GSF.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 4,573,267; NOK 100k / 500k orders = 2.19% / 10.93% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**YAR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 180,664,767; NOK 100k / 500k orders = 0.06% / 0.28% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


**Example rule qualification (not a validated priority)**

BWE.OL kvalifiserte via gatekeeper (RSI≤35 & opp-dag). MACD støtter (✅). ADX≥25 (🟢).


## Reduction/exit review setups — not short (legacy SELL codes)

| Context count (heuristic) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|---:|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| 1 | SAGA.OL | 1.66 | 69.95 | -1.14 | 0.02 ◻️ | 8.04 ❌ | 50 🟢 | RSI6 85 ⚠️ · MFI 71 🔴 |
| 1 | 2020.OL | 19.94 | 72.61 | -2.29 | 1.10 ❌ | 112.30 ❌ | 50 🟢 | RSI6 73 ⚪ · MFI 86 🔴 |

**SAGA.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 43,328; NOK 100k / 500k orders = 230.80% / 1153.98% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**2020.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 15,753,682; NOK 100k / 500k orders = 0.63% / 3.17% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


**Example rule qualification (not a validated priority)**

SAGA.OL kvalifiserte via gatekeeper (RSI≥65 & ned-dag). ADX≥25 (🟢).


## BUY-watch — rebound review (alphabetical, not proximity-ranked)

| Missing setup conditions (not ranked) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|:-------|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | ABG.OL | 6.73 | 25.46 | -0.68 | -0.04 ◻️ | -6.32 ❌ | 20 ⚪ | RSI6 12 ⚪ · MFI 13 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | AGLX.OL | 12.50 | 32.98 | -2.74 | -0.02 ◻️ | -12.93 ❌ | 23 ⚪ | RSI6 20 ⚪ · MFI 49 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | AKAST.OL | 8.74 | 34.01 | -2.33 | -0.04 ◻️ | -12.83 ❌ | 29 🟢 | RSI6 25 ⚪ · MFI 41 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | AKER.OL | 1030.00 | 34.61 | -0.23 | 3.70 ✅ | -15.49 ❌ | 39 🟢 | RSI6 35 ⚪ · MFI 41 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | AKSO.OL | 34.84 | 32.26 | -1.23 | -0.09 ❌ | -10.23 ❌ | 23 ⚪ | RSI6 19 ⚪ · MFI 31 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | BNOR.OL | 499.00 | 25.03 | -1.83 | -5.40 ❌ | -13.43 ❌ | 36 🟢 | RSI6 13 ⚪ · MFI 24 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | CAVEN.OL | 3.85 | 29.71 | -1.05 | -0.08 ❌ | -23.36 ❌ | 15 ⚠️ | RSI6 17 ⚪ · MFI 46 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | COSH.OL | 110.00 | 15.71 | -9.04 | -1.69 ❌ | -16.03 ❌ | 21 ⚪ | RSI6 5 ⚪ · MFI 25 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | ELABS.OL | 1.94 | 23.79 | -4.18 | -0.07 ❌ | -35.76 ❌ | 21 ⚪ | RSI6 13 ⚪ · MFI 21 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | ENSU.OL | 0.42 | 28.30 | -3.76 | -0.01 ◻️ | -23.19 ❌ | 37 🟢 | RSI6 28 ⚪ · MFI 23 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | ENVIP.OL | 32.45 | 34.22 | -2.46 | -0.75 ❌ | -12.47 ❌ | 18 ⚠️ | RSI6 17 ⚪ · MFI 12 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | GENO.OL | 14.12 | 28.51 | -1.33 | -0.33 ❌ | -26.05 ❌ | 30 🟢 | RSI6 18 ⚪ · MFI 17 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | HAUTO.OL | 155.10 | 30.71 | -1.82 | -1.41 ❌ | -11.49 ❌ | 21 ⚪ | RSI6 19 ⚪ · MFI 37 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | HAVI.OL | 0.70 | 31.86 | -5.43 | 0.00 ◻️ | -25.10 ❌ | 41 🟢 | RSI6 30 ⚪ · MFI 44 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | HYPRO.OL | 0.14 | 19.26 | -3.05 | -0.01 ◻️ | -64.32 ❌ | 33 🟢 | RSI6 8 ⚪ · MFI 5 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | IOX.OL | 1.57 | 20.50 | -2.98 | -0.04 ◻️ | -33.40 ❌ | 21 ⚪ | RSI6 7 ⚪ · MFI 45 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | KMAR.OL | 54.20 | 33.04 | -2.28 | -0.36 ❌ | -9.19 ❌ | 22 ⚪ | RSI6 24 ⚪ · MFI 26 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | LIFE.OL | 0.31 | 34.72 | -5.18 | -0.01 ◻️ | -20.93 ❌ | 28 🟢 | RSI6 21 ⚪ · MFI 15 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | LINK.OL | 22.32 | 32.49 | -7.54 | -0.31 ❌ | -8.48 ❌ | 17 ⚠️ | RSI6 18 ⚪ · MFI 36 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | MPCC.OL | 23.53 | 29.49 | -7.62 | -0.03 ◻️ | -13.56 ❌ | 32 🟢 | RSI6 20 ⚪ · MFI 53 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | NHY.OL | 63.66 | 29.18 | -0.75 | 0.00 ◻️ | -13.76 ❌ | 37 🟢 | RSI6 24 ⚪ · MFI 26 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | NRC.OL | 8.46 | 33.22 | -3.69 | -0.05 ❌ | -12.11 ❌ | 22 ⚪ | RSI6 24 ⚪ · MFI 21 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | NYKD.OL | 2.65 | 30.59 | -5.61 | 0.00 ◻️ | -18.12 ❌ | 25 🟢 | RSI6 28 ⚪ · MFI 33 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | PHO.OL | 39.60 | 29.14 | -1.38 | -0.08 ❌ | -15.82 ❌ | 37 🟢 | RSI6 27 ⚪ · MFI 17 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | PRS.OL | 3.55 | 27.11 | -0.75 | -0.07 ❌ | -22.21 ❌ | 34 🟢 | RSI6 18 ⚪ · MFI 27 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | REACH.OL | 4.20 | 19.85 | -0.05 | -0.14 ❌ | -28.92 ❌ | 40 🟢 | RSI6 15 ⚪ · MFI 25 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | SCATC.OL | 80.55 | 33.31 | -1.19 | -0.32 ❌ | -13.14 ❌ | 18 ⚠️ | RSI6 16 ⚪ · MFI 23 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | TGS.OL | 121.00 | 32.14 | -2.95 | -1.53 ❌ | -10.91 ❌ | 17 ⚠️ | RSI6 18 ⚪ · MFI 32 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | TOM.OL | 78.00 | 21.05 | -1.31 | -2.25 ❌ | -16.14 ❌ | 36 🟢 | RSI6 9 ⚪ · MFI 11 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | TRMED.OL | 3.69 | 33.11 | -4.09 | -0.02 ◻️ | -13.84 ❌ | 33 🟢 | RSI6 27 ⚪ · MFI 32 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | VAR.OL | 43.49 | 24.47 | -2.64 | -0.60 ❌ | -14.95 ❌ | 38 🟢 | RSI6 11 ⚪ · MFI 14 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | VOIM.OL | 0.10 | 30.44 | -2.28 | 0.00 ◻️ | -57.41 ❌ | 20 ⚪ | RSI6 24 ⚪ · MFI 43 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | VOW.OL | 2.06 | 25.47 | -3.60 | -0.06 ❌ | -26.33 ❌ | 26 🟢 | RSI6 19 ⚪ · MFI 25 ⚪ |

**ABG.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 1,819,758; NOK 100k / 500k orders = 5.50% / 27.48% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**AGLX.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 442,866; NOK 100k / 500k orders = 22.58% / 112.90% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**AKAST.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 9,972,487; NOK 100k / 500k orders = 1.00% / 5.01% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**AKER.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 104,535,145; NOK 100k / 500k orders = 0.10% / 0.48% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**AKSO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 11,700,646; NOK 100k / 500k orders = 0.85% / 4.27% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**BNOR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 45,322,672; NOK 100k / 500k orders = 0.22% / 1.10% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**CAVEN.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 73,597; NOK 100k / 500k orders = 135.88% / 679.38% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**COSH.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 17,482,059; NOK 100k / 500k orders = 0.57% / 2.86% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**ELABS.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 536,039; NOK 100k / 500k orders = 18.66% / 93.28% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**ENSU.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 537,584; NOK 100k / 500k orders = 18.60% / 93.01% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**ENVIP.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 16,514,384; NOK 100k / 500k orders = 0.61% / 3.03% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**GENO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 4,386,432; NOK 100k / 500k orders = 2.28% / 11.40% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HAUTO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 53,746,838; NOK 100k / 500k orders = 0.19% / 0.93% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HAVI.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 122,484; NOK 100k / 500k orders = 81.64% / 408.22% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HYPRO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 227,285; NOK 100k / 500k orders = 44.00% / 219.99% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**IOX.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 116,000; NOK 100k / 500k orders = 86.21% / 431.03% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**KMAR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 61,915,635; NOK 100k / 500k orders = 0.16% / 0.81% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**LIFE.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 989,712; NOK 100k / 500k orders = 10.10% / 50.52% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**LINK.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 16,716,732; NOK 100k / 500k orders = 0.60% / 2.99% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**MPCC.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 32,152,621; NOK 100k / 500k orders = 0.31% / 1.56% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NHY.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 285,210,239; NOK 100k / 500k orders = 0.04% / 0.18% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NRC.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 3,206,088; NOK 100k / 500k orders = 3.12% / 15.60% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NYKD.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 2,139,131; NOK 100k / 500k orders = 4.67% / 23.37% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**PHO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 3,544,538; NOK 100k / 500k orders = 2.82% / 14.11% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**PRS.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 5,629,714; NOK 100k / 500k orders = 1.78% / 8.88% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**REACH.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 1,782,518; NOK 100k / 500k orders = 5.61% / 28.05% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**SCATC.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 65,829,397; NOK 100k / 500k orders = 0.15% / 0.76% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**TGS.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 48,959,177; NOK 100k / 500k orders = 0.20% / 1.02% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**TOM.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 64,785,073; NOK 100k / 500k orders = 0.15% / 0.77% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**TRMED.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 7,182,125; NOK 100k / 500k orders = 1.39% / 6.96% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**VAR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 311,641,692; NOK 100k / 500k orders = 0.03% / 0.16% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**VOIM.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 83,482; NOK 100k / 500k orders = 119.79% / 598.93% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**VOW.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 2,456,247; NOK 100k / 500k orders = 4.07% / 20.36% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


## SELL-watch — reduction/exit review, not short (alphabetical)

| Missing setup conditions (not ranked) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|:-------|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | HUNT.OL | 20.95 | 65.61 | +1.52 | 0.45 ❌ | 19.06 ❌ | 15 ⚠️ | RSI6 76 ⚪ · MFI 75 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | IDEX.OL | 10.90 | 76.39 | +1.34 | 0.21 ❌ | 47.47 ❌ | 38 🟢 | RSI6 82 ⚪ · MFI 83 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | KID.OL | 149.00 | 71.15 | +4.31 | -0.36 ✅ | 12.55 ❌ | 47 🟢 | RSI6 74 ⚪ · MFI 54 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | MEDI.OL | 330.00 | 75.08 | +2.22 | -0.09 ✅ | 15.25 ❌ | 36 🟢 | RSI6 84 ⚪ · MFI 66 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | MORLD.OL | 27.95 | 69.81 | +2.81 | 0.07 ❌ | 15.76 ❌ | 26 🟢 | RSI6 76 ⚪ · MFI 69 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | NKR.OL | 20.90 | 77.07 | +0.98 | 0.07 ❌ | 26.97 ❌ | 51 🟢 | RSI6 82 ⚪ · MFI 79 ⚪ |

**HUNT.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 63,644,361; NOK 100k / 500k orders = 0.16% / 0.79% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**IDEX.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 2,092,238; NOK 100k / 500k orders = 4.78% / 23.90% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**KID.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 10,064,436; NOK 100k / 500k orders = 0.99% / 4.97% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**MEDI.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 4,778,370; NOK 100k / 500k orders = 2.09% / 10.46% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**MORLD.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 9,256,967; NOK 100k / 500k orders = 1.08% / 5.40% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NKR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-09-03 to 2026-11-25, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 3,716,550; NOK 100k / 500k orders = 2.69% / 13.45% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


## Aksjer uten nødvendige data

Disse aksjene er ikke med i signallistene. Manglende data betyr ikke at en aksje er avnotert.

| Aksje | Datastatus | Observasjonsdato | Årsak |
|---|---|---|---|
| CADLR.OL | stale | 2026-11-05 | missing_expected_completed_session |
| GYL.OL | stale | 2026-11-24 | missing_expected_completed_session |
| HSPG.OL | stale | 2026-11-24 | missing_expected_completed_session |
| OUTLT.OL | invalid | 2026-11-25 | insufficient_indicator_warmup |
| SKUE.OL | stale | 2026-11-24 | missing_expected_completed_session |
| TRSB.OL | stale | 2026-11-24 | missing_expected_completed_session |


---

**Kontroller:** Datakontroll: avsluttet handelssesjon, raddekning og snapshot-integritet verifisert. Datastatus degraded; begrensninger: ingen strukturelle avvik.

_Event- og fundamentaldekning: ikke tilgjengelig i denne tekniske screeningen. BUY/SELL er tekniske oppsett, ikke verifiserte handelsanbefalinger._
