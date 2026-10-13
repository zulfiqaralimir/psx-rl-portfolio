"""Retrain on the PATCHED data (data/clean after the PSX patch + PAEL rescale): PPO, A2C, DDPG x 10 seeds (0-9), same hyperparameters/protocol/seeds as Stage B/C.
Usage: run_retrain_all.py c0018 [c001 c0 ...]. Output results/retrain_patched/<tag>. 2 workers; skips finished runs."""
import subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = r"D:\psx_rl_portfolio\results\retrain_patched"
ALL = {"c0": 0.0, "c001": 0.001, "c0018": 0.0018}
tags = sys.argv[1:] or ["c0018"]
STEPS = 100_000
jobs = []
for tag in tags:
    os.makedirs(rf"{ROOT}\{tag}", exist_ok=True)
    jobs += [(tag, ALL[tag], a, s) for a in ("DDPG", "PPO", "A2C") for s in range(10) if not os.path.exists(rf"{ROOT}\{tag}\{a}_{s}.json")]
print(len(jobs), "jobs", tags, flush=True)

def run(j):
    tag, c, a, s = j
    env = dict(os.environ, PSX_OUT=rf"{ROOT}\{tag}", PSX_COST=str(c))
    with open(rf"{ROOT}\{tag}\log_{a}_{s}.txt", "w") as f:
        r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\train_stage_b.py", a, str(s), str(STEPS)], stdout=f, stderr=subprocess.STDOUT, env=env)
    print(tag, a, s, "exit", r.returncode, flush=True)

with ThreadPoolExecutor(2) as ex:
    list(ex.map(run, jobs))
print("ALL DONE", flush=True)
