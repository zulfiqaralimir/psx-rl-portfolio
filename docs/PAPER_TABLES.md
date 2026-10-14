# Paper tables (patched data)

All results use the patched price data (`data/patch/`, applied 2026-10-13). Test period 2022-01-03 to 2026-10-09 unless stated. Sharpe is over the SBP policy rate. Turnover = one-way traded value / mean asset value / year. Agents are 10-seed means; Sharpe CI for agents = 95% t-interval over seeds, for baselines = circular block bootstrap of test days (block 20, 4,000 draws); turnover CI for agents = percentile bootstrap over seeds (baselines are deterministic). Regenerate with `python scripts/make_paper_tables.py`.

## Table 1a: test results at 0.18% per side (realistic PSX/CDC/SECP fees)

Agents are retrained on the patched data at this cost.

| Strategy | Annual return | Volatility | Sharpe [95% CI] | Max drawdown | Turnover/yr [95% CI] |
|---|---|---|---|---|---|
| Buy-and-hold | 40.5% | 23.6% | 0.91 [0.01, 1.87] | -25.5% | 0.04 (deterministic) |
| Equal-weight monthly | 40.8% | 24.1% | 0.90 [-0.03, 1.90] | -25.1% | 0.44 (deterministic) |
| Mean-variance monthly | 43.9% | 25.0% | 0.97 [-0.05, 1.99] | -32.3% | 0.45 (deterministic) |
| KSE-100 (price index, excl. dividends) | 31.8% | 20.2% | 0.71 [-0.18, 1.67] | -22.6% | n/a |
| A2C (10-seed mean) | 39.8% | 26.2% | 0.82 [0.69, 0.96] | -27.5% | 0.08 [0.06, 0.10] |
| PPO (10-seed mean) | 36.4% | 23.7% | 0.78 [0.64, 0.92] | -25.5% | 0.73 [0.55, 0.91] |
| DDPG (10-seed mean) | 38.1% | 26.3% | 0.79 [0.66, 0.91] | -29.2% | 4.87 [1.26, 8.60] |

*Significance at 0.18% cost: 12 comparisons (algorithm vs baseline, Sharpe difference, circular block bootstrap), 0 with p < 0.05, smallest p = 0.355 (DDPG vs buy and hold).*

## Table 1b: test results at 0.1% per side

Agents are retrained on the patched data at this cost.

| Strategy | Annual return | Volatility | Sharpe [95% CI] | Max drawdown | Turnover/yr [95% CI] |
|---|---|---|---|---|---|
| Buy-and-hold | 40.5% | 23.6% | 0.91 [0.01, 1.87] | -25.5% | 0.04 (deterministic) |
| Equal-weight monthly | 40.9% | 24.1% | 0.91 [-0.02, 1.90] | -25.1% | 0.44 (deterministic) |
| Mean-variance monthly | 44.1% | 25.0% | 0.97 [-0.04, 1.99] | -32.3% | 0.45 (deterministic) |
| KSE-100 (price index, excl. dividends) | 31.8% | 20.2% | 0.71 [-0.18, 1.67] | -22.6% | n/a |
| A2C (10-seed mean) | 40.2% | 27.4% | 0.81 [0.65, 0.97] | -28.5% | 0.13 [0.06, 0.25] |
| PPO (10-seed mean) | 36.6% | 24.0% | 0.78 [0.67, 0.89] | -26.9% | 0.82 [0.59, 1.06] |
| DDPG (10-seed mean) | 37.5% | 25.7% | 0.78 [0.66, 0.90] | -27.7% | 5.51 [2.38, 8.80] |

*Significance at 0.1% cost: 12 comparisons (algorithm vs baseline, Sharpe difference, circular block bootstrap), 0 with p < 0.05, smallest p = 0.393 (DDPG vs equal weight monthly).*

## Table 2: test Sharpe by cost per side (agents: mean [95% CI over 10 seeds]; baselines: Sharpe [95% block-bootstrap CI])

