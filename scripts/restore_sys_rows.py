"""Restore the 9 SYS rows that were dropped as 'scale glitch' (2025-04-09..04-11, 2025-05-19..05-26) from the PSX tables.
Raw columns (open/high/low/close/volume) come from PSX (unadjusted, like the other pre-split clean rows). adj_close = PSX close x Yahoo's adj factor
(adj_close/close of the neighbouring rows; equal on both sides of each gap: 0.98446 for April, 0.98683 for May); adj_close_fixed = adj_close / 5.
Default: write the rows to data/restored/SYS_restored_rows.csv only. With --apply: insert them into data/clean/SYS.csv and mark them restored in
data/removed_rows.csv. NOT applied while experiments that read data/clean are running (it would change their input mid-run)."""
import sys, glob
import pandas as pd

FACTOR = 5.0
P = pd.concat([pd.read_csv(f, parse_dates=["date"]) for f in sorted(glob.glob(r"D:\psx_rl_portfolio\data\psx_tables\SYS_*.csv"))]).set_index("date").sort_index()
y = pd.read_csv(r"D:\psx_rl_portfolio\data\raw\SYS.csv", parse_dates=["date"]).set_index("date")
c = pd.read_csv(r"D:\psx_rl_portfolio\data\clean\SYS.csv", parse_dates=["date"])
rem = pd.read_csv(r"D:\psx_rl_portfolio\data\removed_rows.csv", parse_dates=["date"])
dates = pd.DatetimeIndex(rem[(rem.ticker == "SYS") & rem.reason.str.startswith("scale_glitch")].date)
assert len(dates) == 9, len(dates)
rows = []
for d in dates:
    r = P.loc[d]
    f = y.adj_close[d] / y.close[d]          # Yahoo's adj factor on that row (same scale error in both columns, so the ratio is clean)
    ac = r.close * f
    rows.append(dict(date=d.date(), open=r.open, high=r.high, low=r.low, close=r.close, adj_close=round(ac, 6), volume=int(r.volume), adj_close_fixed=round(ac / FACTOR, 6),
                     adj_factor=round(f, 5), source="PSX table (user-supplied, data/psx_tables/SYS_2025-0[45].csv)"))
R = pd.DataFrame(rows)
import os; os.makedirs(r"D:\psx_rl_portfolio\data\restored", exist_ok=True)
R.to_csv(r"D:\psx_rl_portfolio\data\restored\SYS_restored_rows.csv", index=False)
# consistency: neighbouring clean rows must carry the same adj factor and the restored fixed values must continue the series smoothly
nb = c.set_index("date")
print(R[["date", "close", "adj_close", "adj_close_fixed", "adj_factor"]].to_string(index=False))
if "--apply" in sys.argv:
    new = R.drop(columns=["adj_factor", "source"]).copy(); new["date"] = pd.to_datetime(new.date)
    out = pd.concat([c, new]).sort_values("date"); out.to_csv(r"D:\psx_rl_portfolio\data\clean\SYS.csv", index=False)
    rem["restored_from_psx"] = rem.apply(lambda r: r.ticker == "SYS" and r.date in set(dates), axis=1)
    rem.to_csv(r"D:\psx_rl_portfolio\data\removed_rows.csv", index=False)
    print("APPLIED: clean/SYS.csv now has", len(out), "rows")
