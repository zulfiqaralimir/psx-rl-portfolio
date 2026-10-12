"""Run all Stage B runs (10 seeds x PPO/A2C/DDPG) with 4 parallel workers, longest jobs first; skips finished runs."""
import subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
OUT = r"D:\psx_rl_portfolio\results\stageB"
STEPS = 100_000
jobs = [(a, s) for a in ("DDPG", "PPO", "A2C") for s in range(10) if not os.path.exists(rf"{OUT}\{a}_{s}.json")]
print(len(jobs), "jobs", flush=True)

def run(j):
    a, s = j
    with open(rf"{OUT}\log_{a}_{s}.txt", "w") as f:
        r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\train_stage_b.py", a, str(s), str(STEPS)], stdout=f, stderr=subprocess.STDOUT)
    print(a, s, "exit", r.returncode, flush=True)

with ThreadPoolExecutor(4) as ex:
    list(ex.map(run, jobs))
print("ALL DONE", flush=True)
