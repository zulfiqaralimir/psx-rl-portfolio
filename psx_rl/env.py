"""Portfolio environment. Trades execute at the close of day t at the adjusted price; value is marked at t+1.
Unlisted tickers (no price yet) are masked: they cannot be traded and hold 0. Dividends are reinvested
implicitly through adjusted prices. Gym-style API without the gym dependency (a wrapper comes in Stage B).
Every step's info dict carries total_asset, so results never depend on VecEnv auto-reset."""
import numpy as np
import pandas as pd


class PortfolioEnv:
    def __init__(self, P: pd.DataFrame, listed: pd.DataFrame, dates: pd.DatetimeIndex,
                 cost: float = 0.001, hmax: float | None = None, initial: float = 1e6, lookback: int = 20):
        self.P, self.listed, self.cost, self.hmax, self.initial, self.lookback = P, listed, cost, hmax, initial, lookback
        self.tickers = list(P.columns)
        self.n = len(self.tickers)
        self.idx = P.index.get_indexer(dates)
        assert (self.idx >= 0).all() and len(self.idx) > 1
        self._px = P.to_numpy()
        self._ok = listed.to_numpy()
        self.reset()

    # ---- state ----
    def reset(self):
        self.k = 0
        self.cash = self.initial
        self.h = np.zeros(self.n)
        self.log = {"date": [self.P.index[self.idx[0]]], "total_asset": [self.initial], "stock_value": [0.0], "traded": [0.0]}
        return self.obs()

    def prices(self, k=None):
        return np.nan_to_num(self._px[self.idx[self.k if k is None else k]])

    def total_asset(self):
        return self.cash + float(self.h @ self.prices())

    def obs(self):
        i = self.idx[self.k]
        px = self.prices()
        tot = self.cash + float(self.h @ px)
        w = self.h * px / tot
        r1 = np.nan_to_num(self._px[i] / self._px[max(i - 1, 0)] - 1)
        rl = np.nan_to_num(self._px[i] / self._px[max(i - self.lookback, 0)] - 1)
        return np.concatenate([[self.cash / tot], w, r1, rl, self._ok[i].astype(float)])

    # ---- trading ----
    def _trade(self, dh):
        """dh: share deltas (+buy/-sell). Sells first, buys limited by cash. Returns traded value."""
        px, ok = self.prices(), self._ok[self.idx[self.k]]
        dh = np.where(ok, dh, 0.0)
        dh = np.maximum(dh, -self.h)
        sell = -np.minimum(dh, 0) * px
        self.cash += sell.sum() * (1 - self.cost)
        buy = np.maximum(dh, 0) * px
        need = buy.sum() * (1 + self.cost)
        if need > self.cash:
            buy *= self.cash / need
            dh = np.where(dh > 0, buy / np.maximum(px, 1e-12), dh)
        self.cash -= buy.sum() * (1 + self.cost)
        self.h = self.h + dh
        return float(sell.sum() + buy.sum())

    def rebalance_to(self, w):
        """Trade to target value weights (cash = remainder). Baselines use this."""
        px, ok = self.prices(), self._ok[self.idx[self.k]]
        w = np.where(ok, w, 0.0)
        tot = self.cash + float(self.h @ px)
        target = w * tot / np.maximum(px, 1e-12)
        return self._trade(target - self.h)

    def step(self, action=None, weights=None):
        """action in [-1,1]^n scaled by hmax shares, or target weights (baselines). None = hold."""
        traded = 0.0
        if weights is not None:
            traded = self.rebalance_to(np.asarray(weights, float))
        elif action is not None:
            assert self.hmax, "hmax required for share actions"
            traded = self._trade(np.clip(np.asarray(action, float), -1, 1) * self.hmax)
        self.k += 1
        tot = self.total_asset()
        info = {"total_asset": tot, "date": self.P.index[self.idx[self.k]], "traded": traded}
        self.log["date"].append(info["date"])
        self.log["total_asset"].append(tot)
        self.log["stock_value"].append(float(self.h @ self.prices()))
        self.log["traded"].append(traded)
        done = self.k >= len(self.idx) - 1
        reward = np.log(tot / self.log["total_asset"][-2])
        return self.obs(), reward, done, info

    def result(self):
        return pd.DataFrame(self.log).set_index("date")

    def date(self):
        return self.P.index[self.idx[self.k]]

    def listed_mask(self):
        return self._ok[self.idx[self.k]]
