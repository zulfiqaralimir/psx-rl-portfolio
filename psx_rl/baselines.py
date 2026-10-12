"""Baselines run through PortfolioEnv (same costs and accounting as the RL agents will use)."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf
from .env import PortfolioEnv

MAX_W = 0.20  # per-name cap for the mean-variance baseline


def _eq(mask):
    return mask / mask.sum()


def _month_changed(prev, cur):
    return (prev.year, prev.month) != (cur.year, cur.month)


def run_weights(env: PortfolioEnv, weight_fn, monthly: bool):
    """weight_fn(env) -> target weights; applied on day 0 and (if monthly) on each new month, else only day 0."""
    env.reset()
    prev = None
    done = False
    while not done:
        d = env.date()
        reb = prev is None or (monthly and _month_changed(prev, d))
        _, _, done, _ = env.step(weights=weight_fn(env) if reb else None)
        prev = d
    return env.result()


def buy_and_hold(env):
    return run_weights(env, lambda e: _eq(e.listed_mask().astype(float)), monthly=False)


def equal_weight_monthly(env):
    return run_weights(env, lambda e: _eq(e.listed_mask().astype(float)), monthly=True)


def fit_mean_variance(P: pd.DataFrame, train_dates, rf: float, ann: float = 245.0):
    """Max-Sharpe, long-only, cap MAX_W, on TRAIN returns only (Ledoit-Wolf covariance). Fixed afterwards."""
    R = P.loc[train_dates].pct_change().iloc[1:]
    R = R.loc[:, R.notna().mean() > 0.5].fillna(0.0)
    mu = R.mean().to_numpy() * ann
    cov = LedoitWolf().fit(R.to_numpy()).covariance_ * ann
    n = len(mu)

    def neg_sharpe(w):
        return -(w @ mu - rf) / np.sqrt(w @ cov @ w)

    res = minimize(neg_sharpe, np.full(n, 1 / n), method="SLSQP", bounds=[(0, MAX_W)] * n,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}])
    assert res.success, res.message
    return pd.Series(res.x, index=R.columns).reindex(P.columns).fillna(0.0)


def mean_variance_monthly(env, w_fit: pd.Series):
    def fn(e):
        w = w_fit.to_numpy() * e.listed_mask()
        return w / w.sum()
    return run_weights(env, fn, monthly=True)
