"""Train one (algo, seed). Checkpoint chosen by VALIDATION Sharpe only; test is evaluated once, after training,
for the selected checkpoint. Usage: python scripts/train_stage_b.py ALGO SEED STEPS"""
import sys, os, json, time
sys.path.insert(0, r"D:\psx_rl_portfolio")
import numpy as np, pandas as pd, torch
from stable_baselines3 import PPO, A2C, DDPG
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.noise import NormalActionNoise
from stable_baselines3.common.vec_env import DummyVecEnv
from psx_rl.data import load_panel, load_policy_rate, split_slice
from psx_rl.gym_env import PSXGymEnv, rollout
from psx_rl.metrics import metrics

OUT = r"D:\psx_rl_portfolio\results\stageB"
EVAL_EVERY = 10_000


def make_model(algo, venv, seed):
    kw = dict(policy="MlpPolicy", env=venv, seed=seed, verbose=0, device="cpu")
    n = venv.action_space.shape[0]
    if algo == "PPO":
        return PPO(n_steps=1024, batch_size=256, learning_rate=3e-4, gamma=0.99, **kw)
    if algo == "A2C":
        return A2C(n_steps=32, learning_rate=7e-4, gamma=0.99, **kw)
    if algo == "DDPG":
        return DDPG(learning_rate=1e-3, buffer_size=100_000, learning_starts=5_000, batch_size=256, train_freq=(4, "step"),
                    gradient_steps=2, gamma=0.99, action_noise=NormalActionNoise(np.zeros(n), 0.1 * np.ones(n)), **kw)
    raise ValueError(algo)


class ValCheckpoint(BaseCallback):
    def __init__(self, val_env, policy, path):
        super().__init__()
        self.val_env, self.policy, self.path = val_env, policy, path
        self.best, self.best_step, self.history = -np.inf, 0, []

    def _on_step(self):
        if self.num_timesteps % EVAL_EVERY == 0:
            s = metrics(rollout(self.model, self.val_env), self.policy)["sharpe"]
            self.history.append((self.num_timesteps, float(s)))
            if s > self.best:
                self.best, self.best_step = float(s), self.num_timesteps
                self.model.save(self.path)
        return True


def main(algo, seed, steps):
    torch.set_num_threads(1)
    os.makedirs(OUT + r"\models", exist_ok=True); os.makedirs(OUT + r"\test_series", exist_ok=True)
    P, listed, _ = load_panel(); policy = load_policy_rate()
    mk = lambda split: PSXGymEnv(P, listed, split_slice(P.index, split))
    venv = DummyVecEnv([lambda: mk("train")])
    path = rf"{OUT}\models\{algo}_{seed}"
    model = make_model(algo, venv, seed)
    cb = ValCheckpoint(mk("val"), policy, path)
    t0 = time.time()
    model.learn(total_timesteps=steps, callback=cb)
    train_secs = time.time() - t0
    best = {"PPO": PPO, "A2C": A2C, "DDPG": DDPG}[algo].load(path, device="cpu")
    res = rollout(best, mk("test"))  # first and only test look, for the val-selected checkpoint
    res.to_csv(rf"{OUT}\test_series\{algo}_{seed}.csv")
    m = metrics(res, policy)
    out = {"algo": algo, "seed": seed, "steps": steps, "train_secs": train_secs, "best_val_sharpe": cb.best,
           "best_step": cb.best_step, "val_history": cb.history, **{f"test_{k}": float(v) for k, v in m.items()}}
    json.dump(out, open(rf"{OUT}\{algo}_{seed}.json", "w"))
    print(algo, seed, f"{train_secs:.0f}s", "val", round(cb.best, 2), "@", cb.best_step, "test sharpe", round(m["sharpe"], 2), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
