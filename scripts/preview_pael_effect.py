"""Preview (in memory, no files changed) of the PAEL fix on the full-universe BASELINES: rows of PAEL on/before 2013-08-28 get adj_close_fixed x (0.7031 x 1.5)
(replacing the 1/1.5 rescale by 0.7031, the ex-date open/previous-close ratio). The 2014-04-22 bonus is NOT applied: the Yahoo series is already continuous there."""
import sys
sys.path.insert(0, r"D:\psx_rl_portfolio")
import numpy as np, pandas as pd
from psx_rl.data import load_panel, load_policy_rate, split_slice
from psx_rl.env import PortfolioEnv
from psx_rl.metrics import metrics
from psx_rl import baselines as B

P, listed, _ = load_panel(); policy = load_policy_rate()
P2 = P.copy(); P2.loc[P2.index <= "2013-08-28", "PAEL"] *= 0.7031 * 1.5
tr = split_slice(P.index, "train"); rf = policy.reindex(tr.union(policy.index)).ffill().reindex(tr).mean()
rows = []
for name, PP in (("before", P), ("after", P2)):
    w = B.fit_mean_variance(PP, tr, rf)
    for split in ("train", "val", "test"):
        d = split_slice(PP.index, split)
        for strat, fn in (("buy_and_hold", B.buy_and_hold), ("equal_weight_monthly", B.equal_weight_monthly), ("mean_variance_monthly", lambda e: B.mean_variance_monthly(e, w))):
            m = metrics(fn(PortfolioEnv(PP, listed, d, cost=0.001)), policy)
            rows.append(dict(version=name, split=split, strategy=strat, annual_return=m["annual_return"], sharpe=m["sharpe"], max_drawdown=m["max_drawdown"]))
    print(name, "MV weight on PAEL:", round(float(w["PAEL"]), 4), "| non-zero names:", int((w > 1e-4).sum()))
D = pd.DataFrame(rows)
W = D.pivot_table(index=["split", "strategy"], columns="version", values=["sharpe", "annual_return"])
W[("sharpe", "change")] = W[("sharpe", "after")] - W[("sharpe", "before")]
W[("annual_return", "change")] = W[("annual_return", "after")] - W[("annual_return", "before")]
pd.set_option("display.width", 200); print(W.round(4).to_string())
r = P.pct_change()["PAEL"]; r2 = P2.pct_change()["PAEL"]
print("PAEL daily returns that change:", int(((r - r2).abs() > 1e-9).sum()), "on", [d.date().isoformat() for d in r.index[(r - r2).abs() > 1e-9]], "| 2013-08-29 return", round(r["2013-08-29"], 4), "->", round(r2["2013-08-29"], 4))
D.to_csv(r"D:\psx_rl_portfolio\results\pael_preview_baselines.csv", index=False)
