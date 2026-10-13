"""Walk-forward figure: test Sharpe per test period (2018-19, 2020-21, 2022-26): RL mean with 95% CI over seeds, baselines as markers."""
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = r"D:\psx_rl_portfolio\results"
s = pd.read_csv(R + r"\walkforward\walkforward_summary.csv"); g = pd.read_csv(R + r"\walkforward\walkforward_significance.csv")
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"
COL = {"PPO": "#2a78d6", "A2C": "#eb6834", "DDPG": "#1baf7a", "buy_and_hold": "#e87ba4", "equal_weight_monthly": "#008300", "mean_variance_monthly": "#6250d6", "kse100_benchmark": INK}
LAB = {"buy_and_hold": "Buy & hold", "equal_weight_monthly": "EW monthly", "mean_variance_monthly": "Mean-variance", "kse100_benchmark": "KSE-100 (price)"}
MK = {"buy_and_hold": "s", "equal_weight_monthly": "D", "mean_variance_monthly": "^", "kse100_benchmark": "X"}
periods = list(dict.fromkeys(s.test_period)); xs = {p: i for i, p in enumerate(periods)}
fig, ax = plt.subplots(figsize=(9, 5.2), facecolor=SURF); ax.set_facecolor(SURF)
ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.spines["bottom"].set_color("#c3c2b7"); ax.tick_params(colors=MUTED, length=0)
off = {"PPO": -0.2, "A2C": -0.07, "DDPG": 0.06}
for a in ("PPO", "A2C", "DDPG"):
    d = s[s.algo == a]; x = [xs[p] + off[a] for p in d.test_period]
    ax.errorbar(x, d.sharpe_mean, yerr=[d.sharpe_mean - d.sharpe_ci_lo, d.sharpe_ci_hi - d.sharpe_mean], fmt="o", ms=7, color=COL[a], mec=SURF, mew=1.5, capsize=3, lw=1.6, label=f"{a} (mean, 95% CI)")
BOFF = {"buy_and_hold": 0.18, "equal_weight_monthly": 0.24, "mean_variance_monthly": 0.30, "kse100_benchmark": 0.36}
for b in MK:
    d = g[g.baseline == b].drop_duplicates("window")
    ax.plot([xs[p] + BOFF[b] for p in d.test_period], d.baseline_sharpe, MK[b], ms=8, color=COL[b], mec=SURF, mew=1.2, ls="none", label=LAB[b])
ax.axhline(0, color="#c3c2b7", lw=1)
ax.set_xticks(range(len(periods))); ax.set_xticklabels([f"Test {p}" for p in periods], color=INK)
ax.set_ylabel("Test Sharpe", color=MUTED)
ax.set_title("Walk-forward: Sharpe by test period (0.1% cost)", loc="left", color=INK, fontsize=13)
ax.legend(frameon=False, labelcolor=MUTED, fontsize=9, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.08))
fig.text(0.01, 0.01, "Expanding train from 2013; 2-year validation precedes each test. 10 seeds per algorithm. Different periods are not comparable in level.", color=MUTED, fontsize=8)
fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(R + r"\figures\walkforward_sharpe.png", dpi=200)
