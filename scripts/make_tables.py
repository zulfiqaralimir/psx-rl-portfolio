"""Paper tables (CSV + Markdown) from Stage A/B/C results -> results/tables/."""
import pandas as pd
R = r"D:\psx_rl_portfolio\results"; T = R + r"\tables"
s = pd.read_csv(R + r"\stageC\stageC_summary.csv"); g = pd.read_csv(R + r"\stageC\stageC_significance.csv")
a = pd.read_csv(R + r"\stageA_metrics.csv")

# Table 1: test-split metrics, baselines (Stage A, 0.1% cost) and RL (Stage B, 10-seed mean +- sd)
t1 = a[a.split == "test"][["strategy", "annual_return", "volatility", "sharpe", "max_drawdown", "turnover"]].copy()
t1.insert(1, "n_seeds", 1)
b = s[s.cost_per_side == 0.001]
rl = pd.DataFrame({"strategy": b.algo, "n_seeds": b.n_seeds, "annual_return": b.annual_return_mean, "volatility": b.volatility_mean,
                   "sharpe": b.sharpe_mean, "max_drawdown": b.max_drawdown_mean, "turnover": b.turnover_mean})
t1 = pd.concat([t1, rl]); t1.to_csv(T + r"\table1_test_metrics_cost0.1.csv", index=False)

# Table 2: Sharpe by cost level (mean [95% CI over seeds]) + baselines
rows = []
for c, d in s.groupby("cost_per_side"):
    r = {"cost_per_side": c}
    for _, x in d.iterrows(): r[x.algo] = f"{x.sharpe_mean:.2f} [{x.sharpe_ci_lo:.2f}, {x.sharpe_ci_hi:.2f}]"
    bl = g[g.cost_per_side == c].drop_duplicates("baseline").set_index("baseline").baseline_sharpe
    for k in ("buy_and_hold", "equal_weight_monthly", "mean_variance_monthly", "kse100_benchmark"): r[k] = round(bl[k], 2)
    rows.append(r)
t2 = pd.DataFrame(rows); t2.to_csv(T + r"\table2_sharpe_by_cost.csv", index=False)

# Table 3: Sharpe difference vs each baseline, bootstrap CI and p
t3 = g.copy(); t3.to_csv(T + r"\table3_significance_by_cost.csv", index=False)
open(T + r"\tables.md", "w", encoding="utf-8").write(
    "## Table 1: test-split metrics at 0.1% cost (RL = 10-seed mean)\n\n" + t1.round(3).to_markdown(index=False) +
    "\n\n## Table 2: test Sharpe by cost per side (RL: mean [95% CI over 10 seeds])\n\n" + t2.to_markdown(index=False) +
    "\n\n## Table 3: Sharpe difference (algo - baseline), circular block bootstrap\n\n" + t3.round(3).to_markdown(index=False) + "\n")
print(t1.round(3).to_string(index=False)); print(t2.to_string(index=False))
print("p<0.05 rows:", (g.p_two_sided < 0.05).sum(), " min p:", g.p_two_sided.min(), " rows:", len(g))
print(g[g.p_two_sided < 0.1].round(3).to_string(index=False))
