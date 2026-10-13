"""Build the STAGED data patch from the PSX tables (data/psx_tables/*.csv) for MARI, LUCK, BAFL, SYS, UBL. Nothing in data/clean is modified here.
Writes data/patch/: additions.csv (new rows), replacements.csv (rows whose values change), PATCH_SUMMARY.md, and the audit of every PSX date.
For every PSX date the expected clean row is:
  open/high/low/close/volume = PSX values (raw, unadjusted; only adj_close_fixed and row presence are used by the pipeline)
  adj_close        = PSX close x f      where f = Yahoo adj_close/close on the same day (scale-invariant; constant across each gap, asserted)
  adj_close_fixed  = PSX close x f / factor  for dates before the ex-date, PSX close x f on/after it   (the basis of the existing adj_close_fixed)
A date is an ADDITION if it has no clean row, a REPLACEMENT if the clean row's adj_close_fixed differs from the expected one by more than 0.2%.
Also reports clean rows inside a table's date range that PSX does not list (extras)."""
import glob, os
import numpy as np, pandas as pd

CFG = {"MARI": dict(factor=9.0, ex="2024-09-16"), "LUCK": dict(factor=5.0, ex="2025-04-28"), "BAFL": dict(factor=2.0, ex="2026-04-20"),
       "SYS": dict(factor=5.0, ex="2025-06-02"), "UBL": dict(factor=2.0, ex="2025-06-23")}
OUT = r"D:\psx_rl_portfolio\data\patch"; os.makedirs(OUT, exist_ok=True)
add, rep, audit, extras = [], [], [], []
for t, cfg in CFG.items():
    y = pd.read_csv(rf"D:\psx_rl_portfolio\data\raw\{t}.csv", parse_dates=["date"]).set_index("date")
    c = pd.read_csv(rf"D:\psx_rl_portfolio\data\clean\{t}.csv", parse_dates=["date"]).set_index("date")
    P = pd.concat([pd.read_csv(f, parse_dates=["date"]) for f in sorted(glob.glob(rf"D:\psx_rl_portfolio\data\psx_tables\{t}_*.csv"))]).set_index("date").sort_index()
    ex, fac = pd.Timestamp(cfg["ex"]), cfg["factor"]
    fy = (y.adj_close / y.close)
    for d, r in P.iterrows():
        if d not in y.index:
            raise SystemExit(f"{t} {d.date()}: PSX day with no Yahoo row at all (cannot take an adj factor)")
        f = fy[d]
        # f must agree with the nearest rows on both sides unless a dividend goes ex between them
        prev, nxt = fy[fy.index < d].iloc[-1] if (fy.index < d).any() else f, fy[fy.index > d].iloc[0] if (fy.index > d).any() else f
        if abs(f - prev) > 1e-4 and abs(f - nxt) > 1e-4:
            raise SystemExit(f"{t} {d.date()}: adj factor {f} differs from both neighbours ({prev}, {nxt})")
        ac = r.close * f
        fixed = ac / fac if d < ex else ac
        row = dict(ticker=t, date=d.date(), open=r.open, high=r.high, low=r.low, close=r.close, adj_close=round(ac, 6), volume=int(r.volume), adj_close_fixed=round(fixed, 6))
        if d not in c.index:
            reason = "restored: dropped as scale glitch, PSX confirms a real day" if (d in y.index and y.volume[d] > 0) else "missing day: Yahoo has a zero-volume stale row (or none) on a day PSX traded"
            add.append(dict(row, reason=reason))
            audit.append(dict(ticker=t, date=d.date(), action="ADD", psx_close=r.close, clean_fixed=np.nan, expected_fixed=round(fixed, 4)))
        else:
            cur = c.adj_close_fixed[d]; rel = cur / fixed - 1
            if abs(rel) > 0.002:
                rep.append(dict(row, old_adj_close_fixed=round(cur, 6), old_close=c.close[d], old_volume=int(c.volume[d]), rel_change=round(fixed / cur - 1, 4),
                                reason="Yahoo row holds another day's data (date shifted)"))
                audit.append(dict(ticker=t, date=d.date(), action="REPLACE", psx_close=r.close, clean_fixed=round(cur, 4), expected_fixed=round(fixed, 4)))
            else:
                audit.append(dict(ticker=t, date=d.date(), action="ok", psx_close=r.close, clean_fixed=round(cur, 4), expected_fixed=round(fixed, 4)))
    rng = c.loc[P.index.min():P.index.max()].index
    for d in rng.difference(P.index):
        extras.append(dict(ticker=t, date=d.date(), note="clean row on a date the PSX table does not list (check: no change made)"))
