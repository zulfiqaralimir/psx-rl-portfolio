"""Stage B analysis: per-algo test mean/std/95% CI over seeds, and Sharpe-difference bootstrap vs each baseline.
Bootstrap: circular block bootstrap of test days (block 20), shared by algo and baseline; seeds resampled with
replacement each draw. Diff = mean over resampled seeds of Sharpe(algo) - Sharpe(baseline). Two-sided p from the
bootstrap distribution of the diff. Test is only read here, after all checkpoints were chosen on validation."""
import sys, glob, json, os
sys.path.insert(0, r"D:\psx_rl_portfolio")
import numpy as np, pandas as pd
from scipy import stats
from psx_rl.data import load_panel, load_policy_rate, split_slice, load_kse100_close
from psx_rl.env import PortfolioEnv
from psx_rl.metrics import metrics
from psx_rl import baselines as B

OUT = os.environ.get("PSX_OUT", r"D:\psx_rl_portfolio\results\stageB")
COST = float(os.environ.get("PSX_COST", "0.001"))  # Stage C: baselines run at the same cost as the agents
NBOOT, BLOCK = 4000, 20
rng = np.random.default_rng(12345)

P, listed, _ = load_panel(); policy = load_policy_rate()
runs = [json.load(open(f)) for f in sorted(glob.glob(OUT + r"\*_[0-9].json"))]
R = pd.DataFrame(runs)
cols = ["test_annual_return", "test_volatility", "test_sharpe", "test_max_drawdown", "test_exposure", "test_cash_share", "test_turnover"]
R.drop(columns=["val_history"]).to_csv(OUT + r"\stageB_runs.csv", index=False)

# ---- per-algo summary ----
rows = []
for algo, g in R.groupby("algo"):
    row = {"algo": algo, "n_seeds": len(g)}
    for c in cols:
        x = g[c].to_numpy(); n = len(x)
        m, s = x.mean(), x.std(ddof=1) if n > 1 else np.nan
        h = stats.t.ppf(0.975, n - 1) * s / np.sqrt(n) if n > 1 else np.nan
        row.update({f"{c[5:]}_mean": m, f"{c[5:]}_std": s, f"{c[5:]}_ci_lo": m - h, f"{c[5:]}_ci_hi": m + h})
    rows.append(row)
summ = pd.DataFrame(rows); summ.to_csv(OUT + r"\stageB_summary.csv", index=False)

# ---- daily excess-return matrices on the test period ----
test_dates = split_slice(P.index, "test")
ann = float(R.test_ann_days.mean())


def daily(series):
    a = series.total_asset if hasattr(series, "total_asset") else series
    return a.pct_change().dropna()


series = {}
mk = lambda: PortfolioEnv(P, listed, test_dates, cost=COST)
mv = B.fit_mean_variance(P, split_slice(P.index, "train"),
                         policy.reindex(split_slice(P.index, "train").union(policy.index)).ffill().reindex(split_slice(P.index, "train")).mean())
base = {"buy_and_hold": B.buy_and_hold(mk()), "equal_weight_monthly": B.equal_weight_monthly(mk()),
        "mean_variance_monthly": B.mean_variance_monthly(mk(), mv)}
for k, v in base.items():
    series[k] = daily(v)
series["kse100_benchmark"] = load_kse100_close().reindex(P.index).ffill().pct_change().reindex(series["buy_and_hold"].index).dropna()
algo_series = {}
for f in sorted(glob.glob(OUT + r"\test_series\*.csv")):
    name = os.path.basename(f)[:-4]
    algo_series[name] = daily(pd.read_csv(f, parse_dates=["date"]).set_index("date"))
idx = series["buy_and_hold"].index
for s in list(series.values()) + list(algo_series.values()):
    idx = idx.intersection(s.index)
prev = P.index[P.index.get_indexer(idx) - 1]   # rate in force at the start of each return day, as in metrics.py
rf = policy.reindex(prev.union(policy.index)).ffill().reindex(prev).to_numpy() / ann
T = len(idx)


def mat(d):
    return np.column_stack([d[k].reindex(idx).to_numpy() for k in d])


Ra, Rb = mat(algo_series), mat(series)
names_a, names_b = list(algo_series), list(series)


def sharpe_cols(X, ix):
    x = X[ix]; r = rf[ix][:, None]
    return (x - r).mean(axis=0) / x.std(axis=0, ddof=1) * np.sqrt(ann)


nb = int(np.ceil(T / BLOCK))
point_a, point_b = sharpe_cols(Ra, np.arange(T)), sharpe_cols(Rb, np.arange(T))
algo_of = np.array([n.split("_")[0] for n in names_a])
diffs = {(a, b): [] for a in sorted(set(algo_of)) for b in names_b}
for _ in range(NBOOT):
    starts = rng.integers(0, T, nb)
    ix = ((starts[:, None] + np.arange(BLOCK)[None, :]) % T).ravel()[:T]
    sa, sb = sharpe_cols(Ra, ix), sharpe_cols(Rb, ix)
    for a in sorted(set(algo_of)):
        cols_a = np.where(algo_of == a)[0]
        pick = rng.choice(cols_a, len(cols_a), replace=True)
        for j, b in enumerate(names_b):
            diffs[(a, b)].append(sa[pick].mean() - sb[j])
rows = []
for (a, b), d in diffs.items():
    d = np.array(d); pt = point_a[algo_of == a].mean() - point_b[names_b.index(b)]
    p = min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))
    rows.append({"algo": a, "baseline": b, "algo_sharpe_mean": point_a[algo_of == a].mean(), "baseline_sharpe": point_b[names_b.index(b)],
                 "sharpe_diff": pt, "ci_lo": np.percentile(d, 2.5), "ci_hi": np.percentile(d, 97.5), "p_two_sided": p})
sig = pd.DataFrame(rows).sort_values(["algo", "baseline"]); sig.to_csv(OUT + r"\stageB_significance.csv", index=False)
pd.set_option("display.width", 250)
print(f"{len(R)} runs, test days {T}, ann {ann:.0f}")
print(summ[["algo", "n_seeds"] + [c for c in summ.columns if c.endswith(("_mean", "_std", "_ci_lo", "_ci_hi")) and c.split("_")[0] in ("annual", "sharpe", "max", "exposure", "cash", "turnover", "volatility")]].round(3).T.to_string())
print(sig.round(3).to_string(index=False))
