"""One metric formula for every strategy.
ann = observed trading days per year in the sample. Sharpe = mean(r - rf)/std(r) * sqrt(ann), where r is the daily
simple return of total_asset and rf = SBP policy rate in effect at the start of each return day / ann.
Cash earns 0 in the simulator (so cash drag shows up in Sharpe)."""
import numpy as np
import pandas as pd


def metrics(res: pd.DataFrame, policy: pd.Series, turnover: bool = True) -> dict:
    a = res.total_asset
    r = a.pct_change().dropna()
    years = (a.index[-1] - a.index[0]).days / 365.25
    ann = len(r) / years
    rf = policy.reindex(a.index[:-1].union(policy.index)).ffill().reindex(a.index[:-1]).to_numpy() / ann
    ex = r.to_numpy() - rf
    dd = (a / a.cummax() - 1).min()
    expo = (res.stock_value / a).iloc[1:].mean() if "stock_value" in res else 1.0
    out = {
        "annual_return": (a.iloc[-1] / a.iloc[0]) ** (1 / years) - 1,
        "volatility": r.std() * np.sqrt(ann),
        "sharpe": ex.mean() / r.std() * np.sqrt(ann),
        "max_drawdown": dd,
        "exposure": expo,
        "cash_share": 1 - expo,
        "turnover": (res.traded.sum() / 2 / a.mean() / years) if turnover and "traded" in res else np.nan,
        "n_days": len(r), "years": years, "ann_days": ann,
    }
    return out
