# Data patch (staged, NOT applied)

Built from the PSX tables in `data/psx_tables/` by `scripts/build_data_patch.py`; applied by `scripts/apply_data_patch.py --apply`.
Only `adj_close_fixed` and row presence feed the pipeline. Expected `adj_close_fixed` = PSX close x Yahoo adj factor, divided by the split factor before the ex-date.

- PSX dates compared: 133 (5 tickers); unchanged: 111; rows to ADD: 20; rows to REPLACE: 2; extras (clean rows PSX does not list): 0

## MARI (factor 9, ex-date 2024-09-16)
- no change: every PSX day in the table already matches the cleaned data

## LUCK (factor 5, ex-date 2025-04-28)
- ADD 2025-04-28: PSX close 358.88 -> adj_close_fixed 351.5224 (missing day: Yahoo has a zero-volume stale row (or none) on a day PSX traded)

## BAFL (factor 2, ex-date 2026-04-20)
- ADD 2026-04-28: PSX close 60.71 -> adj_close_fixed 57.7045 (missing day: Yahoo has a zero-volume stale row (or none) on a day PSX traded)
- ADD 2026-04-29: PSX close 59.5 -> adj_close_fixed 56.5544 (missing day: Yahoo has a zero-volume stale row (or none) on a day PSX traded)

## SYS (factor 5, ex-date 2025-06-02)
- ADD 2025-04-09: PSX close 486.73 -> adj_close_fixed 95.8330 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-04-10: PSX close 502.73 -> adj_close_fixed 98.9832 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-04-11: PSX close 508.07 -> adj_close_fixed 100.0346 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-05-19: PSX close 539.9 -> adj_close_fixed 106.5584 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-05-20: PSX close 531.05 -> adj_close_fixed 104.8117 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-05-21: PSX close 531.01 -> adj_close_fixed 104.8038 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-05-22: PSX close 559.65 -> adj_close_fixed 110.4564 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-05-23: PSX close 554.19 -> adj_close_fixed 109.3787 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-05-26: PSX close 537.56 -> adj_close_fixed 106.0965 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-06-02: PSX close 103.4 -> adj_close_fixed 102.0387 (missing day: Yahoo has a zero-volume stale row (or none) on a day PSX traded)
- ADD 2025-06-16: PSX close 102.28 -> adj_close_fixed 100.9334 (missing day: Yahoo has a zero-volume stale row (or none) on a day PSX traded)
- REPLACE 2025-06-17: adj_close_fixed 100.9334 -> 102.7492 (+1.80%); Yahoo row holds another day's data (date shifted)

## UBL (factor 2, ex-date 2025-06-23)
- ADD 2025-06-12: PSX close 520.2 -> adj_close_fixed 235.4466 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-06-13: PSX close 517.63 -> adj_close_fixed 234.2834 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-06-16: PSX close 516.46 -> adj_close_fixed 233.7539 (missing day: Yahoo has a zero-volume stale row (or none) on a day PSX traded)
- ADD 2025-06-19: PSX close 521.4 -> adj_close_fixed 235.9897 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-06-20: PSX close 524.19 -> adj_close_fixed 237.2525 (restored: dropped as scale glitch, PSX confirms a real day)
- ADD 2025-06-23: PSX close 261.81 -> adj_close_fixed 236.9945 (missing day: Yahoo has a zero-volume stale row (or none) on a day PSX traded)
- REPLACE 2025-06-17: adj_close_fixed 233.7539 -> 235.8675 (+0.90%); Yahoo row holds another day's data (date shifted)

## PAEL (series-level rescale, see rescale.csv)
- rows 2013-01-01..2013-08-28: adj_close_fixed x 1.05465 (= 0.7031 x 1.5), i.e. factor 0.7031 instead of 1/1.5; PAEL's 2013-08-29 return changes from +0.02% to -5.16% (market median -0.98%; the stock opened at 0.7032 of the previous close and fell 5.2% intraday).
- 2014-04-22 10% bonus (last cum-bonus close 2014-04-21 = 25.68 KSE raw, KSE open 23.35): NOT applied. Yahoo's PAEL series is already continuous there (open/prev close 1.0066, return -1.8%); the KSE-raw / Yahoo ratio drops from 1.4528 to 1.3123 across the two days, a factor 1.107 = the bonus, so Yahoo's earlier rows already contain it. Multiplying 2013-08-29..2014-04-21 by 0.9091 would create a false +8.0% jump on 2014-04-22.