| Cost/side | Agents | A2C | PPO | DDPG | Buy-and-hold | Equal-weight monthly | Mean-variance monthly | KSE-100 |
|---|---|---|---|---|---|---|---|---|
| 0% | retrained | 0.82 [0.67, 0.97] | 0.82 [0.67, 0.96] | 0.73 [0.62, 0.84] | 0.91 [0.01, 1.87] | 0.91 [-0.02, 1.91] | 0.98 [-0.04, 2.00] | 0.71 [-0.18, 1.67] |
| 0.1% | retrained | 0.81 [0.65, 0.97] | 0.78 [0.67, 0.89] | 0.78 [0.66, 0.90] | 0.91 [0.01, 1.87] | 0.91 [-0.02, 1.90] | 0.97 [-0.04, 1.99] | 0.71 [-0.18, 1.67] |
| 0.18% | retrained | 0.82 [0.69, 0.96] | 0.78 [0.64, 0.92] | 0.79 [0.66, 0.91] | 0.91 [0.01, 1.87] | 0.90 [-0.03, 1.90] | 0.97 [-0.05, 1.99] | 0.71 [-0.18, 1.67] |
| 0.25% | re-scored | 0.77 [0.61, 0.94] | 0.81 [0.69, 0.93] | 0.71 [0.58, 0.83] | 0.91 [0.01, 1.87] | 0.90 [-0.03, 1.90] | 0.97 [-0.05, 1.99] | 0.71 [-0.18, 1.67] |
| 0.5% | re-scored | 0.78 [0.60, 0.96] | 0.80 [0.65, 0.95] | 0.56 [0.21, 0.91] | 0.91 [0.01, 1.87] | 0.89 [-0.04, 1.89] | 0.96 [-0.06, 1.98] | 0.71 [-0.18, 1.67] |

*Retrained* = agents trained from scratch on the patched data at that cost (seeds 0-9). *Re-scored* = checkpoints trained before the patch, evaluated on the patched test split (the price patch changes test-split rows from 2025-04; the PAEL rescale also changes 165 PAEL training rows, 2013-01-01 to 2013-08-28, by +5.5%, which these checkpoints did not see). Baselines are recomputed at each cost.

*Significance across all five cost levels: 60 comparisons (algorithm vs baseline, Sharpe difference, circular block bootstrap), 0 with p < 0.05, smallest p = 0.053 (DDPG vs buy and hold).*

## Table 3: walk-forward test Sharpe (0.1% cost; agents: mean [95% CI over 10 seeds]; baselines: point Sharpe)

| Window | Test period | A2C | PPO | DDPG | Buy-and-hold | Equal-weight monthly | Mean-variance monthly | KSE-100 (price index) |
|---|---|---|---|---|---|---|---|---|
| w1 | 2018-2019 | -0.80 [-0.96, -0.64] | -0.82 [-0.97, -0.66] | -0.75 [-0.89, -0.61] | -0.34 | -0.33 | -0.35 | -0.45 |
| w2 | 2020-2021 | -0.06 [-0.20, 0.08] | 0.15 [-0.05, 0.35] | -0.13 [-0.31, 0.05] | 0.30 | 0.16 | 0.09 | -0.12 |
| main | 2022-2026 | 0.81 [0.65, 0.97] | 0.78 [0.67, 0.89] | 0.78 [0.66, 0.90] | 0.91 | 0.91 | 0.97 | 0.71 |

Training/validation/test windows: w1 train 2013-2015, validation 2016-2017, test 2018-2019; w2 train 2013-2017, validation 2018-2019, test 2020-2021; main train 2013-2019, validation 2020-2021, test 2022-2026.
**w1 and w2 were neither retrained nor re-scored after the patch.** They were trained before it. The price patch itself changes no row before 2025-04, but the PAEL rescale (factor 0.7031 instead of 1/1.5 before 2013-08-29) changes 165 PAEL rows from 2013-01-01 to 2013-08-28 by +5.5%, which lie inside the training period of both windows, so their training data differ slightly from the current data. The main row (2022-2026) is the retrained 0.1% agents.

*Significance across the three windows: 36 comparisons (algorithm vs baseline, Sharpe difference, circular block bootstrap), 3 with p < 0.05, smallest p = 0.020 (DDPG vs buy and hold).* All with p < 0.05 have the agent below the baseline.
