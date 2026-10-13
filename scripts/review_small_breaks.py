"""Triage of the UNVERIFIED flagged rows in data/small_breaks.csv (read-only on prices; only data/small_breaks.csv gets new columns and
data/small_breaks_psx_check.csv is written). Uses data/clean (patched) adj_close_fixed, the series the pipeline uses.
New columns (blank for rows not reviewed here):
  abs_move_pct          |raw close return| in %
  exceeds_7_5pct        |raw move| > 7.5%
  exceeds_empirical_limit  |raw move| > the daily limit seen in this data (7.5% before 2024-07-01, 10% after; scan_small_breaks.py)
  fixed_ret_pct         adj_close_fixed return on the same day, in %
  fixed_shows_same_jump |fixed return - raw return| < 1 percentage point (False => the pipeline series already removes/reduces the jump)
  retrace_d1..d5, retrace_max_1_5   share of the move undone at day i+k: (c[i+k]-c[i]) / (c[i-1]-c[i]), on adj_close_fixed (1 = fully reversed, 0 = held, <0 = extended)
  outcome_1_5d          'reversed' (max retrace >= 0.75), 'held' (retrace at day 5 < 0.25 and max < 0.5), else 'partial'; 'n/a' if fewer than 5 later rows
  proposed_label        genuine | likely data error | needs PSX check (rule below)
  label_reason
Rule: (1) the pipeline series (adj_close_fixed) moves by no more than the empirical daily limit -> genuine (ordinary-size move);
(2) beyond the limit and reversed within 5 days -> likely data error (spike); (3) beyond the limit and held or partial -> needs PSX check
(a held drop larger than the limit that nobody adjusted is the signature of an unadjusted corporate action, a stale/misdated row or a real gap)."""
import numpy as np, pandas as pd

S = pd.read_csv(r"D:\psx_rl_portfolio\data\small_breaks.csv")
new = ["abs_move_pct", "exceeds_7_5pct", "exceeds_empirical_limit", "fixed_ret_pct", "fixed_shows_same_jump", "retrace_d1", "retrace_d2", "retrace_d3", "retrace_d4", "retrace_d5",
       "retrace_max_1_5", "outcome_1_5d", "proposed_label", "label_reason"]
S = S.drop(columns=[c for c in new if c in S.columns])
for c in new: S[c] = np.nan
for c in ("exceeds_7_5pct", "exceeds_empirical_limit", "fixed_shows_same_jump", "outcome_1_5d", "proposed_label", "label_reason"): S[c] = S[c].astype(object)
C = {}
sel = S[S.flag.notna() & (S.review_status == "unverified")].index
for ix in sel:
    r = S.loc[ix]
    if r.ticker not in C: C[r.ticker] = pd.read_csv(rf"D:\psx_rl_portfolio\data\clean\{r.ticker}.csv", parse_dates=["date"]).set_index("date")
    c = C[r.ticker]; d = pd.Timestamp(r.date); i = c.index.get_loc(d)
    fx = c.adj_close_fixed; fret = fx.iloc[i] / fx.iloc[i - 1] - 1
    lim = 0.0755 if d < pd.Timestamp("2024-07-01") else 0.1005
    S.loc[ix, ["abs_move_pct", "exceeds_7_5pct", "exceeds_empirical_limit", "fixed_ret_pct", "fixed_shows_same_jump"]] = [round(abs(r.close_ret) * 100, 2), abs(r.close_ret) > 0.0755, abs(r.close_ret) > lim,
                                                                                                                         round(fret * 100, 2), abs(fret - r.close_ret) < 0.01]
    move = fx.iloc[i - 1] - fx.iloc[i]
    ret = [(fx.iloc[i + k] - fx.iloc[i]) / move if i + k < len(fx) else np.nan for k in range(1, 6)]
    for k, v in enumerate(ret, 1): S.loc[ix, f"retrace_d{k}"] = round(v, 3) if np.isfinite(v) else np.nan
    if np.isfinite(ret).all():
        mx = max(ret); S.loc[ix, "retrace_max_1_5"] = round(mx, 3)
        out = "reversed" if mx >= 0.75 else ("held" if ret[-1] < 0.25 and mx < 0.5 else "partial")
    else:
        mx = np.nan; out = "n/a"
    S.loc[ix, "outcome_1_5d"] = out
    if abs(fret) <= lim:
        lab, why = "genuine", f"adj_close_fixed moves {fret * 100:+.1f}% (<= {lim * 100:.1f}% limit); raw {r.close_ret * 100:+.1f}%"
    elif out == "reversed":
        lab, why = "likely data error", f"adj_close_fixed {fret * 100:+.1f}% beyond the {lim * 100:.1f}% limit and {mx * 100:.0f}% undone within 5 days"
    else:
        lab, why = "needs PSX check", f"adj_close_fixed {fret * 100:+.1f}% beyond the {lim * 100:.1f}% limit, {out} over 1-5 days"
    S.loc[ix, ["proposed_label", "label_reason"]] = [lab, why]
S.to_csv(r"D:\psx_rl_portfolio\data\small_breaks.csv", index=False)
R = S.loc[sel]
print(len(R), "rows triaged;", R.proposed_label.value_counts().to_dict())
print(pd.crosstab(R.proposed_label, R.outcome_1_5d))
print("raw move > 7.5%:", int((R.exceeds_7_5pct == True).sum()), "| > empirical limit:", int((R.exceeds_empirical_limit == True).sum()), "| fixed shows same jump:", int((R.fixed_shows_same_jump == True).sum()), "of", len(R))
P = R[R.proposed_label == "needs PSX check"][["ticker", "date", "close_prev", "close", "close_ret", "fixed_ret_pct", "outcome_1_5d", "retrace_d5", "gap_days", "persistent", "adj_close_status", "label_reason"]].sort_values(["ticker", "date"])
P.to_csv(r"D:\psx_rl_portfolio\data\small_breaks_psx_check.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
print(P.drop(columns=["label_reason"]).to_string(index=False))
