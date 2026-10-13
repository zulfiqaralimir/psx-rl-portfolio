"""Robustness: universe = the 16 stocks that were KSE-30 members for 100% of 2022-01-03..2026-10-09 (data/universe_core16.txt),
cost 0.18%, Stage B protocol/hyperparameters, PPO/A2C/DDPG x10 seeds. 2 workers; skips finished runs."""
import subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
OUT = r"D:\psx_rl_portfolio\results\robustness_core16"
os.makedirs(OUT, exist_ok=True)
jobs = [(a, s) for a in ("DDPG", "PPO", "A2C") for s in range(10) if not os.path.exists(rf"{OUT}\{a}_{s}.json")]
print(len(jobs), "jobs", flush=True)

def run(j):
    a, s = j
    env = dict(os.environ, PSX_OUT=OUT, PSX_COST="0.0018", PSX_UNIVERSE="core16")
    with open(rf"{OUT}\log_{a}_{s}.txt", "w") as f:
        r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\train_stage_b.py", a, str(s), "100000"], stdout=f, stderr=subprocess.STDOUT, env=env)
    print(a, s, "exit", r.returncode, flush=True)

with ThreadPoolExecutor(2) as ex:
    list(ex.map(run, jobs))
print("ALL DONE", flush=True)
