# PSX KSE-30 daily price data

## Layout
- `data/raw/<TICKER>.csv` - Yahoo Finance (`<TICKER>.KA`) daily rows, 2013-01-01 to 2026-10-09, unadjusted OHLC + `adj_close` + volume. Untouched.
- `data/clean/<TICKER>.csv` - same, with zero-volume rows removed (see below). Bad prints are NOT yet fixed.
- `scripts/` - `fetch_yahoo.py`, `clean_and_audit.py`, `list_jumps.py`.
- `data/psx_export_snippet.js` - browser-console export for dps.psx.com.pk (unused: PSX downloads were blocked).
- `reference_data/` - clone of blackirontimes-platform (git-ignored). It holds code only, no price data.

## Universe
29 tickers, the current KSE-30 list (taken from the PSX KSE-30 index page) minus ENGROH.
**ENGROH is dropped**: Yahoo has no data for `ENGROH.KA`, and `ENGRO.KA` (the pre-restructuring ticker) also returns nothing, so no stand-in exists.

## Validation against PSX
ATRL closes on 2025-01-02, 2025-01-20 and 2025-01-31 match the PSX figures (684.54, 658.18, 608.65) to the paisa. `adj_close` is lower than `close` (dividend adjustment) and should not be compared with PSX closes.

## Cleaning
Rows with volume = 0 are removed: 5,703 of 102,788. 5,287 fall on market-wide holidays (dates where at least 80% of tickers show zero volume; 185 such dates). 416 are illiquid days, mostly SAZEW.

## Fixes applied (pipeline: clean_and_audit.py, despike.py, apply_fixes.py, build_ew_proxy.py)
- `data/removed_rows.csv`: 17 rows dropped as bad prints (1 spike-and-reverse UBL; LUCK 3, UBL 4, SYS 9 scale-glitch rows), with a reason each.
- `adj_close_fixed` (in `data/clean`): `adj_close` divided by the split ratio for all rows before each break listed in `data/split_events.csv`. Yahoo's `adj_close` does not adjust these breaks. Six events; only PAEL is unverified even against Yahoo; none are verified against PSX (the PSX endpoint is blocked and its company page has no corporate-action table).
- Only breaks over 30% were treated as splits. Smaller bonus issues (e.g. 10-25%) are covered only to the extent Yahoo's `adj_close` handles them.

## Known data problems (partly superseded by the fixes above)
- Bad prints in 2025: single-day spikes that revert (e.g. UBL -53%/+98%, SYS -81%/+396%, LUCK -80%/+396%, MARI -89%). They have non-zero volume, so cleaning did not remove them.
- `adj_close` does not cover all corporate actions: e.g. HUBC 2022-10-11 and NBP 2017-04-06 / 2026-03-17 show close jumps of 17-19% that `adj_close` mostly does not.
- Series begin on the 2013-01-01 request date for 26 tickers, so first trading days are left-censored. EFERT starts 2014-01-20 and SYS 2015-02-16, probably Yahoo's coverage limit rather than listing date (not verified).

## Survivorship bias
The universe is today's KSE-30 membership applied to all history (2013-2026). KSE-30 is rebuilt twice a year, so over this period many stocks that were in the index at the time are missing, and every stock here is one that did well enough to be in the index now. This favours the winners:
- Backtest returns are biased upward, and drawdowns understated.
- Stocks later delisted, merged or demoted are absent. ENGROH (the Engro Corporation restructuring) is itself an example.
- Index weights and rebalance dates are not reproduced; historical membership was deliberately not reconstructed.
Treat any result as an upper bound, not an estimate of live performance.

