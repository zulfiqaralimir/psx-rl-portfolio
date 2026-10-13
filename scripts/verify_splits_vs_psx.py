"""Compare Yahoo raw rows with PSX tables (data/psx_tables/<TICKER>_<YYYY-MM>.csv, pasted from dps.psx.com.pk) around a split.
Per date: ratio = PSX close / Yahoo close. ~1 -> Yahoo equals PSX; ~factor -> Yahoo is already divided by the factor; anything else -> MISMATCH.
Also checks that a cash dividend with a known ex-date is in adj_close: (adj/close before ex) / (adj/close on ex) should equal 1 - D/P_cum.
Writes data/split_verification.csv (read-only on prices)."""
import sys, glob, os
import numpy as np, pandas as pd

CHECKS = {"MARI": dict(factor=9.0, ex_date="2024-09-16", div=134.0),   # div = Rs per pre-bonus share, ex on ex_date
          "LUCK": dict(factor=5.0, ex_date="2025-04-28", div=None),
          "BAFL": dict(factor=2.0, ex_date="2026-04-20", div=None),
          "SYS": dict(factor=5.0, ex_date="2025-06-02", div=None)}   # no dividend supplied: only check that adj_close has no jump at ex
out = []
for t, cfg in CHECKS.items():
    y = pd.read_csv(rf"D:\psx_rl_portfolio\data\raw\{t}.csv", parse_dates=["date"]).set_index("date")
    P = pd.concat([pd.read_csv(f, parse_dates=["date"]) for f in sorted(glob.glob(rf"D:\psx_rl_portfolio\data\psx_tables\{t}_*.csv"))]).set_index("date").sort_index()
    f = cfg["factor"]
    for d, r in P.iterrows():
        if d not in y.index:
            out.append(dict(ticker=t, date=d.date(), psx_close=r.close, yahoo_close=np.nan, ratio=np.nan, verdict="no Yahoo row")); continue
        q = r.close / y.close[d]
        v = "equal" if abs(q - 1) < 0.002 else ("Yahoo = PSX/factor" if abs(q / f - 1) < 0.002 else "MISMATCH")
        vq = r.volume / y.volume[d] if y.volume[d] else np.nan
        stale = bool(y.volume[d] == 0 and r.volume > 0)   # Yahoo carries a flat zero-volume row on a day PSX traded
        out.append(dict(ticker=t, date=d.date(), psx_close=r.close, yahoo_close=round(y.close[d], 4), ratio=round(q, 4), verdict=v, yahoo_stale_row=stale,
                        psx_volume=r.volume, yahoo_volume=y.volume[d], volume_ratio=round(vq, 4) if np.isfinite(vq) else np.nan,
                        psx_high=r.high, yahoo_high=round(y.high[d], 4), psx_low=r.low, yahoo_low=round(y.low[d], 4)))
    ex = pd.Timestamp(cfg["ex_date"])
    traded = y.index[(y.volume > 0)]
    before = traded[traded < ex][-1]; after = traded[traded >= ex][0]   # last traded row before ex, first traded row on/after ex
    pcum = P.close[P.index[P.index < ex][-1]]
    obs = (y.adj_close[before] / y.close[before]) / (y.adj_close[after] / y.close[after])
    msg = f"{t}: adj/close factor {before.date()} -> {after.date()}: implied dividend factor {obs:.5f} (close ratio {y.close[after]/y.close[before]:.4f}, adj_close ratio {y.adj_close[after]/y.adj_close[before]:.4f})"
    if cfg["div"]: msg += f" vs expected 1 - {cfg['div']}/{pcum} = {1 - cfg['div'] / pcum:.5f}"
    print(msg)
D = pd.DataFrame(out); D.to_csv(r"D:\psx_rl_portfolio\data\split_verification.csv", index=False)
print(D.groupby("ticker").verdict.value_counts().to_string()); print("Yahoo stale zero-volume rows on PSX trading days:", D[D.yahoo_stale_row][["ticker", "date"]].astype(str).agg(" ".join, axis=1).tolist())
print(D[D.ticker == "BAFL"][["ticker", "date", "psx_close", "yahoo_close", "ratio", "verdict", "volume_ratio", "yahoo_stale_row"]].to_string(index=False))

# ---- record the verified facts in data/split_events.csv (extra columns; apply_fixes.py preserves them) ----
NOTES = {"MARI": dict(ex_date="2024-09-16", psx_close_check="19 PSX closes 2024-09-02..09-30 vs Yahoo: 12 equal, 7 (09-05..09-13) Yahoo = PSX/9; 0 mismatches",
                      psx_notice_url="", verification_note="Yahoo break date (2024-09-05) is earlier than the ex-date (2024-09-16): Yahoo divided the closes (and multiplied volumes) of 09-05..09-13 by 9 but not 09-04 and earlier, so dividing rows before 09-05 by 9 makes the series continuous (adj_close_fixed 09-04->09-05 = PSX 3641.42->3590.72, -1.39%). Rs 134 dividend ex 2024-09-16 is in adj_close on the ex-date (implied factor 0.96211 = 1-134/3536.83). PSX notice link not yet provided.")}
