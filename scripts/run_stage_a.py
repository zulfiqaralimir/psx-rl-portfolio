"""Stage A: baselines only, no training. Writes results/stageA_metrics.csv."""
import sys
sys.path.insert(0, r"D:\psx_rl_portfolio")
import numpy as np, pandas as pd
from psx_rl.data import load_panel, load_policy_rate, split_slice, load_kse100_close
from psx_rl.env import PortfolioEnv
from psx_rl.metrics import metrics
from psx_rl import baselines as B

COST = 0.001
P, listed, traded = load_panel()
policy = load_policy_rate()
print(f"calendar {P.index[0].date()}..{P.index[-1].date()}  {len(P)} days  {P.shape[1]} tickers")
train_dates = split_slice(P.index, "train")
rf_train = policy.reindex(train_dates.union(policy.index)).ffill().reindex(train_dates).mean()
w_mv = B.fit_mean_variance(P, train_dates, rf_train)
w_mv[w_mv > 1e-4].sort_values(ascending=False).round(3).to_csv(r"D:\psx_rl_portfolio\results\mv_weights_trainfit.csv", header=["weight"])
print("MV non-zero weights:", (w_mv > 1e-4).sum(), " max", w_mv.max().round(3), " rf_train", round(rf_train, 4))

kse = load_kse100_close().reindex(P.index).ffill()  # KSE-100 price index on the strategies' calendar
rows = []
for split in ["train", "val", "test"]:
    d = split_slice(P.index, split)
    runs = {}
    for name, fn in [("buy_and_hold", B.buy_and_hold), ("equal_weight_monthly", B.equal_weight_monthly),
                     ("mean_variance_monthly", lambda e: B.mean_variance_monthly(e, w_mv))]:
        env = PortfolioEnv(P, listed, d, cost=COST)
        runs[name] = (fn(env), True)
    a = 1e6 * kse.loc[d] / kse.loc[d[0]]
    runs["kse100_benchmark"] = (pd.DataFrame({"total_asset": a, "stock_value": a, "traded": 0.0}), False)
    for name, (res, to) in runs.items():
        m = metrics(res, policy, turnover=to)
        rows.append({"split": split, "strategy": name, "start": res.index[0].date(), "end": res.index[-1].date(), **m})
out = pd.DataFrame(rows)
out.to_csv(r"D:\psx_rl_portfolio\results\stageA_metrics.csv", index=False)
pd.set_option("display.width", 250)
show = out.copy()
for c in ["annual_return", "volatility", "max_drawdown", "exposure", "cash_share"]:
    show[c] = (show[c] * 100).round(1)
show["sharpe"] = show.sharpe.round(2); show["turnover"] = show.turnover.round(2); show["ann_days"] = show.ann_days.round(0)
print(show.drop(columns=["start", "years"]).to_string(index=False))
print(out.groupby("split")[["start", "end", "n_days"]].first())