## Benchmark
The benchmark is the **KSE-100 index** (`data/raw/KSE100.csv`, an Investing.com export supplied manually because Yahoo, Stooq, FRED and Investing.com's API all refused scripted access). `scripts/clean_kse100.py` validates it and writes `data/benchmark_kse100.csv` (kept outside `data/clean/`, which `load_panel` globs as tickers). Validation: 3,412 rows 2013-01-01..2026-10-12; no duplicates, gaps over 11 days or weekend dates; computed returns match the reported Change % (max diff 0.005 pt); 8 days with |return| over 6% (max 9.6%, COVID crash and 2025-26 events, kept); 7 rows have the close 0.01-0.11% outside the day's high-low (feed mismatch, kept, close used); volume is blank before 2013-11. Daily correlation with the old equal-weight proxy 0.96.
**It is a PRICE index: no dividends.** The strategies are total-return (`adj_close_fixed`), so the KSE-100 understates what an investor would have earned and the comparison favours the strategies by roughly the dividend yield. The index also covers 100 names (not survivorship-biased like our 29-stock universe). The old equal-weight proxy (`data/benchmark_ew_proxy.csv`, built by `build_ew_proxy.py`) is superseded and no longer used in any metric.

## Data caveats (read before trusting any result)
1. **Yahoo-only splits.** The six split/bonus breaks (MARI, BAFL, LUCK, SYS, UBL, PAEL; `data/split_events.csv`) were adjusted from price breaks over 30%. Five ratios agree with Yahoo's own split table; none was checked against PSX (endpoint blocked; PSX company pages carry no corporate-action table). Yahoo's split dates sit 2-14 days after the price breaks, so a few returns around each break may be off.
2. **PAEL unverified.** The 1.5x break on 2013-08-29 has no matching Yahoo split record; its ratio is inferred from price only. The PAEL 2014-04-22 10% bonus (factor 0.9091) was re-checked on 2026-10-15 and is NOT applied: Yahoo close, adj_close and adj_close_fixed fall only 1.82% on that day, so the series is already continuous there. All models in this repo were therefore trained without that correction, and none needs re-scoring for it. Models trained before the 0.7031 rescale of 2013 are listed in `docs/FACTSHEET.md` (Training-data provenance).
3. **Survivorship bias.** Today's KSE-30 constituents are applied to 2013-2026. Stocks that left the index (or were delisted/merged) are absent, so every return and the proxy benchmark are biased upward. Treat results as upper bounds.
4. **ENGROH dropped.** No Yahoo data for `ENGROH.KA` or the old `ENGRO.KA`; the universe is 29 tickers.
5. Also: zero-volume rows removed (market holidays and illiquid days, prices forward-filled); 17 bad-print rows dropped; breaks under 30% rely on Yahoo's `adj_close`; EFERT (2014-01-20) and SYS (2015-02-16) start late and are masked until then; the stocks' real first trading days before 2013 are not observed.

## Stage A: environment and baselines (no training)
- Code: `psx_rl/` (`data.py`, `env.py`, `metrics.py`, `baselines.py`), runner `scripts/run_stage_a.py`, results `results/stageA_metrics.csv`, train-fit mean-variance weights `results/mv_weights_trainfit.csv`.
- **Prices:** `adj_close_fixed` (dividends reinvested implicitly). Calendar = days where at least 20 of the 29 tickers have a row (3,378 days). Unlisted tickers are masked: no price, no trading, weight 0. Missing days are forward-filled; illiquid-day trading is not blocked (simplification).
- **Splits:** train 2013-01-01..2019-12-31, validation 2020-2021, test 2022-01-03..2026-10-09. Each split starts fresh with 1,000,000 cash.
- **Costs:** 0.1% of traded value per side (Stage C varies it). Trades at the close of day t; marked at t+1.
- **Baselines:** buy-and-hold (equal weight on day 1, never rebalanced); equal-weight rebalanced monthly; mean-variance monthly (max-Sharpe, long-only, 20% per-name cap, Ledoit-Wolf covariance, fit on train returns only and held fixed, so train-split results are in-sample); KSE-100 benchmark (price index buy-and-hold on the strategies' calendar; no costs, no dividends).
- **Metrics (one formula for all):** annual return = geometric; volatility = daily std x sqrt(ann); Sharpe = mean(r - rf)/std(r) x sqrt(ann); ann = observed trading days per year (about 245). Max drawdown on total asset. Exposure = mean stock value / total asset; cash share = 1 - exposure (cash earns 0); turnover = one-way traded value / mean asset, per year. Benchmark turnover is n/a.
- **Risk-free rate:** SBP policy rate, step function from `data/macro/sbp_policy_rate.csv`, parsed from SBP's official history "SBP's Reverse Repo, Repo and Policy (Target) Rates" (https://archive.sbp.org.pk/ecodata/OVR-Repo-History.pdf, saved at `data/macro/sbp_OVR-Repo-History.pdf`; `scripts/parse_sbp_policy_rate.py`). Per its footnote the ceiling rate served as the policy rate until 2015-05-24; the Policy (Target) Rate column applies from 2015-05-25. 45 changes, 2012-12-17 to 2026-04-28 (latest 11.50%, consistent with sbp.org.pk's September 2026 statement). Wikipedia's yearly table disagrees with SBP for 2017, 2021 and 2022, so it was not used.

## Stage B: PPO, A2C, DDPG (10 seeds each)
- Code: `psx_rl/gym_env.py`, `scripts/train_stage_b.py`, `scripts/run_stage_b_all.py`, `scripts/analyze_stage_b.py`. Results in `results/stageB/` (`stageB_runs.csv`, `stageB_summary.csv`, `stageB_significance.csv`, per-run test series in `test_series/`; model zips are git-ignored).
- **Setup:** stable-baselines3 2.9, MlpPolicy, CPU. 100,000 steps per run (about 58 passes over the 2013-2019 training data), seeds 0-9. Action = target share trades of action x hmax (hmax 100); cost 0.1%/side; reward = 100 x log return of total asset; observation = cash share, weights, 1-day and 20-day returns, listed mask. Hyperparameters were set once and not changed after seeing any test result (PPO n_steps 1024; A2C n_steps 32; DDPG noise 0.1, train_freq 4, gradient_steps 2).
- **Checkpoint selection:** validation Sharpe, checked every 10k steps. Test was evaluated once per run, for the selected checkpoint only.
- **total_asset** is accumulated from each step's `info` dict on a bare environment (no VecEnv auto-reset).
- **CI** = t-interval over the 10 seeds. **Significance** = Sharpe difference (mean over seeds of the algorithm minus the baseline) with a circular block bootstrap (blocks of 20 days, 4,000 draws, seeds resampled each draw); two-sided p from the bootstrap distribution.
- **Result:** no algorithm beats any baseline (all p > 0.17, all 95% CIs on the Sharpe difference include 0). Seed-0 test Sharpes (1.05-1.07), seen early, were an optimistic draw: the 10-seed means are lower.

## Figures and benchmark update
- `scripts/make_figures.py` writes `results/figures/test_equity.png` (test-split equity curves incl. KSE-100) and `test_sharpe.png` (test Sharpe with 95% CI over seeds).
- Stage A and Stage B tables were regenerated with the KSE-100 in place of the proxy. Test Sharpe: KSE-100 0.71 (price only), buy-and-hold 0.91, equal-weight monthly 0.91, mean-variance 0.96. Every Stage B algorithm still shows no significant Sharpe difference against any benchmark (KSE-100: PPO +0.10, A2C +0.15, DDPG -0.01; all p > 0.48). Bootstrap CIs for the other baselines moved in the third decimal because the shared test-day set changed slightly.

## Stage C: cost sensitivity
- Code: `scripts/run_stage_c_all.py` (driver), `scripts/analyze_stage_c.py`, `scripts/make_figures_c.py`, `scripts/make_tables.py`. Agents are trained, validated and tested at per-side cost 0, 0.25% and 0.5% (0.1% is Stage B); baselines are re-run at the same cost. 90 runs, protocol and hyperparameters as Stage B. Results in `results/stageC/`, tables in `results/tables/`, figure `results/figures/cost_sensitivity_sharpe.png`; summary in `docs/FACTSHEET.md`.
- Result: no algorithm differs significantly from any baseline at any cost (48 comparisons, min p = 0.052, DDPG vs buy-and-hold at 0.5%). DDPG's mean Sharpe is lowest at 0.5% cost (0.56).
- The Stage B bootstrap was made deterministic (it iterated a `set` of algorithm names, so draws depended on string-hash order); Stage B CIs moved in the third decimal, point estimates are unchanged.

## Walk-forward (2 extra windows)
- Code: `scripts/run_walkforward_all.py`, `scripts/analyze_walkforward.py`, `scripts/make_figures_wf.py`, `scripts/make_tables_wf.py`; windows in `psx_rl/data.py` (`WINDOWS`, selected by env `PSX_WINDOW`). w1: train 2013-2015, validation 2016-2017, test 2018-2019. w2: train 2013-2017, validation 2018-2019, test 2020-2021. 60 runs (3 algorithms x 10 seeds x 2 windows), 0.1% cost, Stage B protocol and hyperparameters. Results in `results/walkforward/`, tables 4-5 in `results/tables/`, figure `results/figures/walkforward_sharpe.png`.
- Result: in 2018-2019 all three algorithms have Sharpe about -0.75 to -0.82 against about -0.33 to -0.35 for the stock baselines; in 2020-2021 A2C and DDPG are slightly negative and PPO 0.15, against 0.08-0.30 for the baselines. Of 36 comparisons, 3 have p < 0.05 and all three are the algorithm below the baseline (no multiple-comparison correction); none has an algorithm significantly above a baseline.

## KSE-30 constituent history (survivorship check)
- `data/kse30_history.csv`: 28 semi-annual reviews (effective 2013-2026): date, added, removed, source link, source type, status. Status counts: 8 verified against PSX notices; 2 derived by differencing PSX constituent lists (2022H1, 2024H2); 3 news with the page read; 2 news summaries only; 13 slots unverified (all of 2012H2-2016H2, plus 2018H2, 2019H1, 2020H1, 2021H1); plus one undated Business Recorder item that cannot be placed in a slot. `data/kse30_constituent_lists.csv` holds the 8 full 30-name lists parsed from the PSX notice annexes (each has exactly 30 symbols); `scripts/build_kse30_history.py` builds the files.
- `data/kse30_membership_our29.csv`: which of our 29 stocks were index members in each window from 2022-01-03 on. Before 2022 membership cannot be established from verified sources (2021H1 is missing), so the 2013-2021 history is not reconstructed.
- Our 29 are essentially the September-2026 list (PTC, KEL and FATIMA joined on 2026-09-15). Over 2022-01-03..2026-10-09 the share of days each was a KSE-30 member: FATIMA, KEL, PTC 2%; BOP 22%; NBP and BAFL 33%; SAZEW 43%; FCCL and PAEL 54%; SNGP 64%; SEARL and NRL 69%; MLCF 89%; the other 16 100%.
- ENGRO / ENGROH (in the index throughout) is not in our 29, so its history is not covered by the price data.

## PSX data patch and 0.18% cost (applied)
- A fifth cost level, 0.18% per side (realistic PSX/CDC/SECP charges; sources in `data/fee_schedule.csv`), was run with the same 10 seeds per algorithm. Test Sharpe (mean [95% CI over seeds]): A2C 0.81 [0.67, 0.94], PPO 0.83 [0.68, 0.97], DDPG 0.80 [0.63, 0.98]; buy-and-hold 0.91, mean-variance 0.97, KSE-100 0.71. No comparison reaches p < 0.05 (60 comparisons, smallest p = 0.053).
- After the 0.18% runs finished, the staged patch from the PSX tables was applied (restored or added rows and date corrections for MARI, LUCK, BAFL, SYS, UBL; PAEL pre-2013-08-29 rescale 0.7031). The PAEL 2014 10% bonus was NOT applied (Yahoo's series is already continuous there). Trained models were re-scored on the patched data without retraining; the PAEL change touches training data, so its effect on trained RL agents is unmeasured. Effect: baselines change by at most 0.0075 Sharpe (mean-variance), RL means by at most 0.0004; no comparison changes significance. Details: `data/patch/PATCH_SUMMARY.md`, `results/patch_effect.csv`.
- Statement in "Known data problems" about HUBC/NBP jumps is a Yahoo adj_close limitation noted before the split-event checks (`data/split_events.csv`); it has not been re-verified against PSX tables.