NOTES["LUCK"] = dict(ex_date="2025-04-28", psx_close_check="15 PSX closes 2025-04-03..04-30 vs Yahoo: 5 equal pre-04-10, 7 (04-10..04-18) Yahoo = PSX/5, 2 equal after; 1 MISMATCH: 2025-04-28 (PSX close 358.88, volume 9,953,480; Yahoo has a stale zero-volume row at 350.29)",
                     psx_notice_url="", verification_note="Factor 5 and ex-date 2025-04-28 (last pre-split close 2025-04-18 = 1,751.45; no trading 04-21..04-25 per user). Yahoo break date (2025-04-10) is earlier than the ex-date: Yahoo divided 04-10..04-18 by 5 but not 04-09 and earlier, so dividing rows before 04-10 by 5 makes the series continuous. adj_close/close factor is constant across 04-18 -> 04-29 (no dividend adjustment at ex). The real 2025-04-28 trading day is missing from our cleaned data (Yahoo's zero-volume stale row was dropped), so the 04-18 -> 04-29 return merges two days (PSX: +2.45% then -2.70%). PSX table source: user-supplied from dps.psx.com.pk, data/psx_tables/LUCK_2025-04.csv; notice link not yet provided.")
NOTES["BAFL"] = dict(ex_date="2026-04-20", psx_close_check="22 PSX closes 2026-04-01..04-30 vs Yahoo: 6 equal (04-01..04-08), 7 (04-09..04-17) Yahoo = PSX/2, 8 equal after 04-20 (04-28 only by coincidence: Yahoo stale zero-volume row), 1 MISMATCH: 2026-04-29 (PSX 59.50, Yahoo stale 60.71)",
                     psx_notice_url="", verification_note="Factor 2, last pre-split close 2026-04-17 = 125.34, ex-date 2026-04-20 (user-supplied). Yahoo break date (2026-04-09) is earlier than the ex-date: Yahoo divided 04-09..04-17 by 2 but not 04-08 and earlier, so dividing rows before 04-09 by 2 makes the series continuous. adj_close/close factor is constant across 04-17 -> 04-20 (no dividend adjusted at ex). Yahoo's 04-28/04-29 rows are stale zero-volume copies of the 04-27 close; PSX traded both days (04-28 close 60.71, 4.85M shares; 04-29 close 59.50, 4.44M), and our cleaned data lacks them, so 04-27 -> 04-30 merges three days. PSX table source: user-supplied from dps.psx.com.pk, data/psx_tables/BAFL_2026-04.csv; notice link not yet provided.")
NOTES["SYS"] = dict(ex_date="2025-06-02", psx_close_check="57 PSX closes 2025-04-03..06-30 vs Yahoo: 45 equal, 4 (2025-04-09..04-11, 05-27) Yahoo = PSX/5, 8 MISMATCH: 05-19..05-26 (6 days, Yahoo = PSX/2, the dropped rows), 06-02 (Yahoo stale), 06-17 (holds PSX 06-16 data); 06-16 is a Yahoo stale zero-volume row that equals PSX within tolerance",
                    psx_notice_url="", verification_note="Factor 5, last pre-split close 2025-05-27 = 544.10, ex-date 2025-06-02 (user-supplied). Yahoo's close for 05-27 is already 544.10/5 = 108.82 (volume x5 = PSX), so Yahoo's break date 2025-05-27 is the first /5 row; adj_close_fixed divides rows BEFORE it by 5 (through 05-26) and leaves 05-27 as is: adj_close_fixed*5/PSX close = the constant adj factor 0.9868 on every row 04-18..05-27 and 4.934 (=5*0.9868) from 06-03 on, so no off-by-one. The 9 dropped rows are real PSX days: 04-09..04-11 Yahoo = PSX/5 (already the correct split-adjusted value), 05-19..05-26 Yahoo = PSX/2 (wrong). Restoration from PSX is staged, not applied (scripts/restore_sys_rows.py). Also missing from cleaned data: 2025-06-02 (PSX traded, close 103.40, 5.76M; Yahoo stale zero-volume row) and 06-17 (Yahoo 06-17 row carries PSX 06-16 data, PSX 06-17 close 104.12 absent). PSX table source: user-supplied from dps.psx.com.pk, data/psx_tables/SYS_2025-0[4-6].csv; notice link not yet provided.")
S = pd.read_csv(r"D:\psx_rl_portfolio\data\split_events.csv")
for c in ("ex_date", "psx_close_check", "psx_notice_url", "verification_note"):
    if c not in S.columns: S[c] = ""
    S[c] = S[c].astype(object)
for t, kv in NOTES.items():
    for c, v in kv.items(): S.loc[S.ticker == t, c] = v
for t in NOTES: S.loc[S.ticker == t, "status"] = "psx_closes_verified (notice link pending)"
S.to_csv(r"D:\psx_rl_portfolio\data\split_events.csv", index=False)
