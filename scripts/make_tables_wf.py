"""Walk-forward tables 4 and 5 -> results/tables/ (CSV) and appended to tables.md (run after make_tables.py; idempotent)."""
import pandas as pd
R = r"D:\psx_rl_portfolio\results"; T = R + r"\tables"
w = pd.read_csv(R + r"\walkforward\walkforward_summary.csv"); wg = pd.read_csv(R + r"\walkforward\walkforward_significance.csv")
rows = []
for (win, per), d in w.groupby(["window", "test_period"], sort=False):
    r = {"window": win, "test_period": per}
    for _, x in d.iterrows(): r[x.algo] = f"{x.sharpe_mean:.2f} [{x.sharpe_ci_lo:.2f}, {x.sharpe_ci_hi:.2f}]"
    bl = wg[wg.window == win].drop_duplicates("baseline").set_index("baseline").baseline_sharpe
    for k in ("buy_and_hold", "equal_weight_monthly", "mean_variance_monthly", "kse100_benchmark"): r[k] = round(bl[k], 2)
    rows.append(r)
t4 = pd.DataFrame(rows); t4.to_csv(T + r"\table4_walkforward_sharpe.csv", index=False)
wg.to_csv(T + r"\table5_walkforward_significance.csv", index=False)
md = open(T + r"\tables.md", encoding="utf-8").read().split("\n\n## Table 4")[0]
md += "\n\n## Table 4: walk-forward test Sharpe at 0.1% cost (RL: mean [95% CI over 10 seeds])\n\n" + t4.to_markdown(index=False)
md += "\n\n## Table 5: walk-forward Sharpe differences (algo - baseline), circular block bootstrap\n\n" + wg.round(3).to_markdown(index=False) + "\n"
open(T + r"\tables.md", "w", encoding="utf-8").write(md)
print(t4.to_string(index=False))