A, R, U = pd.DataFrame(add), pd.DataFrame(rep), pd.DataFrame(audit)
A.to_csv(OUT + r"\additions.csv", index=False); R.to_csv(OUT + r"\replacements.csv", index=False); U.to_csv(OUT + r"\audit_all_psx_dates.csv", index=False)
pd.DataFrame(extras, columns=["ticker", "date", "note"]).to_csv(OUT + r"\extras_not_in_psx.csv", index=False)

# ---- series-level rescales (not row-level) ----
# PAEL: adj_close_fixed was adj_close/1.5 before the 2013-08-29 break. The ex-date open / previous close is 0.7032 (Yahoo basis), so the factor should be 0.7031:
# new = adj_close x 0.7031 = old x (0.7031 x 1.5). The 2014-04-22 10% bonus is NOT applied: Yahoo's series is already continuous there (see PATCH_SUMMARY).
pd.DataFrame([dict(ticker="PAEL", date_from="2013-01-01", date_to="2013-08-28", multiplier=round(0.7031 * 1.5, 6),
                   reason="replace the 1/1.5 rescale before the 2013-08-29 break by the ex-date open/prev-close factor 0.7031; makes PAEL's 2013-08-29 return -5.2% (open->close) instead of +0.02%")]
             ).to_csv(OUT + r"\rescale.csv", index=False)

# ---- summary ----
L = ["# Data patch (staged, NOT applied)", "", "Built from the PSX tables in `data/psx_tables/` by `scripts/build_data_patch.py`; applied by `scripts/apply_data_patch.py --apply`.",
     "Only `adj_close_fixed` and row presence feed the pipeline. Expected `adj_close_fixed` = PSX close x Yahoo adj factor, divided by the split factor before the ex-date.", "",
     f"- PSX dates compared: {len(U)} (5 tickers); unchanged: {int((U.action == 'ok').sum())}; rows to ADD: {len(A)}; rows to REPLACE: {len(R)}; extras (clean rows PSX does not list): {len(extras)}", ""]
for t in CFG:
    a, r_ = A[A.ticker == t], R[R.ticker == t]
    L.append(f"## {t} (factor {CFG[t]['factor']:g}, ex-date {CFG[t]['ex']})")
    if a.empty and r_.empty: L.append("- no change: every PSX day in the table already matches the cleaned data")
    for _, x in a.iterrows(): L.append(f"- ADD {x.date}: PSX close {x.close} -> adj_close_fixed {x.adj_close_fixed:.4f} ({x.reason})")
    for _, x in r_.iterrows(): L.append(f"- REPLACE {x.date}: adj_close_fixed {x.old_adj_close_fixed:.4f} -> {x.adj_close_fixed:.4f} ({x.rel_change:+.2%}); {x.reason}")
    L.append("")
L += ["## PAEL (series-level rescale, see rescale.csv)", "- rows 2013-01-01..2013-08-28: adj_close_fixed x 1.05465 (= 0.7031 x 1.5), i.e. factor 0.7031 instead of 1/1.5; PAEL's 2013-08-29 return changes from +0.02% to -5.16% (market median -0.98%; the stock opened at 0.7032 of the previous close and fell 5.2% intraday).",
      "- 2014-04-22 10% bonus (last cum-bonus close 2014-04-21 = 25.68 KSE raw, KSE open 23.35): NOT applied. Yahoo's PAEL series is already continuous there (open/prev close 1.0066, return -1.8%); the KSE-raw / Yahoo ratio drops from 1.4528 to 1.3123 across the two days, a factor 1.107 = the bonus, so Yahoo's earlier rows already contain it. Multiplying 2013-08-29..2014-04-21 by 0.9091 would create a false +8.0% jump on 2014-04-22.", ""]
if extras: L += ["## Extras", *[f"- {e['ticker']} {e['date']}" for e in extras], ""]
open(OUT + r"\PATCH_SUMMARY.md", "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
