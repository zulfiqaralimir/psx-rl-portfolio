"""Walk-forward: 2 extra windows (w1 test 2018-19, w2 test 2020-21; windows defined in psx_rl/data.py), PPO/A2C/DDPG x10 seeds,
cost 0.1%, Stage B protocol/hyperparameters. 2 parallel workers; skips finished runs."""
import subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = r"D:\psx_rl_portfolio\results\walkforward"
STEPS = 100_000
jobs = []
for w in ("w1", "w2"):
    os.makedirs(rf"{ROOT}\{w}", exist_ok=True)
    jobs += [(w, a, s) for a in ("DDPG", "PPO", "A2C") for s in range(10) if not os.path.exists(rf"{ROOT}\{w}\{a}_{s}.json")]
jobs.sort(key=lambda j: ("DDPG", "PPO", "A2C").index(j[1]))
print(len(jobs), "jobs", flush=True)

def run(j):
    w, a, s = j
    env = dict(os.environ, PSX_OUT=rf"{ROOT}\{w}", PSX_WINDOW=w, PSX_COST="0.001")
    with open(rf"{ROOT}\{w}\log_{a}_{s}.txt", "w") as f:
        r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\train_stage_b.py", a, str(s), str(STEPS)], stdout=f, stderr=subprocess.STDOUT, env=env)
    print(w, a, s, "exit", r.returncode, flush=True)

with ThreadPoolExecutor(2) as ex:
    list(ex.map(run, jobs))
print("ALL DONE", flush=True)
