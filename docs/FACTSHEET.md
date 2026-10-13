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

## Walk-forward (0.1% cost, 10 seeds per algorithm per window)
Windows (`psx_rl/data.py`): w1 train 2013-2015, validation 2016-2017, test 2018-2019; w2 train 2013-2017, validation 2018-2019, test 2020-2021; main split as above. Same protocol, hyperparameters and bootstrap as Stage B. Test Sharpe (RL: mean [95% CI over seeds]):

| Test period | A2C | PPO | DDPG | Buy-and-hold | EW monthly | Mean-variance | KSE-100 |
|---|---|---|---|---|---|---|---|
| 2018-2019 | -0.80 [-0.96, -0.64] | -0.82 [-0.97, -0.66] | -0.75 [-0.89, -0.61] | -0.34 | -0.33 | -0.35 | -0.45 |
| 2020-2021 | -0.06 [-0.20, 0.08] | 0.15 [-0.05, 0.35] | -0.13 [-0.31, 0.05] | 0.30 | 0.16 | 0.08 | -0.12 |
| 2022-2026 | 0.85 [0.73, 0.98] | 0.80 [0.65, 0.95] | 0.70 [0.50, 0.89] | 0.91 | 0.91 | 0.96 | 0.71 |

- Mean annual return of the RL algorithms: 2018-2019 A2C -11.1%, PPO -13.5%, DDPG -13.1%; 2020-2021 A2C 3.5%, PPO 9.9%, DDPG 1.3%.
- Significance: 36 comparisons (3 algorithms x 4 baselines x 3 test periods), no multiple-comparison correction. 3 have p < 0.05, all with the algorithm below the baseline: A2C vs equal-weight monthly 2018-19 (diff -0.47, p = 0.035), A2C vs buy-and-hold 2020-21 (-0.36, p = 0.044), DDPG vs buy-and-hold 2020-21 (-0.43, p = 0.020). No comparison has the algorithm significantly above a baseline. Full table: `results/tables/table5_walkforward_significance.csv`.
- Figure: `results/figures/walkforward_sharpe.png`.

## Known limitations (all in README)
Walk-forward covers only two extra windows (2018-19, 2020-21) plus the main split; survivorship bias; Yahoo-only split adjustments; KSE-100 excludes dividends; the test period is one strongly rising market (baseline CAGR about 40%); 10 seeds, 100k steps, one hyperparameter setting.

## Files
- Figures: `results/figures/` (`test_equity.png`, `test_sharpe.png`, `cost_sensitivity_sharpe.png`, `walkforward_sharpe.png`).
- Tables: `results/tables/` (CSV + `tables.md`).
- Raw per-run results: `results/stageB/` (0.1%), `results/stageC/<c0|c0025|c005>/`, `results/walkforward/<w1|w2>/`.
- Regenerate: `scripts/run_stage_a.py`, `scripts/analyze_stage_c.py`, `scripts/make_figures.py`, `scripts/make_figures_c.py`, `scripts/make_tables.py`, `scripts/analyze_walkforward.py`, `scripts/make_figures_wf.py`, `scripts/make_tables_wf.py`.
