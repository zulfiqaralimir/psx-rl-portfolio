"""Stage C: run the Stage B analysis at each cost level (agents and baselines at the same per-side cost), then combine
into results/stageC/stageC_summary.csv and stageC_significance.csv. Cost 0.1% is the Stage B run."""
import os, subprocess, sys
import pandas as pd

ROOT = r"D:\psx_rl_portfolio\results"
LEVELS = [("0.0%", 0.0, ROOT + r"\stageC\c0"), ("0.1%", 0.001, ROOT + r"\stageB"),
          ("0.25%", 0.0025, ROOT + r"\stageC\c0025"), ("0.5%", 0.005, ROOT + r"\stageC\c005")]
S, G = [], []
for label, c, out in LEVELS:
    env = dict(os.environ, PSX_OUT=out, PSX_COST=str(c))
    r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\analyze_stage_b.py"], env=env, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:]); raise SystemExit(f"analysis failed at cost {label}")
    open(out + r"\analysis_log.txt", "w").write(r.stdout)
    s = pd.read_csv(out + r"\stageB_summary.csv"); s.insert(0, "cost_per_side", c); S.append(s)
    g = pd.read_csv(out + r"\stageB_significance.csv"); g.insert(0, "cost_per_side", c); G.append(g)
pd.concat(S).to_csv(ROOT + r"\stageC\stageC_summary.csv", index=False)
pd.concat(G).to_csv(ROOT + r"\stageC\stageC_significance.csv", index=False)
pd.set_option("display.width", 220)
s = pd.concat(S)
print(s[["cost_per_side", "algo", "annual_return_mean", "sharpe_mean", "sharpe_ci_lo", "sharpe_ci_hi", "turnover_mean"]].round(3).to_string(index=False))
g = pd.concat(G)
print(g[g.baseline.isin(["buy_and_hold", "kse100_benchmark"])][["cost_per_side", "algo", "baseline", "baseline_sharpe", "sharpe_diff", "ci_lo", "ci_hi", "p_two_sided"]].round(3).to_string(index=False))
