"""Compare Yahoo raw rows with PSX tables (data/psx_tables/<TICKER>_<YYYY-MM>.csv, pasted from dps.psx.com.pk) around a split.
Per date: ratio = PSX close / Yahoo close. ~1 -> Yahoo equals PSX; ~factor -> Yahoo is already divided by the factor; anything else -> MISMATCH.
Also checks that a cash dividend with a known ex-date is in adj_close: (adj/close before ex) / (adj/close on ex) should equal 1 - D/P_cum.
Writes data/split_verification.csv (read-only on prices)."""
import sys, glob, os
import numpy as np, pandas as pd

CHECKS = {"MARI": dict(factor=9.0, ex_date="2024-09-16", div=134.0)}   # div = Rs per pre-bonus share, ex on ex_date
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
        out.append(dict(ticker=t, date=d.date(), psx_close=r.close, yahoo_close=round(y.close[d], 4), ratio=round(q, 4), verdict=v,
                        psx_volume=r.volume, yahoo_volume=y.volume[d], volume_ratio=round(vq, 4) if np.isfinite(vq) else np.nan,
                        psx_high=r.high, yahoo_high=round(y.high[d], 4), psx_low=r.low, yahoo_low=round(y.low[d], 4)))
    ex = pd.Timestamp(cfg["ex_date"]); before = y.index[y.index < ex][-1]
    pcum = P.close[P.index[P.index < ex][-1]]
    obs = (y.adj_close[before] / y.close[before]) / (y.adj_close[ex] / y.close[ex])
    exp = 1 - cfg["div"] / pcum
    print(f"{t}: dividend check across {before.date()}->{ex.date()}: close ratio {y.close[ex]/y.close[before]:.4f}, adj_close ratio {y.adj_close[ex]/y.adj_close[before]:.4f}, "
          f"implied dividend factor {obs:.5f} vs expected 1 - {cfg['div']}/{pcum} = {exp:.5f}")
D = pd.DataFrame(out); D.to_csv(r"D:\psx_rl_portfolio\data\split_verification.csv", index=False)
print(D.verdict.value_counts().to_string())
print(D[["ticker", "date", "psx_close", "yahoo_close", "ratio", "verdict", "volume_ratio"]].to_string(index=False))

# ---- record the verified facts in data/split_events.csv (extra columns; apply_fixes.py preserves them) ----
NOTES = {"MARI": dict(ex_date="2024-09-16", psx_close_check="19 PSX closes 2024-09-02..09-30 vs Yahoo: 12 equal, 7 (09-05..09-13) Yahoo = PSX/9; 0 mismatches",
                      psx_notice_url="", verification_note="Yahoo break date (2024-09-05) is earlier than the ex-date (2024-09-16): Yahoo divided the closes (and multiplied volumes) of 09-05..09-13 by 9 but not 09-04 and earlier, so dividing rows before 09-05 by 9 makes the series continuous (adj_close_fixed 09-04->09-05 = PSX 3641.42->3590.72, -1.39%). Rs 134 dividend ex 2024-09-16 is in adj_close on the ex-date (implied factor 0.96211 = 1-134/3536.83). PSX notice link not yet provided.")}
S = pd.read_csv(r"D:\psx_rl_portfolio\data\split_events.csv")
for c in ("ex_date", "psx_close_check", "psx_notice_url", "verification_note"):
    if c not in S.columns: S[c] = ""
    S[c] = S[c].astype(object)
for t, kv in NOTES.items():
    for c, v in kv.items(): S.loc[S.ticker == t, c] = v
S.loc[S.ticker == "MARI", "status"] = "psx_closes_verified (notice link pending)"
S.to_csv(r"D:\psx_rl_portfolio\data\split_events.csv", index=False)
