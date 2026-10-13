# Consolidated results (patched data; facts and tables only)

Test split 2022-01-03..2026-10-09. RL cells: mean [95% t-interval over 10 seeds; turnover: bootstrap percentile interval]. Baseline cells: single deterministic run; Sharpe cell has a block-bootstrap 95% interval; the other baseline metrics have no interval.
RL models were trained before the data patch and re-scored on the patched data without retraining (see section b). The KSE-100 is a PRICE index (no dividends), so it understates the benchmark; no reliable total-return series was found and none was invented. RL turnover intervals are bootstrap percentile intervals over seeds (10,000 resamples), so they cannot go below zero.

## a) Main 29-stock results, 0% (before cost) cost per side

| Strategy | Annual return | Volatility | Sharpe | Max drawdown | Turnover/yr |
|---|---|---|---|---|---|
| Buy-and-hold | 40.5% | 23.6% | 0.91 [-0.00, 1.89] | -25.5% | 0.04 |
| Equal-weight monthly | 41.1% | 24.1% | 0.91 [-0.05, 1.93] | -25.1% | 0.44 |
| Mean-variance monthly | 44.2% | 25.0% | 0.98 [-0.04, 1.98] | -32.2% | 0.45 |
| KSE-100 (price index, excl. dividends) | 31.8% | 20.2% | 0.71 [-0.16, 1.67] | -22.6% | n/a |
| A2C (10-seed mean) | 41.7% [35.9, 47.5] | 28.1% [27.2, 29.1] | 0.83 [0.68, 0.98] | -29.2% [-32.2, -26.3] | 0.07 [0.05, 0.10] |
| PPO (10-seed mean) | 37.5% [33.1, 41.9] | 23.8% [22.5, 25.1] | 0.82 [0.67, 0.96] | -26.3% [-28.6, -24.0] | 0.79 [0.54, 1.07] |
| DDPG (10-seed mean) | 36.4% [27.4, 45.3] | 26.8% [24.1, 29.5] | 0.73 [0.48, 0.99] | -29.6% [-35.4, -23.8] | 7.69 [4.37, 10.53] |

Sharpe difference (algorithm minus baseline), circular block bootstrap: smallest p = 0.267; comparisons with p < 0.05: 0 of 12.
No RL agent significantly beats the baselines even at zero cost (smallest p = 0.27).


## a) Main 29-stock results, 0.1% cost per side

| Strategy | Annual return | Volatility | Sharpe | Max drawdown | Turnover/yr |
|---|---|---|---|---|---|
| Buy-and-hold | 40.5% | 23.6% | 0.91 [-0.01, 1.88] | -25.5% | 0.04 |
| Equal-weight monthly | 40.9% | 24.1% | 0.91 [-0.05, 1.90] | -25.1% | 0.44 |
| Mean-variance monthly | 44.1% | 25.0% | 0.97 [-0.06, 2.01] | -32.3% | 0.45 |
| KSE-100 (price index, excl. dividends) | 31.8% | 20.2% | 0.71 [-0.16, 1.64] | -22.6% | n/a |
| A2C (10-seed mean) | 41.1% [35.9, 46.3] | 26.1% [24.4, 27.9] | 0.85 [0.73, 0.98] | -27.0% [-30.0, -24.1] | 0.12 [0.05, 0.24] |
| PPO (10-seed mean) | 37.1% [32.7, 41.4] | 23.8% [22.6, 25.1] | 0.80 [0.65, 0.95] | -26.1% [-29.0, -23.2] | 0.77 [0.56, 0.98] |
| DDPG (10-seed mean) | 35.0% [28.9, 41.1] | 25.6% [23.8, 27.4] | 0.70 [0.50, 0.90] | -28.8% [-33.1, -24.5] | 7.08 [3.39, 10.70] |

Sharpe difference (algorithm minus baseline), circular block bootstrap: smallest p = 0.172; comparisons with p < 0.05: 0 of 12.

## a) Main 29-stock results, 0.18% (realistic PSX/CDC/SECP) cost per side

