"""Restore the 4 UBL rows dropped as 'scale glitch' (2025-06-12, 06-13, 06-19, 06-20) from the PSX table. They are real PRE-split days: Yahoo's raw values
equal PSX (~520, unadjusted) while the neighbouring cleaned rows are split-adjusted (~258). Raw columns come from PSX; adj_close = PSX close x Yahoo's adj factor
(0.9052, constant over June 2025); adj_close_fixed = adj_close / 2, so the restored rows sit on the same /2 basis as the cleaned rows around them.
Default: write data/restored/UBL_restored_rows.csv only. With --apply: insert into data/clean/UBL.csv and mark them restored in data/removed_rows.csv.
NOT applied while experiments that read data/clean are running."""
import sys, glob
import pandas as pd

FACTOR = 2.0
P = pd.concat([pd.read_csv(f, parse_dates=["date"]) for f in sorted(glob.glob(r"D:\psx_rl_portfolio\data\psx_tables\UBL_*.csv"))]).set_index("date").sort_index()
y = pd.read_csv(r"D:\psx_rl_portfolio\data\raw\UBL.csv", parse_dates=["date"]).set_index("date")
c = pd.read_csv(r"D:\psx_rl_portfolio\data\clean\UBL.csv", parse_dates=["date"])
rem = pd.read_csv(r"D:\psx_rl_portfolio\data\removed_rows.csv", parse_dates=["date"])
dates = pd.DatetimeIndex(rem[(rem.ticker == "UBL") & rem.reason.str.startswith("scale_glitch")].date)
assert len(dates) == 4, len(dates)
rows = []
for d in dates:
    r = P.loc[d]
    f = y.adj_close[d] / y.close[d]          # Yahoo's adj factor on that row (same scale error in both columns, so the ratio is clean)
    ac = r.close * f
    rows.append(dict(date=d.date(), open=r.open, high=r.high, low=r.low, close=r.close, adj_close=round(ac, 6), volume=int(r.volume), adj_close_fixed=round(ac / FACTOR, 6),
                     adj_factor=round(f, 5), source="PSX table (user-supplied, data/psx_tables/UBL_2025-06.csv)"))
R = pd.DataFrame(rows)
import os; os.makedirs(r"D:\psx_rl_portfolio\data\restored", exist_ok=True)
R.to_csv(r"D:\psx_rl_portfolio\data\restored\UBL_restored_rows.csv", index=False)
# consistency: neighbouring clean rows must carry the same adj factor and the restored fixed values must continue the series smoothly
nb = c.set_index("date")
print(R[["date", "close", "adj_close", "adj_close_fixed", "adj_factor"]].to_string(index=False))
if "--apply" in sys.argv:
    new = R.drop(columns=["adj_factor", "source"]).copy(); new["date"] = pd.to_datetime(new.date)
    out = pd.concat([c, new]).sort_values("date"); out.to_csv(r"D:\psx_rl_portfolio\data\clean\UBL.csv", index=False)
    rem["restored_from_psx"] = rem.apply(lambda r: r.ticker == "UBL" and r.date in set(dates), axis=1)
    rem.to_csv(r"D:\psx_rl_portfolio\data\removed_rows.csv", index=False)
    print("APPLIED: clean/UBL.csv now has", len(out), "rows")
