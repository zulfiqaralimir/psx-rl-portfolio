"""Analyse the training-length ablation: results/ablation_steps300k/{steps300k,steps100k_control}. Runs the Stage B analysis (bootstrap vs the baselines,
including buy-and-hold) for each, then writes comparison.csv (mean test Sharpe / return / turnover with 95% CI over seeds, chosen checkpoint step, Sharpe
difference vs buy-and-hold with bootstrap CI), checkpoints.csv (best_step and best validation Sharpe for every run) and paired_diff.csv (300k minus 100k
control, paired by seed)."""
import os, subprocess, sys, json, glob
import numpy as np, pandas as pd
from scipy import stats

ROOT = r"D:\psx_rl_portfolio\results"
AB = ROOT + r"\ablation_steps300k"
CFG = {"100k_control (patched)": AB + r"\steps100k_control", "300k": AB + r"\steps300k", "main 100k (trained pre-patch, re-scored)": ROOT + r"\stageB"}
for name, d in CFG.items():
    if "main" in name: continue
    env = dict(os.environ, PSX_OUT=d, PSX_COST="0.001"); env.pop("PSX_UNIVERSE", None); env.pop("PSX_WINDOW", None)
    r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\analyze_stage_b.py"], env=env, capture_output=True, text=True)
    if r.returncode: print(r.stderr[-1500:]); raise SystemExit("analysis failed: " + name)
    open(d + r"\analysis_log.txt", "w").write(r.stdout)

runs = []
for name, d in CFG.items():
    for f in sorted(glob.glob(d + r"\*_[0-9].json")):
        j = json.load(open(f))
        if j["algo"] in ("PPO", "A2C"): runs.append(dict(config=name, algo=j["algo"], seed=j["seed"], steps=j["steps"], best_step=j["best_step"], best_val_sharpe=j["best_val_sharpe"],
                                                         test_sharpe=j["test_sharpe"], test_annual_return=j["test_annual_return"], test_turnover=j["test_turnover"]))
R = pd.DataFrame(runs); R.to_csv(AB + r"\checkpoints.csv", index=False)

def ci(x):
    x = np.asarray(x, float); n = len(x)
    h = stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    return x.mean(), x.mean() - h, x.mean() + h

rows = []
for (cfg, algo), g in R.groupby(["config", "algo"]):
    d = CFG[cfg]; sig = pd.read_csv(d + r"\stageB_significance.csv"); s = sig[(sig.algo == algo) & (sig.baseline == "buy_and_hold")].iloc[0]
    row = dict(config=cfg, algo=algo, n_seeds=len(g), best_step_mean=g.best_step.mean(), best_step_median=g.best_step.median(), best_step_min=g.best_step.min(), best_step_max=g.best_step.max())
    for k in ("test_sharpe", "test_annual_return", "test_turnover"):
        m, lo, hi = ci(g[k]); row.update({f"{k}_mean": m, f"{k}_ci_lo": lo, f"{k}_ci_hi": hi})
    row.update(buy_and_hold_sharpe=s.baseline_sharpe, diff_vs_bh=s.sharpe_diff, diff_ci_lo=s.ci_lo, diff_ci_hi=s.ci_hi, diff_p=s.p_two_sided)
    rows.append(row)
C = pd.DataFrame(rows); C.to_csv(AB + r"\comparison.csv", index=False)

pr = []
rng = np.random.default_rng(7)
for algo in ("PPO", "A2C"):
    a = R[(R.config == "300k") & (R.algo == algo)].set_index("seed"); b = R[(R.config == "100k_control (patched)") & (R.algo == algo)].set_index("seed")
    seeds = a.index.intersection(b.index)
    for k in ("test_sharpe", "test_annual_return", "test_turnover"):
        d = (a.loc[seeds, k] - b.loc[seeds, k]).to_numpy()
        m, lo, hi = ci(d); bs = np.array([rng.choice(d, len(d)).mean() for _ in range(10000)])
        pr.append(dict(algo=algo, metric=k, n_pairs=len(d), mean_diff_300k_minus_100k=m, t_ci_lo=lo, t_ci_hi=hi, boot_ci_lo=np.percentile(bs, 2.5), boot_ci_hi=np.percentile(bs, 97.5),
                       seeds_300k_better=int((d > 0).sum())))
P = pd.DataFrame(pr); P.to_csv(AB + r"\paired_diff.csv", index=False)
pd.set_option("display.width", 220)
print(C[["config", "algo", "n_seeds", "test_sharpe_mean", "test_sharpe_ci_lo", "test_sharpe_ci_hi", "test_annual_return_mean", "test_turnover_mean", "best_step_median", "diff_vs_bh", "diff_ci_lo", "diff_ci_hi", "diff_p"]].round(3).to_string(index=False))
print(P.round(4).to_string(index=False))
print(R[R.config != "main 100k (trained pre-patch, re-scored)"].groupby(["config", "algo"]).best_step.apply(lambda s: sorted(s.tolist())).to_string())