| Strategy | Annual return | Volatility | Sharpe | Max drawdown | Turnover/yr |
|---|---|---|---|---|---|
| Buy-and-hold | 40.5% | 23.6% | 0.91 [0.01, 1.85] | -25.5% | 0.04 |
| Equal-weight monthly | 40.8% | 24.1% | 0.90 [-0.08, 1.90] | -25.1% | 0.44 |
| Mean-variance monthly | 43.9% | 25.0% | 0.97 [-0.02, 2.01] | -32.3% | 0.45 |
| KSE-100 (price index, excl. dividends) | 31.8% | 20.2% | 0.71 [-0.19, 1.67] | -22.6% | n/a |
| A2C (10-seed mean) | 39.1% [33.9, 44.2] | 25.9% [24.0, 27.9] | 0.81 [0.67, 0.94] | -27.0% [-30.8, -23.2] | 0.09 [0.06, 0.12] |
| PPO (10-seed mean) | 38.0% [33.3, 42.8] | 23.8% [22.4, 25.2] | 0.83 [0.68, 0.97] | -26.2% [-28.9, -23.5] | 0.76 [0.54, 0.99] |
| DDPG (10-seed mean) | 38.6% [32.6, 44.6] | 26.0% [23.2, 28.8] | 0.80 [0.63, 0.98] | -28.5% [-32.9, -24.0] | 3.59 [0.27, 7.10] |

Sharpe difference (algorithm minus baseline), circular block bootstrap: smallest p = 0.422; comparisons with p < 0.05: 0 of 12.

## b) Effect of the PSX data patch (test Sharpe before -> after)

Patch: rows restored/added/date-corrected for MARI, LUCK, BAFL, SYS, UBL from PSX tables; PAEL pre-2013-08-29 rescale 0.7031 (2014 bonus not applied). Trained models re-scored, not retrained; the PAEL change touches training data, so its effect on trained agents is unmeasured.

| Cost/side | Strategy | Before | After | Change |
|---|---|---|---|---|
| 0.1% | A2C (RL (10-seed mean)) | 0.8534 | 0.8534 | +0.0000 |
| 0.1% | DDPG (RL (10-seed mean)) | 0.6995 | 0.6998 | +0.0004 |
| 0.1% | PPO (RL (10-seed mean)) | 0.8011 | 0.8011 | -0.0000 |
| 0.18% | A2C (RL (10-seed mean)) | 0.8078 | 0.8078 | -0.0001 |
| 0.18% | DDPG (RL (10-seed mean)) | 0.8035 | 0.8030 | -0.0004 |
| 0.18% | PPO (RL (10-seed mean)) | 0.8269 | 0.8270 | +0.0001 |
| 0.1% | buy_and_hold (baseline) | 0.9091 | 0.9093 | +0.0001 |
| 0.1% | equal_weight_monthly (baseline) | 0.9061 | 0.9062 | +0.0001 |
| 0.1% | kse100_benchmark (baseline) | 0.7059 | 0.7059 | +0.0000 |
| 0.1% | mean_variance_monthly (baseline) | 0.9640 | 0.9715 | +0.0075 |
| 0.18% | buy_and_hold (baseline) | 0.9085 | 0.9086 | +0.0001 |
| 0.18% | equal_weight_monthly (baseline) | 0.9028 | 0.9029 | +0.0001 |
| 0.18% | kse100_benchmark (baseline) | 0.7059 | 0.7059 | +0.0000 |
| 0.18% | mean_variance_monthly (baseline) | 0.9607 | 0.9682 | +0.0075 |

All 35 rows (5 cost levels): max |Sharpe change| = 0.0075 (mean_variance_monthly, 0%). Significance: 60 comparisons, 0 with p < 0.05 before and after; max change in a Sharpe difference 0.0097. Full table: `results/patch_effect.csv`.

## c) Small-break scan (`data/small_breaks.csv`)

Scan of all 29 tickers for 5-30% daily close moves, compared with adj_close; re-run on the PATCHED data (the pre-patch output is kept as `data/small_breaks_prepatch.csv`). Candidates are not corrections: nothing in data/clean was changed because of this scan.

- Candidates: 3546; adj_close status: NOT adjusted 3421, partly adjusted 65, adjusted 60; persistent (level shift that stays): 2474; beyond the empirical daily price limit (7.5% until mid-2024, 10% after): 296.
- Flagged 'CHECK: drop beyond daily limit, not market-wide, adj_close did not (fully) adjust': 46 rows (34 persistent), in 16 tickers: PAEL 8, PTC 7, KEL 4, BOP 4, SEARL 3, UBL 3, FATIMA 3, MARI 3, POL 2, NBP 2, BAFL 2, MLCF 1, HUBC 1, MEBL 1, NRL 1, EFERT 1.
- Review status (column review_status): 45 of the 46 flagged rows are unverified; the others lie within 20 days of a split event checked against PSX tables (`data/split_events.csv`: MARI, LUCK, BAFL, SYS, UBL, PAEL). Before the patch: 46 flagged rows in 16 tickers, i.e. the patch changed neither the flagged count nor the tickers (candidates 3,547 -> 3,546).

