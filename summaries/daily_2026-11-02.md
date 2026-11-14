# Oslo Børs – Teknisk dagsrapport

Research-only rebound setups. SELL denotes an existing-holder reduction/exit review, never a short instruction. Fixed stop distances and position percentages are legacy heuristics, not executable stops, recommended allocations or loss budgets. Separate KE activity/capacity evidence follows each list. Execution suitability remains unverified; no new liquidity cutoff is introduced.

<!-- snapshot_id=44ec1656abdf4e33a8ed07a2d9c08b18 -->

**Forventet avsluttet handelssesjon:** 02.11.2026

**Datastatus:** CURRENT · 199/199 aktuelle rader

**Generert:** 2026-11-03T14:04:15Z · snapshot 44ec1656abdf4e33a8ed07a2d9c08b18


**Samlet prosentkrav er midlertidig suspendert. Bare aksjer med aktuelle, gyldige data kan gi signaler.**

**Utelatte aksjer:** 0. Full liste med årsaker står nedenfor.

**Telling:** BUY 3 | SELL 2 | BUY-watch 20 | SELL-watch 8


## Rebound setups — review (legacy BUY codes)

| Context count (heuristic) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|---:|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| 1 | OTEC.OL | 17.24 | 31.90 | +1.52 | -0.58 ❌ | -9.76 ❌ | 30 🟢 | RSI6 20 ⚠️ · MFI 30 🔴 |
| 1 | HEX.OL | 11.18 | 34.87 | +0.51 | -0.06 ❌ | -10.79 ❌ | 27 🟢 | RSI6 29 ⚪ · MFI 25 🔴 |
| 0 | NOM.OL | 0.47 | 31.37 | +1.18 | 0.04 ◻️ | -63.78 ❌ | 12 ⚠️ | RSI6 32 ⚪ · MFI 45 ⚪ |

**OTEC.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 2,644,016; NOK 100k / 500k orders = 3.78% / 18.91% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HEX.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 11,536,500; NOK 100k / 500k orders = 0.87% / 4.33% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NOM.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 934,272; NOK 100k / 500k orders = 10.70% / 53.52% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


**Example rule qualification (not a validated priority)**

OTEC.OL kvalifiserte via gatekeeper (RSI≤35 & opp-dag). ADX≥25 (🟢).


## Reduction/exit review setups — not short (legacy SELL codes)

| Context count (heuristic) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|---:|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| 1 | DNO.OL | 23.76 | 71.13 | -11.72 | 0.11 ❌ | 18.09 ❌ | 47 🟢 | RSI6 62 ⚪ · MFI 87 🔴 |
| 1 | BOUV.OL | 53.10 | 68.50 | -8.33 | 0.53 ❌ | 9.01 ❌ | 36 🟢 | RSI6 70 ⚪ · MFI 68 🔴 |

**DNO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 93,328,967; NOK 100k / 500k orders = 0.11% / 0.54% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**BOUV.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 4,816,626; NOK 100k / 500k orders = 2.08% / 10.38% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


**Example rule qualification (not a validated priority)**

DNO.OL kvalifiserte via gatekeeper (RSI≥65 & ned-dag). ADX≥25 (🟢).


## BUY-watch — rebound review (alphabetical, not proximity-ranked)

