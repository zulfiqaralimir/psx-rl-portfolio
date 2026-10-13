"""Apply the staged data patch (data/patch/additions.csv, replacements.csv) to data/clean/<TICKER>.csv.
Default = dry run: checks the patched panel in memory (trading calendar, row counts, return sanity) and prints it; changes nothing.
--apply: writes data/clean, marks the restored rows in data/removed_rows.csv (column restored_from_psx) and saves a log to data/patch/applied.txt.
Do NOT apply while any experiment that reads data/clean is running."""
import sys, os, shutil, tempfile
import numpy as np, pandas as pd

ROOT = r"D:\psx_rl_portfolio"
A = pd.read_csv(ROOT + r"\data\patch\additions.csv", parse_dates=["date"])
R = pd.read_csv(ROOT + r"\data\patch\replacements.csv", parse_dates=["date"])
COLS = ["date", "open", "high", "low", "close", "adj_close", "volume", "adj_close_fixed"]
RS_PATH = ROOT + r"\data\patch\rescale.csv"
RS = pd.read_csv(RS_PATH, parse_dates=["date_from", "date_to"]) if os.path.exists(RS_PATH) else pd.DataFrame(columns=["ticker"])


def patched(t):
    c = pd.read_csv(rf"{ROOT}\data\clean\{t}.csv", parse_dates=["date"])
    r = R[R.ticker == t]
    c = c[~c.date.isin(r.date)]
    c = pd.concat([c, r[COLS], A[A.ticker == t][COLS]]).sort_values("date").reset_index(drop=True)
    for _, q in RS[RS.ticker == t].iterrows():   # multiply adj_close_fixed over a date range (series-level correction)
        c.loc[(c.date >= q.date_from) & (c.date <= q.date_to), "adj_close_fixed"] *= q.multiplier
    return c


tickers = sorted(set(A.ticker) | set(R.ticker) | set(RS.ticker))
tmp = tempfile.mkdtemp()
for f in os.listdir(ROOT + r"\data\clean"):
    shutil.copy(rf"{ROOT}\data\clean\{f}", tmp)
for t in tickers:
    patched(t).to_csv(rf"{tmp}\{t}.csv", index=False)

sys.path.insert(0, ROOT)
import psx_rl.data as D
old = D.load_panel()[0]
D.CLEAN = tmp
new = D.load_panel()[0]
print("trading calendar before/after:", len(old.index), len(new.index), "| identical:", old.index.equals(new.index))
r_old, r_new = old.pct_change(), new.pct_change()
for t in tickers:
    print(t, "clean rows", len(pd.read_csv(rf"{ROOT}\data\clean\{t}.csv")), "->", len(patched(t)),
          "| days whose return changes:", int(((r_old[t] - r_new[t]).abs() > 1e-9).sum()), "| max |return change|:", round(float((r_old[t] - r_new[t]).abs().max()), 4))
bad = new.pct_change().abs().stack()
print("largest |daily return| among patched tickers after patch:", round(float(new[tickers].pct_change().abs().max().max()), 4))
if "--apply" in sys.argv:
    for t in tickers:
        patched(t).to_csv(rf"{ROOT}\data\clean\{t}.csv", index=False)
    rem = pd.read_csv(ROOT + r"\data\removed_rows.csv", parse_dates=["date"])
    key = set(zip(A.ticker, A.date))
    rem["restored_from_psx"] = [(t, d) in key for t, d in zip(rem.ticker, rem.date)]
    rem.to_csv(ROOT + r"\data\removed_rows.csv", index=False)
    open(ROOT + r"\data\patch\applied.txt", "w").write(f"applied {len(A)} additions and {len(R)} replacements at {pd.Timestamp.now()}\n")
    print("APPLIED:", len(A), "additions,", len(R), "replacements; restored rows flagged in removed_rows.csv:", int(rem.restored_from_psx.sum()))
else:
    print("dry run only; nothing written")
shutil.rmtree(tmp)