Largest flagged rows:

| Ticker | Date | Close return | adj_close status | Persistent |
|---|---|---|---|---|
| NBP | 2017-04-06 | -18.9% | partly adjusted | True |
| MARI | 2015-05-14 | -12.7% | NOT adjusted | True |
| NBP | 2015-03-19 | -12.1% | partly adjusted | True |
| SEARL | 2025-09-30 | -11.8% | NOT adjusted | True |
| BOP | 2015-03-27 | -11.3% | NOT adjusted | True |
| BAFL | 2013-03-21 | -11.1% | partly adjusted | True |
| BOP | 2013-01-15 | -10.7% | NOT adjusted | False |
| BOP | 2023-10-30 | -10.4% | NOT adjusted | False |
| POL | 2015-09-10 | -10.1% | partly adjusted | True |
| MEBL | 2020-03-17 | -9.8% | partly adjusted | True |
| BAFL | 2024-03-13 | -9.8% | partly adjusted | True |
| KEL | 2021-10-01 | -9.5% | NOT adjusted | False |
| KEL | 2024-02-12 | -9.5% | NOT adjusted | True |
| PAEL | 2013-01-15 | -9.3% | NOT adjusted | False |
| FATIMA | 2017-04-14 | -9.2% | partly adjusted | True |

## d) Cost sensitivity (test Sharpe; RL mean [95% CI over 10 seeds]; patched data)

|   cost_per_side | A2C               | DDPG              | PPO               |   buy_and_hold |   equal_weight_monthly |   mean_variance_monthly |   KSE-100 (price index, excl. dividends) |
|----------------:|:------------------|:------------------|:------------------|---------------:|-----------------------:|------------------------:|-----------------------------------------:|
|          0      | 0.83 [0.68, 0.98] | 0.73 [0.48, 0.99] | 0.82 [0.67, 0.96] |           0.91 |                   0.91 |                    0.98 |                                     0.71 |
|          0.001  | 0.85 [0.73, 0.98] | 0.70 [0.50, 0.90] | 0.80 [0.65, 0.95] |           0.91 |                   0.91 |                    0.97 |                                     0.71 |
|          0.0018 | 0.81 [0.67, 0.94] | 0.80 [0.63, 0.98] | 0.83 [0.68, 0.97] |           0.91 |                   0.9  |                    0.97 |                                     0.71 |
|          0.0025 | 0.77 [0.61, 0.94] | 0.71 [0.58, 0.83] | 0.81 [0.69, 0.93] |           0.91 |                   0.9  |                    0.97 |                                     0.71 |
|          0.005  | 0.78 [0.60, 0.96] | 0.56 [0.21, 0.91] | 0.80 [0.65, 0.95] |           0.91 |                   0.89 |                    0.96 |                                     0.71 |

## d) Walk-forward (0.1% cost; patched data; RL models trained pre-patch and re-scored)

| window   | test_period   | A2C                  | DDPG                 | PPO                  |   buy_and_hold |   equal_weight_monthly |   mean_variance_monthly |   KSE-100 (price index, excl. dividends) |
|:---------|:--------------|:---------------------|:---------------------|:---------------------|---------------:|-----------------------:|------------------------:|-----------------------------------------:|
| w1       | 2018-2019     | -0.80 [-0.96, -0.64] | -0.75 [-0.89, -0.61] | -0.82 [-0.97, -0.66] |          -0.34 |                  -0.33 |                   -0.35 |                                    -0.45 |
| w2       | 2020-2021     | -0.06 [-0.20, 0.08]  | -0.13 [-0.31, 0.05]  | 0.15 [-0.05, 0.35]   |           0.3  |                   0.16 |                    0.09 |                                    -0.12 |
| main     | 2022-2026     | 0.85 [0.73, 0.98]    | 0.70 [0.50, 0.90]    | 0.80 [0.65, 0.95]    |           0.91 |                   0.91 |                    0.97 |                                     0.71 |
