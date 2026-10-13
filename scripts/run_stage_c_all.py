"""Stage C: cost sensitivity. Trains/validates/tests PPO, A2C, DDPG x10 seeds at per-side costs 0, 0.25%, 0.5%
(0.1% is Stage B). Same protocol/hyperparameters as Stage B. 2 parallel workers; skips finished runs."""
import subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = r"D:\psx_rl_portfolio\results\stageC"
COSTS = {"c0": 0.0, "c0018": 0.0018, "c0025": 0.0025, "c005": 0.005}  # c0018 = realistic PSX/CDC/SECP cost, see data/fee_schedule.csv
STEPS = 100_000
jobs = []
for tag, c in COSTS.items():
    os.makedirs(rf"{ROOT}\{tag}", exist_ok=True)
    jobs += [(tag, c, a, s) for a in ("DDPG", "PPO", "A2C") for s in range(10) if not os.path.exists(rf"{ROOT}\{tag}\{a}_{s}.json")]
jobs.sort(key=lambda j: ("DDPG", "PPO", "A2C").index(j[2]))
print(len(jobs), "jobs", flush=True)

def run(j):
    tag, c, a, s = j
    env = dict(os.environ, PSX_OUT=rf"{ROOT}\{tag}", PSX_COST=str(c))
    with open(rf"{ROOT}\{tag}\log_{a}_{s}.txt", "w") as f:
        r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\train_stage_b.py", a, str(s), str(STEPS)], stdout=f, stderr=subprocess.STDOUT, env=env)
    print(tag, a, s, "exit", r.returncode, flush=True)

with ThreadPoolExecutor(2) as ex:
    list(ex.map(run, jobs))
print("ALL DONE", flush=True)
