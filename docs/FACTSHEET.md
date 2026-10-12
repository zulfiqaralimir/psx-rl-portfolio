# Factsheet: PSX RL portfolio study (facts only, no interpretation)

Generated from files in this repo. Numbers are test split 2022-01-03..2026-10-09 (1,166 trading days) unless stated.

## Data
- Universe: 29 KSE-30 tickers (ENGROH dropped, no Yahoo data). Source: Yahoo Finance `.KA`, 2013-01-01..2026-10-09. Survivorship-biased (today's constituents applied to all history).
- Cleaning: 5,703 zero-volume rows removed; 17 bad-print rows dropped (`data/removed_rows.csv`); 6 splits adjusted from price breaks over 30% (`data/split_events.csv`), five agree with Yahoo's split table, PAEL unverified, none checked against PSX.
- Prices used: `adj_close_fixed` (total return). Calendar: 3,378 days with at least 20 tickers.
- Benchmark: KSE-100 index, Investing.com export (`data/raw/KSE100.csv`), 3,412 rows. Price index, no dividends. Validation in README ("Benchmark").
- Risk-free: SBP policy rate step function (45 changes, latest 11.50%).

## Setup
- Splits: train 2013-2019, validation 2020-2021, test 2022-2026. Each starts with 1,000,000 cash.
- Costs: 0.1% per side (Stage C: 0, 0.25%, 0.5%, agents trained and tested at the same cost). Trades at close of day t, marked at t+1.
- Baselines: buy-and-hold, equal-weight monthly, mean-variance monthly (max-Sharpe, long-only, 20% cap, Ledoit-Wolf, fit on train only), KSE-100.
- Agents: stable-baselines3 2.9 PPO, A2C, DDPG; MlpPolicy; 100,000 steps; 10 seeds (0-9) per algorithm per cost; hyperparameters fixed before any test result; checkpoint chosen on validation Sharpe every 10k steps; test evaluated once per run.
- Metrics: one formula for all (geometric annual return, volatility, Sharpe over SBP rate, max drawdown, turnover = one-way traded value / mean asset / year).
- Significance: Sharpe difference (algo seed-mean minus baseline), circular block bootstrap (block 20 days, 4,000 draws, seeds resampled), two-sided p.

## Results at 0.1% cost (test)
| Strategy | Annual return | Volatility | Sharpe | Max drawdown | Turnover/yr |
|---|---|---|---|---|---|
| Buy-and-hold | 40.5% | 23.6% | 0.91 | -25.5% | 0.04 |
| Equal-weight monthly | 40.9% | 24.1% | 0.91 | -25.1% | 0.44 |
| Mean-variance monthly | 43.8% | 25.0% | 0.96 | -32.4% | 0.45 |
| KSE-100 (price index) | 31.8% | 20.2% | 0.71 | -22.6% | n/a |
| A2C (10-seed mean) | 41.1% | 26.1% | 0.85 | -27.0% | 0.12 |
| PPO (10-seed mean) | 37.1% | 23.8% | 0.80 | -26.1% | 0.77 |
| DDPG (10-seed mean) | 35.0% | 25.6% | 0.70 | -28.8% | 7.09 |

## Cost sensitivity (test Sharpe, RL = mean [95% CI over 10 seeds])
| Cost/side | A2C | PPO | DDPG | Buy-and-hold | Mean-variance | KSE-100 |
|---|---|---|---|---|---|---|
| 0% | 0.83 [0.68, 0.98] | 0.82 [0.67, 0.96] | 0.73 [0.48, 0.99] | 0.91 | 0.97 | 0.71 |
| 0.1% | 0.85 [0.73, 0.98] | 0.80 [0.65, 0.95] | 0.70 [0.50, 0.89] | 0.91 | 0.96 | 0.71 |
| 0.25% | 0.77 [0.61, 0.94] | 0.81 [0.69, 0.93] | 0.71 [0.58, 0.83] | 0.91 | 0.96 | 0.71 |
| 0.5% | 0.78 [0.60, 0.96] | 0.80 [0.65, 0.95] | 0.56 [0.21, 0.91] | 0.91 | 0.95 | 0.71 |

- Significance: 48 algorithm-vs-baseline comparisons (3 algorithms x 4 baselines x 4 cost levels). None has p < 0.05; smallest p = 0.052 (DDPG vs buy-and-hold at 0.5%), next 0.090 (DDPG vs equal-weight monthly at 0.5%). Full table: `results/tables/table3_significance_by_cost.csv`.
- DDPG turnover: about 7.7/yr at 0% cost, 7.1 at 0.1%, 4.7 at 0.25%, 4.9 at 0.5%. A2C 0.08-0.19/yr, PPO 0.58-0.79/yr.

## Known limitations (all in README)
Single test window (walk-forward in `results/walkforward/` if present); survivorship bias; Yahoo-only split adjustments; KSE-100 excludes dividends; the test period is one strongly rising market (baseline CAGR about 40%); 10 seeds, 100k steps, one hyperparameter setting.

## Files
- Figures: `results/figures/` (`test_equity.png`, `test_sharpe.png`, `cost_sensitivity_sharpe.png`).
- Tables: `results/tables/` (CSV + `tables.md`).
- Raw per-run results: `results/stageB/` (0.1%), `results/stageC/<c0|c0025|c005>/`.
- Regenerate: `scripts/run_stage_a.py`, `scripts/analyze_stage_c.py`, `scripts/make_figures.py`, `scripts/make_figures_c.py`, `scripts/make_tables.py`.
