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
Yahoo has no KSE-100 (`^KSE`, `KSE100.KA` and `^KSE100` all return nothing). `data/benchmark_ew_proxy.csv` is an **equal-weight PROXY of the 29 tickers, not the KSE-100**: daily-rebalanced, total-return (`adj_close_fixed`), no return-exclusion rule. It inherits the survivorship bias, so its CAGR (about 25.6%) is inflated.

## Data caveats (read before trusting any result)
1. **Yahoo-only splits.** The six split/bonus breaks (MARI, BAFL, LUCK, SYS, UBL, PAEL; `data/split_events.csv`) were adjusted from price breaks over 30%. Five ratios agree with Yahoo's own split table; none was checked against PSX (endpoint blocked; PSX company pages carry no corporate-action table). Yahoo's split dates sit 2-14 days after the price breaks, so a few returns around each break may be off.
2. **PAEL unverified.** The 1.5x break on 2013-08-29 has no matching Yahoo split record; its ratio is inferred from price only.
3. **Survivorship bias.** Today's KSE-30 constituents are applied to 2013-2026. Stocks that left the index (or were delisted/merged) are absent, so every return and the proxy benchmark are biased upward. Treat results as upper bounds.
4. **ENGROH dropped.** No Yahoo data for `ENGROH.KA` or the old `ENGRO.KA`; the universe is 29 tickers.
5. Also: zero-volume rows removed (market holidays and illiquid days, prices forward-filled); 17 bad-print rows dropped; breaks under 30% rely on Yahoo's `adj_close`; EFERT (2014-01-20) and SYS (2015-02-16) start late and are masked until then; the stocks' real first trading days before 2013 are not observed.

## Stage A: environment and baselines (no training)
- Code: `psx_rl/` (`data.py`, `env.py`, `metrics.py`, `baselines.py`), runner `scripts/run_stage_a.py`, results `results/stageA_metrics.csv`, train-fit mean-variance weights `results/mv_weights_trainfit.csv`.
- **Prices:** `adj_close_fixed` (dividends reinvested implicitly). Calendar = days where at least 20 of the 29 tickers have a row (3,378 days). Unlisted tickers are masked: no price, no trading, weight 0. Missing days are forward-filled; illiquid-day trading is not blocked (simplification).
- **Splits:** train 2013-01-01..2019-12-31, validation 2020-2021, test 2022-01-03..2026-10-09. Each split starts fresh with 1,000,000 cash.
- **Costs:** 0.1% of traded value per side (Stage C varies it). Trades at the close of day t; marked at t+1.
- **Baselines:** buy-and-hold (equal weight on day 1, never rebalanced); equal-weight rebalanced monthly; mean-variance monthly (max-Sharpe, long-only, 20% per-name cap, Ledoit-Wolf covariance, fit on train returns only and held fixed, so train-split results are in-sample); equal-weight proxy benchmark (daily rebalanced, frictionless, days with 20+ tickers only; not the KSE-100).
- **Metrics (one formula for all):** annual return = geometric; volatility = daily std x sqrt(ann); Sharpe = mean(r - rf)/std(r) x sqrt(ann); ann = observed trading days per year (about 245). Max drawdown on total asset. Exposure = mean stock value / total asset; cash share = 1 - exposure (cash earns 0); turnover = one-way traded value / mean asset, per year. Benchmark turnover is n/a.
- **Risk-free rate:** SBP policy rate, step function from `data/macro/sbp_policy_rate.csv`, parsed from SBP's official history "SBP's Reverse Repo, Repo and Policy (Target) Rates" (https://archive.sbp.org.pk/ecodata/OVR-Repo-History.pdf, saved at `data/macro/sbp_OVR-Repo-History.pdf`; `scripts/parse_sbp_policy_rate.py`). Per its footnote the ceiling rate served as the policy rate until 2015-05-24; the Policy (Target) Rate column applies from 2015-05-25. 45 changes, 2012-12-17 to 2026-04-28 (latest 11.50%, consistent with sbp.org.pk's September 2026 statement). Wikipedia's yearly table disagrees with SBP for 2017, 2021 and 2022, so it was not used.
