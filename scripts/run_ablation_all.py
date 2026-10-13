"""Training-length ablation (reviewer 'under-trained'): PPO and A2C, 300,000 steps (steps300k) vs a 100,000-step control (steps100k_control) on the
SAME patched data, 0.1% cost, same splits, same hyperparameters; checkpoint chosen on validation Sharpe every 10k steps; test evaluated once per run
(train_stage_b.py records best_step and the validation history in each run's JSON). Seeds are run in two groups, 0-4 then 5-9; the second group is skipped
if the projected total wall time (2 x the first group's) exceeds 2.5 h. 2 parallel workers. Skips finished runs."""
import subprocess, os, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = r"D:\psx_rl_portfolio\results\ablation_steps300k"
CONFIGS = [("steps300k", 300_000), ("steps100k_control", 100_000)]
GROUPS = [range(0, 5), range(5, 10)]
LIMIT_S = 2.5 * 3600
for c, _ in CONFIGS:
    os.makedirs(rf"{ROOT}\{c}", exist_ok=True)


def run(j):
    cfg, steps, algo, seed = j
    env = dict(os.environ, PSX_OUT=rf"{ROOT}\{cfg}", PSX_COST="0.001")
    with open(rf"{ROOT}\{cfg}\log_{algo}_{seed}.txt", "w") as f:
        r = subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\train_stage_b.py", algo, str(seed), str(steps)], stdout=f, stderr=subprocess.STDOUT, env=env)
    print(cfg, algo, seed, "exit", r.returncode, flush=True)


t_start = time.time()
for gi, seeds in enumerate(GROUPS):
    jobs = [(c, s, a, sd) for c, s in CONFIGS for a in ("PPO", "A2C") for sd in seeds if not os.path.exists(rf"{ROOT}\{c}\{a}_{sd}.json")]
    jobs.sort(key=lambda j: -j[1])   # long (300k) runs first
    print(f"group {gi} seeds {seeds[0]}-{seeds[-1]}: {len(jobs)} jobs", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(run, jobs))
    t1 = time.time() - t0
    print(f"group {gi} took {t1 / 60:.0f} min", flush=True)
    if gi == 0 and 2 * (time.time() - t_start) > LIMIT_S:
        print(f"projected total {2 * (time.time() - t_start) / 3600:.1f} h exceeds 2.5 h: skipping seeds 5-9", flush=True)
        break
print("ALL DONE", flush=True)
