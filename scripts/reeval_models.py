"""Re-evaluate the saved, validation-selected checkpoints on the TEST split of the (patched) data, without retraining.
Valid because the patch only changes rows from 2024-09 on (inside the test split): training (2013-2019) and validation (2020-2021) data are unchanged,
so the checkpoints would be selected and trained identically. Updates test_* fields in each run's JSON and its test_series CSV; the old Sharpe/return
are kept as prepatch_test_*. Usage: python scripts/reeval_models.py"""
import sys, os, json, glob
sys.path.insert(0, r"D:\psx_rl_portfolio")
import torch
from stable_baselines3 import PPO, A2C, DDPG
from psx_rl.data import load_panel, load_policy_rate, split_slice
from psx_rl.gym_env import PSXGymEnv, rollout
from psx_rl.metrics import metrics

torch.set_num_threads(1)
ROOT = r"D:\psx_rl_portfolio\results"
LEVELS = [(ROOT + r"\stageB", 0.001), (ROOT + r"\stageC\c0", 0.0), (ROOT + r"\stageC\c0018", 0.0018), (ROOT + r"\stageC\c0025", 0.0025), (ROOT + r"\stageC\c005", 0.005)]
ALG = {"PPO": PPO, "A2C": A2C, "DDPG": DDPG}
P, listed, _ = load_panel(); policy = load_policy_rate()
test = split_slice(P.index, "test")
n = 0
for out, cost in LEVELS:
    for f in sorted(glob.glob(out + r"\*_[0-9].json")):
        j = json.load(open(f)); a, s = j["algo"], j["seed"]
        model = ALG[a].load(rf"{out}\models\{a}_{s}", device="cpu")
        res = rollout(model, PSXGymEnv(P, listed, test, cost=cost))
        m = metrics(res, policy)
        if "prepatch_test_sharpe" not in j:
            j["prepatch_test_sharpe"], j["prepatch_test_annual_return"] = j["test_sharpe"], j["test_annual_return"]
        j.update({f"test_{k}": float(v) for k, v in m.items()})
        json.dump(j, open(f, "w")); res.to_csv(rf"{out}\test_series\{a}_{s}.csv"); n += 1
    print(out, "re-evaluated", n, flush=True)
print("done", n)
