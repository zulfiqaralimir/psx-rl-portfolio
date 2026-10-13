"""Core-16 robustness: run the Stage B analysis on results/robustness_core16 (universe = 16 stocks always in KSE-30 over the test split,
cost 0.18%), then put it next to the main 29-stock results at 0.18% (results/stageC/c0018). Writes results/robustness_core16/comparison.csv."""
import os, subprocess, sys
import pandas as pd

ROOT = r"D:\psx_rl_portfolio\results"
CORE = ROOT + r"\robustness_core16"
MAIN = ROOT + r"\stageC\c0018"

env = dict(os.environ, PSX_OUT=CORE, PSX_COST="0.0018", PSX_UNIVERSE="core16")
r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\analyze_stage_b.py"], env=env, capture_output=True, text=True)
if r.returncode:
    print(r.stderr[-1500:]); raise SystemExit("core16 analysis failed")
open(CORE + r"\analysis_log.txt", "w").write(r.stdout)
env = dict(os.environ, PSX_OUT=MAIN, PSX_COST="0.0018")
env.pop("PSX_UNIVERSE", None)
r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\analyze_stage_b.py"], env=env, capture_output=True, text=True)
if r.returncode:
    print(r.stderr[-1500:]); raise SystemExit("main 0.18% analysis failed")
open(MAIN + r"\analysis_log.txt", "w").write(r.stdout)

rows = []
for label, d in (("main_29_stocks", MAIN), ("core16", CORE)):
    s = pd.read_csv(d + r"\stageB_summary.csv"); g = pd.read_csv(d + r"\stageB_significance.csv")
    for _, x in s.iterrows():
        rows.append(dict(universe=label, strategy=x.algo, kind="RL (10-seed mean)", annual_return=x.annual_return_mean, sharpe=x.sharpe_mean,
                         sharpe_ci_lo=x.sharpe_ci_lo, sharpe_ci_hi=x.sharpe_ci_hi, max_drawdown=x.max_drawdown_mean, turnover=x.turnover_mean))
    for b, v in g.drop_duplicates("baseline").set_index("baseline").baseline_sharpe.items():
        rows.append(dict(universe=label, strategy=b, kind="baseline", sharpe=v))
    g.insert(0, "universe", label); g.to_csv(d + r"\comparison_significance.csv", index=False)
C = pd.DataFrame(rows)
C.to_csv(CORE + r"\comparison.csv", index=False)
pd.set_option("display.width", 200)
print(C.round(3).to_string(index=False))
sig = pd.concat([pd.read_csv(MAIN + r"\comparison_significance.csv"), pd.read_csv(CORE + r"\comparison_significance.csv")])
print("comparisons:", len(sig), " p<0.05:", (sig.p_two_sided < 0.05).groupby(sig.universe).sum().to_dict())
print(sig[sig.p_two_sided < 0.1].round(3).to_string(index=False))
