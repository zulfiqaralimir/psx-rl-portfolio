"""Sensitivity: 0.18% cost, 10 seeds x 3 algos, flagged test-period days (data/small_breaks.csv, flag set, date >= 2022-01-03) as is vs return set to zero.
Copies results/retrain_patched/c0018 to results/sensitivity_flagged/<as_is|zeroed>, re-evaluates the saved checkpoints on the test split (no retraining) with
PSX_ZERO_FLAGGED=0/1, then run analyze_stage_b.py with PSX_OUT/PSX_COST/PSX_ZERO_FLAGGED set. Usage: python scripts/sensitivity_flagged.py <as_is|zeroed>"""
import sys, os, json, glob, shutil
mode = sys.argv[1]
os.environ["PSX_ZERO_FLAGGED"] = "1" if mode == "zeroed" else "0"
sys.path.insert(0, r"D:\psx_rl_portfolio")
import torch
from stable_baselines3 import PPO, A2C, DDPG
from psx_rl.data import load_panel, load_policy_rate, split_slice
from psx_rl.gym_env import PSXGymEnv, rollout
from psx_rl.metrics import metrics

torch.set_num_threads(1)
SRC = r"D:\psx_rl_portfolio\results\retrain_patched\c0018"; DST = rf"D:\psx_rl_portfolio\results\sensitivity_flagged\{mode}"
os.makedirs(DST + r"\test_series", exist_ok=True)
shutil.copytree(SRC + r"\models", DST + r"\models", dirs_exist_ok=True)
ALG = {"PPO": PPO, "A2C": A2C, "DDPG": DDPG}
P, listed, _ = load_panel(); policy = load_policy_rate(); test = split_slice(P.index, "test")
for f in sorted(glob.glob(SRC + r"\*_[0-9].json")):
    j = json.load(open(f)); a, s = j["algo"], j["seed"]
    res = rollout(ALG[a].load(rf"{DST}\models\{a}_{s}", device="cpu"), PSXGymEnv(P, listed, test, cost=0.0018))
    j.update({f"test_{k}": float(v) for k, v in metrics(res, policy).items()})
    json.dump(j, open(rf"{DST}\{a}_{s}.json", "w")); res.to_csv(rf"{DST}\test_series\{a}_{s}.csv")
print(mode, "done", flush=True)
