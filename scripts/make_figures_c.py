"""Stage C figure: test Sharpe vs per-side cost for PPO/A2C/DDPG (mean over 10 seeds, 95% CI) with baselines at the same cost."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

R = r"D:\psx_rl_portfolio\results"
s = pd.read_csv(R + r"\stageC\stageC_summary.csv"); g = pd.read_csv(R + r"\stageC\stageC_significance.csv")
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"
COL = {"PPO": "#2a78d6", "A2C": "#eb6834", "DDPG": "#1baf7a", "buy_and_hold": "#e87ba4", "equal_weight_monthly": "#008300", "mean_variance_monthly": "#6250d6", "kse100_benchmark": INK}
LAB = {"buy_and_hold": "Buy & hold", "equal_weight_monthly": "EW monthly", "mean_variance_monthly": "Mean-variance", "kse100_benchmark": "KSE-100 (price, no cost)"}
fig, ax = plt.subplots(figsize=(9, 5.2), facecolor=SURF); ax.set_facecolor(SURF)
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.spines["bottom"].set_color("#c3c2b7"); ax.tick_params(colors=MUTED, length=0)
for b in ["mean_variance_monthly", "buy_and_hold", "equal_weight_monthly", "kse100_benchmark"]:
    d = g[(g.baseline == b)].drop_duplicates("cost_per_side").sort_values("cost_per_side")
    ax.plot(d.cost_per_side, d.baseline_sharpe, color=COL[b], lw=2.2 if b == "kse100_benchmark" else 1.6, ls="-", label=LAB[b])
off = {"PPO": -0.00012, "A2C": 0.0, "DDPG": 0.00012}
for a in ("PPO", "A2C", "DDPG"):
    d = s[s.algo == a].sort_values("cost_per_side")
    x = d.cost_per_side + off[a]
    ax.errorbar(x, d.sharpe_mean, yerr=[d.sharpe_mean - d.sharpe_ci_lo, d.sharpe_ci_hi - d.sharpe_mean], color=COL[a], marker="o", ms=7,
                mec=SURF, mew=1.5, lw=1.6, capsize=3, ls="--", label=f"{a} (mean, 95% CI)")
ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=2)); ax.set_xticks([0, 0.001, 0.0018, 0.0025, 0.005]); ax.tick_params(axis="x", labelsize=8)
ax.set_xlabel("Transaction cost per side (agents trained and tested at this cost)", color=MUTED); ax.set_ylabel("Test-split Sharpe", color=MUTED)
ax.set_title("Sharpe vs transaction cost, test 2022-2026", loc="left", color=INK, fontsize=13)
ax.legend(frameon=False, labelcolor=MUTED, fontsize=9, ncol=2, loc="lower left")
fig.text(0.01, 0.01, "10 seeds per algorithm. Baselines re-run at each cost. KSE-100 is a price index with no dividends and no cost.", color=MUTED, fontsize=8)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(R + r"\figures\cost_sensitivity_sharpe.png", dpi=200)
