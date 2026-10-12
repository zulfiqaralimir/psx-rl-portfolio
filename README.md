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

## Known data problems (open)
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
Not built yet. Planned: KSE-100 from another source, or an equal-weight basket of these 29 labelled as a proxy.