| Missing setup conditions (not ranked) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|:-------|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | AKER.OL | 1118.00 | 24.21 | -4.20 | -1.62 ❌ | -20.63 ❌ | 42 🟢 | RSI6 19 ⚪ · MFI 38 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | AKSO.OL | 35.52 | 29.70 | -1.88 | -0.29 ❌ | -12.73 ❌ | 28 🟢 | RSI6 22 ⚪ · MFI 28 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | ARCH.OL | 17.72 | 27.89 | -2.43 | -0.21 ❌ | -19.31 ❌ | 28 🟢 | RSI6 23 ⚪ · MFI 21 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | BWE.OL | 51.80 | 26.40 | -3.67 | -1.86 ❌ | -12.79 ❌ | 34 🟢 | RSI6 9 ⚪ · MFI 17 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | DELIA.OL | 17.30 | 34.56 | -1.38 | 0.05 ✅ | -14.62 ❌ | 27 🟢 | RSI6 32 ⚪ · MFI 39 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | GSF.OL | 22.52 | 32.87 | -2.38 | 0.10 ✅ | -10.85 ❌ | 38 🟢 | RSI6 29 ⚪ · MFI 77 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | HAVI.OL | 0.81 | 28.54 | -0.57 | -0.02 ◻️ | -23.28 ❌ | 38 🟢 | RSI6 17 ⚪ · MFI 28 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | HBC.OL | 1.16 | 29.86 | -1.95 | -0.02 ◻️ | -13.30 ❌ | 15 ⚠️ | RSI6 12 ⚪ · MFI 17 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | HSHP.OL | 146.80 | 33.16 | -4.00 | -0.99 ❌ | -10.27 ❌ | 17 ⚠️ | RSI6 20 ⚪ · MFI 25 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | NAVA.OL | 10.80 | 30.09 | -2.04 | -0.20 ❌ | -18.83 ❌ | 20 ⚪ | RSI6 23 ⚪ · MFI 23 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | NHY.OL | 65.98 | 20.37 | -0.21 | -0.42 ❌ | -19.60 ❌ | 48 🟢 | RSI6 16 ⚪ · MFI 32 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | NSKOG.OL | 34.85 | 26.45 | -3.76 | -0.48 ❌ | -23.00 ❌ | 31 🟢 | RSI6 18 ⚪ · MFI 23 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | NYKD.OL | 2.91 | 28.40 | -3.07 | -0.01 ◻️ | -21.05 ❌ | 25 🟢 | RSI6 15 ⚪ · MFI 28 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | ONCIN.OL | 65.40 | 30.72 | -4.90 | 0.97 ✅ | -25.90 ❌ | 21 ⚪ | RSI6 25 ⚪ · MFI 41 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | PHO.OL | 45.85 | 30.95 | -2.09 | -0.27 ❌ | -9.85 ❌ | 19 ⚠️ | RSI6 20 ⚪ · MFI 29 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | SALME.OL | 2.41 | 19.07 | -0.17 | -0.06 ❌ | -26.58 ❌ | 25 ⚪ | RSI6 7 ⚪ · MFI 15 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | SOMA.OL | 27.30 | 33.22 | -5.02 | -0.22 ❌ | -5.33 ❌ | 23 ⚪ | RSI6 18 ⚪ · MFI 46 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | TRMED.OL | 3.94 | 31.01 | -1.98 | -0.01 ◻️ | -17.03 ❌ | 20 ⚪ | RSI6 24 ⚪ · MFI 34 ⚪ |
| RSI <=35 met; Needs up-close (current down); SMA50/MACD are confirmations only, not missing hard gates | VOIM.OL | 0.10 | 22.55 | -1.47 | -0.01 ◻️ | -66.82 ❌ | 19 ⚠️ | RSI6 13 ⚪ · MFI 23 ⚪ |
| RSI <=35 met; Needs up-close (current flat); SMA50/MACD are confirmations only, not missing hard gates | ZLNA.OL | 17.20 | 32.42 | +0.00 | -0.04 ◻️ | -15.99 ❌ | 9 ⚠️ | RSI6 21 ⚪ · MFI 41 ⚪ |

**AKER.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 174,700,432; NOK 100k / 500k orders = 0.06% / 0.29% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**AKSO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 19,899,044; NOK 100k / 500k orders = 0.50% / 2.51% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**ARCH.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 4,133,497; NOK 100k / 500k orders = 2.42% / 12.10% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**BWE.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 9,364,197; NOK 100k / 500k orders = 1.07% / 5.34% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**DELIA.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 835,178; NOK 100k / 500k orders = 11.97% / 59.87% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**GSF.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 5,418,346; NOK 100k / 500k orders = 1.85% / 9.23% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HAVI.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 181,221; NOK 100k / 500k orders = 55.18% / 275.91% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HBC.OL**: KE suitability: Ineligible under daily-trading requirement: vendor reports 1/60 zero-volume sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 86,038; NOK 100k / 500k orders = 116.23% / 581.14% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**HSHP.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 19,999,534; NOK 100k / 500k orders = 0.50% / 2.50% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NAVA.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 287,480; NOK 100k / 500k orders = 34.78% / 173.92% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NHY.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 258,932,835; NOK 100k / 500k orders = 0.04% / 0.19% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NSKOG.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 10,499,619; NOK 100k / 500k orders = 0.95% / 4.76% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**NYKD.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 2,210,830; NOK 100k / 500k orders = 4.52% / 22.62% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**ONCIN.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 1,355,361; NOK 100k / 500k orders = 7.38% / 36.89% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**PHO.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 1,637,540; NOK 100k / 500k orders = 6.11% / 30.53% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**SALME.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 2,256,083; NOK 100k / 500k orders = 4.43% / 22.16% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**SOMA.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 3,313,834; NOK 100k / 500k orders = 3.02% / 15.09% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**TRMED.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 8,970,772; NOK 100k / 500k orders = 1.11% / 5.57% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**VOIM.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 77,889; NOK 100k / 500k orders = 128.39% / 641.94% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**ZLNA.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 285,230; NOK 100k / 500k orders = 35.06% / 175.30% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


