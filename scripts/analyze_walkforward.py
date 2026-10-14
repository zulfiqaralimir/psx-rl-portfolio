"""Walk-forward: run the Stage B analysis for each window (agents + baselines at 0.1% cost, same protocol), then combine with the
main split into results/walkforward/walkforward_summary.csv and walkforward_significance.csv."""
import os, subprocess, sys
import pandas as pd

ROOT = r"D:\psx_rl_portfolio\results"
WINS = [("w1", "2018-2019", ROOT + r"\walkforward\w1"), ("w2", "2020-2021", ROOT + r"\walkforward\w2"), ("main", "2022-2026", ROOT + r"\retrain_patched\c001")]  # main split: agents retrained on the patched data (patch only touches rows from 2025-04)
S, G = [], []
for w, label, out in WINS:
    env = dict(os.environ, PSX_OUT=out, PSX_COST="0.001")
    env.pop("PSX_WINDOW", None)
    if w != "main": env["PSX_WINDOW"] = w
    r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\analyze_stage_b.py"], env=env, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:]); raise SystemExit(f"analysis failed for {w}")
    open(out + r"\analysis_log.txt", "w").write(r.stdout)
    s = pd.read_csv(out + r"\stageB_summary.csv"); s.insert(0, "test_period", label); s.insert(0, "window", w); S.append(s)
    g = pd.read_csv(out + r"\stageB_significance.csv"); g.insert(0, "test_period", label); g.insert(0, "window", w); G.append(g)
pd.concat(S).to_csv(ROOT + r"\walkforward\walkforward_summary.csv", index=False)
pd.concat(G).to_csv(ROOT + r"\walkforward\walkforward_significance.csv", index=False)
pd.set_option("display.width", 220)
s, g = pd.concat(S), pd.concat(G)
print(s[["window", "test_period", "algo", "n_seeds", "annual_return_mean", "sharpe_mean", "sharpe_ci_lo", "sharpe_ci_hi", "turnover_mean"]].round(3).to_string(index=False))
print(g.drop_duplicates(["window", "baseline"])[["window", "baseline", "baseline_sharpe"]].round(3).to_string(index=False))
print("comparisons:", len(g), " p<0.05:", (g.p_two_sided < 0.05).sum(), " min p:", g.p_two_sided.min())
print(g[g.p_two_sided < 0.1].round(3).to_string(index=False))
