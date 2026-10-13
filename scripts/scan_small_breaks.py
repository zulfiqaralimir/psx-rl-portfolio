"""Scan data/clean for persistent price breaks of 5-30% in the unadjusted close and compare with Yahoo's adj_close.
Writes data/small_breaks.csv. Read-only: no price data is changed.
Columns: close_ret = day-over-day change in close between consecutive rows; adj_ret = same for adj_close;
absorbed = share of the break that adj_close removed ((close_ret - adj_ret)/close_ret; ~1 = adj_close adjusted it, ~0 = it did not);
persist_ratio = median close over the next 10 rows / median over the previous 10 rows - 1 (same sign and >= half the break => persistent);
market_median = median close_ret of all tickers that day (flags market-wide moves); idio = close_ret - market_median."""
import glob, os
import numpy as np, pandas as pd

LO, HI = 0.05, 0.30
rets = {}
frames = {}
for f in sorted(glob.glob(r"D:\psx_rl_portfolio\data\clean\*.csv")):
    t = os.path.basename(f)[:-4]
    c = pd.read_csv(f, parse_dates=["date"]).set_index("date")
    frames[t] = c
    rets[t] = c.close.pct_change()
R = pd.DataFrame(rets)
mkt = R.median(axis=1)
splits = pd.read_csv(r"D:\psx_rl_portfolio\data\split_events.csv", parse_dates=["break_date"])

rows = []
for t, c in frames.items():
    cr = c.close.pct_change(); ar = c.adj_close.pct_change()
    vol_med = c.volume.rolling(20, min_periods=5).median().shift(1)
    for i in np.where((cr.abs() >= LO) & (cr.abs() <= HI))[0]:
        d = c.index[i]
        pre = c.close.iloc[max(0, i - 10):i]; post = c.close.iloc[i:i + 10]
        pr = post.median() / pre.median() - 1 if len(pre) >= 3 and len(post) >= 3 else np.nan
        persistent = bool(np.isfinite(pr) and np.sign(pr) == np.sign(cr.iloc[i]) and abs(pr) >= 0.5 * abs(cr.iloc[i]))
        absorbed = (cr.iloc[i] - ar.iloc[i]) / cr.iloc[i]
        status = "adjusted" if absorbed >= 0.8 else ("partly adjusted" if absorbed >= 0.2 else "NOT adjusted")
        gap = (d - c.index[i - 1]).days
        rows.append(dict(ticker=t, date=d.date(), prev_date=c.index[i - 1].date(), gap_days=gap, close_prev=round(c.close.iloc[i - 1], 3), close=round(c.close.iloc[i], 3),
                         close_ret=round(cr.iloc[i], 4), adj_ret=round(ar.iloc[i], 4), absorbed=round(absorbed, 3), adj_close_status=status,
                         persist_ratio=round(pr, 4) if np.isfinite(pr) else np.nan, persistent=persistent,
                         market_median=round(mkt.loc[d], 4), idio=round(cr.iloc[i] - mkt.loc[d], 4), market_wide=bool(abs(mkt.loc[d]) >= 0.03),
                         volume_vs_20d_median=round(c.volume.iloc[i] / vol_med.iloc[i], 2) if vol_med.iloc[i] > 0 else np.nan,
                         near_known_split=bool(((splits.ticker == t) & ((splits.break_date - d).abs() <= pd.Timedelta(days=20))).any())))
D = pd.DataFrame(rows).sort_values(["date", "ticker"])
# Observed daily-move cliff: counts drop sharply above 7.5% until mid-2024 and above 10% afterwards (empirical, from this data), so a close-to-close move
# beyond that is unlikely to be an ordinary trading-day move: it is either an ex-date (dividend/bonus/rights) or a limit-free event.
D["beyond_daily_limit"] = D.close_ret.abs() > np.where(pd.to_datetime(D.date) < "2024-07-01", 0.0755, 0.1005)
D["flag"] = np.where((D.close_ret < 0) & D.beyond_daily_limit & ~D.market_wide & (D.adj_close_status != "adjusted"),
                     "CHECK: drop beyond daily limit, not market-wide, adj_close did not (fully) adjust", "")
D["review_status"] = np.where(D.near_known_split, "reviewed: near a split event checked against PSX tables (data/split_events.csv)", "unverified")
D.to_csv(r"D:\psx_rl_portfolio\data\small_breaks.csv", index=False)

print("candidate days with |close return| in [5%, 30%]:", len(D), "across", D.ticker.nunique(), "tickers")
print("within the ordinary daily range (cannot be told from a real move):", int((~D.beyond_daily_limit).sum()), "| beyond it:", int(D.beyond_daily_limit.sum()))
B = D[D.beyond_daily_limit]
print("beyond-limit by sign:", {"down": int((B.close_ret < 0).sum()), "up": int((B.close_ret > 0).sum())}, "| market-wide days:", int(B.market_wide.sum()))
print("beyond-limit DOWN moves by adj_close status:", B[B.close_ret < 0].adj_close_status.value_counts().to_dict())
print("beyond-limit UP moves by adj_close status:", B[B.close_ret > 0].adj_close_status.value_counts().to_dict())
F = D[D.flag != ""]
print("FLAGGED:", len(F), "| persistent among them:", int(F.persistent.sum()), "| by status:", F.adj_close_status.value_counts().to_dict())
print(F[["ticker", "date", "gap_days", "close_prev", "close", "close_ret", "adj_ret", "absorbed", "persist_ratio", "idio", "volume_vs_20d_median"]].to_string(index=False))
print("beyond-limit drops that adj_close DID adjust, per ticker:", B[(B.close_ret < 0) & (B.adj_close_status == "adjusted")].ticker.value_counts().to_dict())
