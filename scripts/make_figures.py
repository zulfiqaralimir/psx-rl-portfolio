"""Figures for the test split (2022-01-03..2026-10-09): equity curves and Sharpe with 95% CI. Writes results/figures/*.png."""
import sys, glob, os
sys.path.insert(0, r"D:\psx_rl_portfolio")
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from psx_rl.data import load_panel, load_policy_rate, split_slice, load_kse100_close
from psx_rl.env import PortfolioEnv
from psx_rl.metrics import metrics
from psx_rl import baselines as B

OUT = r"D:\psx_rl_portfolio\results\figures"; os.makedirs(OUT, exist_ok=True)
SB = r"D:\psx_rl_portfolio\results\stageB"
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"
COL = {"PPO": "#2a78d6", "A2C": "#eb6834", "DDPG": "#1baf7a", "buy_and_hold": "#e87ba4",
       "equal_weight_monthly": "#008300", "mean_variance_monthly": "#6250d6", "kse100_benchmark": INK}
LAB = {"buy_and_hold": "Buy & hold", "equal_weight_monthly": "EW monthly", "mean_variance_monthly": "Mean-variance",
       "kse100_benchmark": "KSE-100 (price index)", "PPO": "PPO (10-seed mean)", "A2C": "A2C (10-seed mean)", "DDPG": "DDPG (10-seed mean)"}

P, listed, _ = load_panel(); policy = load_policy_rate(); d = split_slice(P.index, "test")
mk = lambda: PortfolioEnv(P, listed, d, cost=0.001)
tr = split_slice(P.index, "train")
mv = B.fit_mean_variance(P, tr, policy.reindex(tr.union(policy.index)).ffill().reindex(tr).mean())
res = {"buy_and_hold": B.buy_and_hold(mk()), "equal_weight_monthly": B.equal_weight_monthly(mk()),
       "mean_variance_monthly": B.mean_variance_monthly(mk(), mv)}
eq = {k: v.total_asset / v.total_asset.iloc[0] * 100 for k, v in res.items()}
kse = load_kse100_close().reindex(P.index).ffill().loc[d]; eq["kse100_benchmark"] = kse / kse.iloc[0] * 100
runs = {a: [pd.read_csv(f, parse_dates=["date"]).set_index("date").total_asset for f in sorted(glob.glob(rf"{SB}\test_series\{a}_*.csv"))] for a in ("PPO", "A2C", "DDPG")}
for a, L in runs.items():
    M = pd.concat([s / s.iloc[0] * 100 for s in L], axis=1); eq[a] = M.mean(axis=1)


def style(ax):
    ax.set_facecolor(SURF); ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7"); ax.tick_params(colors=MUTED, length=0)


# ---- Fig 1: equity curves ----
fig, ax = plt.subplots(figsize=(10, 5.4), facecolor=SURF); style(ax)
for k in ["buy_and_hold", "equal_weight_monthly", "mean_variance_monthly", "PPO", "A2C", "DDPG", "kse100_benchmark"]:
    s = eq[k]; ax.plot(s.index, s.values, color=COL[k], lw=2.4 if k == "kse100_benchmark" else 1.6,
                       ls="--" if k in runs else "-", label=LAB[k])
ax.set_yscale("log"); ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator()); ax.set_yticks([100, 150, 200, 300, 400, 500]); ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax.set_ylabel("Value, start = 100 (log scale)", color=MUTED)
ax.set_title("Test split 2022-2026: no learned policy separates from the baselines", loc="left", color=INK, fontsize=13)
ax.legend(frameon=False, labelcolor=MUTED, fontsize=9, ncol=2, loc="upper left")
fig.text(0.01, 0.01, "Strategies include 0.1% cost per side and are total-return; KSE-100 is a price index (no dividends). Survivorship-biased universe.", color=MUTED, fontsize=8)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(rf"{OUT}\test_equity.png", dpi=200); plt.close(fig)

# ---- Fig 2: Sharpe with 95% CI ----
rows = []
for k, v in list(res.items()):
    rows.append((LAB[k], k, metrics(v, policy)["sharpe"], None))
ks = pd.DataFrame({"total_asset": eq["kse100_benchmark"]}); rows.append((LAB["kse100_benchmark"], "kse100_benchmark", metrics(ks, policy, turnover=False)["sharpe"], None))
R = pd.read_csv(rf"{SB}\stageB_runs.csv")
for a in ("PPO", "A2C", "DDPG"):
    x = R[R.algo == a].test_sharpe.to_numpy(); h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    rows.append((f"{a} (mean of {len(x)} seeds)", a, x.mean(), h))
rows.sort(key=lambda r: r[2])
fig, ax = plt.subplots(figsize=(8.5, 4.6), facecolor=SURF); style(ax); ax.grid(axis="x", color=GRID, lw=0.8); ax.grid(axis="y", visible=False)
for i, (lab, k, m, h) in enumerate(rows):
    if h: ax.errorbar(m, i, xerr=h, color=COL[k], capsize=4, lw=1.6)
    ax.plot(m, i, "o", ms=9, color=COL[k], mec=SURF, mew=2)
    ax.text(m + (h or 0) + 0.03, i, f"{m:.2f}", va="center", color=MUTED, fontsize=9)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], color=INK)
ax.set_xlabel("Test-split Sharpe (excess over SBP policy rate); bars = 95% CI over seeds", color=MUTED)
ax.set_title("Sharpe ratio, test 2022-2026", loc="left", color=INK, fontsize=13)
fig.tight_layout(); fig.savefig(rf"{OUT}\test_sharpe.png", dpi=200); plt.close(fig)
print("saved", os.listdir(OUT))