## SELL-watch — reduction/exit review, not short (alphabetical)

| Missing setup conditions (not ranked) | Ticker | Close | RSI14 | ΔRSI | MACD | SMA% | ADX | Sec. |
|:-------|:------|-----:|-----:|-----:|:----:|:----:|:---:|:----|
| RSI >=65 met; Needs down-close (current flat); SMA50/MACD are confirmations only, not missing hard gates | AKVA.OL | 158.00 | 72.12 | +0.00 | -0.64 ✅ | 6.60 ❌ | 48 🟢 | RSI6 65 ⚪ · MFI 47 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | ENDUR.OL | 128.40 | 70.93 | +4.72 | 0.79 ❌ | 14.23 ❌ | 28 🟢 | RSI6 81 ⚪ · MFI 68 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | KOG.OL | 357.60 | 74.15 | +0.52 | 6.33 ❌ | 14.71 ❌ | 20 ⚠️ | RSI6 89 ⚪ · MFI 81 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | MEDI.OL | 307.00 | 74.16 | +0.97 | 1.46 ❌ | 16.25 ❌ | 47 🟢 | RSI6 76 ⚪ · MFI 82 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | MOWI.OL | 218.40 | 67.15 | +1.10 | 0.51 ❌ | 5.92 ❌ | 34 🟢 | RSI6 72 ⚪ · MFI 62 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | SMOP.OL | 57.00 | 65.15 | +1.54 | 0.87 ❌ | 17.18 ❌ | 20 ⚪ | RSI6 75 ⚪ · MFI 64 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | STECH.OL | 89.60 | 67.29 | +1.41 | 0.65 ❌ | 6.36 ❌ | 26 🟢 | RSI6 79 ⚪ · MFI 86 ⚪ |
| RSI >=65 met; Needs down-close (current up); SMA50/MACD are confirmations only, not missing hard gates | TEL.OL | 132.20 | 67.80 | +1.01 | 1.03 ❌ | 4.29 ❌ | 29 🟢 | RSI6 83 ⚪ · MFI 83 ⚪ |

**AKVA.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 1,297,934; NOK 100k / 500k orders = 7.70% / 38.52% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**ENDUR.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 16,587,180; NOK 100k / 500k orders = 0.60% / 3.01% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**KOG.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 322,197,246; NOK 100k / 500k orders = 0.03% / 0.16% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**MEDI.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 3,441,794; NOK 100k / 500k orders = 2.91% / 14.53% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**MOWI.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 220,406,439; NOK 100k / 500k orders = 0.05% / 0.23% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**SMOP.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 10,926,085; NOK 100k / 500k orders = 0.92% / 4.58% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**STECH.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 391,242; NOK 100k / 500k orders = 25.56% / 127.80% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.

**TEL.OL**: KE suitability: Daily activity: vendor reports positive volume on 60/60 expected open sessions (window 2026-08-11 to 2026-11-02, Yahoo Finance). 20-session median unadjusted-close × volume proxy NOK 246,290,595; NOK 100k / 500k orders = 0.04% / 0.20% of proxy. Execution suitability unverified; not exchange-confirmed turnover, depth or guaranteed fills. No safe participation cutoff assumed.


## Aksjer uten nødvendige data

Disse aksjene er ikke med i signallistene. Manglende data betyr ikke at en aksje er avnotert.

Ingen aksjer er utelatt.


---

**Kontroller:** Datakontroll: avsluttet handelssesjon, raddekning og snapshot-integritet verifisert. Datastatus current; begrensninger: ingen strukturelle avvik.

_Event- og fundamentaldekning: ikke tilgjengelig i denne tekniske screeningen. BUY/SELL er tekniske oppsett, ikke verifiserte handelsanbefalinger._
