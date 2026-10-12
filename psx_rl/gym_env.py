"""Gymnasium wrapper + shared training/evaluation helpers for Stage B."""
import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces
from .env import PortfolioEnv


class PSXGymEnv(gym.Env):
    """Wraps PortfolioEnv. Action in [-1,1]^29 -> share trades of action*hmax. Reward = 100 * log return of total asset.
    Observation = [cash share, weights, 1d return x20, 20d return x5, listed mask], clipped to [-5, 5]."""

    def __init__(self, P, listed, dates, cost=0.001, hmax=100.0):
        super().__init__()
        self.core = PortfolioEnv(P, listed, dates, cost=cost, hmax=hmax)
        n = self.core.n
        self.action_space = spaces.Box(-1.0, 1.0, (n,), np.float32)
        self.observation_space = spaces.Box(-5.0, 5.0, (1 + 4 * n,), np.float32)
        self.n = n

    def _scale(self, o):
        n = self.n
        o = o.copy()
        o[1 + n:1 + 2 * n] *= 20
        o[1 + 2 * n:1 + 3 * n] *= 5
        return np.clip(o, -5, 5).astype(np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        return self._scale(self.core.reset()), {}

    def step(self, action):
        prev = self.core.total_asset()
        o, _, done, info = self.core.step(action=action)
        info = dict(info, stock_value=self.core.log["stock_value"][-1])
        r = 100.0 * float(np.log(info["total_asset"] / prev))
        return self._scale(o), r, bool(done), False, info


def rollout(model, env: PSXGymEnv) -> pd.DataFrame:
    """Deterministic episode on a bare env (no VecEnv auto-reset). total_asset etc. are accumulated from each step's info dict."""
    obs, _ = env.reset()
    rows = [{"date": env.core.log["date"][0], "total_asset": env.core.initial, "stock_value": 0.0, "traded": 0.0}]
    done = False
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        obs, _, done, _, info = env.step(a)
        rows.append({k: info[k] for k in ("date", "total_asset", "stock_value", "traded")})
    return pd.DataFrame(rows).set_index("date")
