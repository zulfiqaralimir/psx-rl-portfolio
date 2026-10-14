"""Panel loading: 29 tickers, adj_close_fixed, calendar = days with >= 20 tickers having a row."""
import glob, os
import pandas as pd

CLEAN = r"D:\psx_rl_portfolio\data\clean"
SPLITS = {"train": ("2013-01-01", "2019-12-31"), "val": ("2020-01-01", "2021-12-31"), "test": ("2022-01-01", "2100-01-01")}
# Walk-forward windows (expanding train, 2y validation, 2y test), selected with env PSX_WINDOW; default = main split above.
WINDOWS = {"w1": {"train": ("2013-01-01", "2015-12-31"), "val": ("2016-01-01", "2017-12-31"), "test": ("2018-01-01", "2019-12-31")},
           "w2": {"train": ("2013-01-01", "2017-12-31"), "val": ("2018-01-01", "2019-12-31"), "test": ("2020-01-01", "2021-12-31")}}
SPLITS = WINDOWS.get(os.environ.get("PSX_WINDOW"), SPLITS)


def load_panel(min_tickers: int = 20):
    """Returns P (adjusted price, ffilled, NaN before a ticker's first row), listed (P notna),
    traded (ticker had a row that day). Unlisted tickers are masked: no trading, weight 0."""
    cols = {}
    for f in sorted(glob.glob(CLEAN + r"\*.csv")):
        c = pd.read_csv(f, parse_dates=["date"]).set_index("date")
        cols[os.path.basename(f)[:-4]] = c.adj_close_fixed
    A = pd.DataFrame(cols).sort_index()
    cal = A.index[A.notna().sum(axis=1) >= min_tickers]
    P = A.ffill().loc[cal]
    if os.environ.get("PSX_ZERO_FLAGGED") == "1":  # sensitivity test: zero the return of each flagged test-period (ticker, day); later returns unchanged
        sb = pd.read_csv(r"D:\psx_rl_portfolio\data\small_breaks.csv", parse_dates=["date"])
        for t, d in sb[sb.flag.notna() & (sb.date >= "2022-01-03")][["ticker", "date"]].itertuples(index=False):
            i = P.index.get_loc(d)
            P.loc[P.index[i]:, t] *= P[t].iloc[i - 1] / P[t].iloc[i]
    traded = A.loc[cal].notna()
    if os.environ.get("PSX_UNIVERSE") == "core16":  # robustness: always-KSE-30 members; the calendar above still uses all 29 tickers
        keep = open(r"D:\psx_rl_portfolio\data\universe_core16.txt").read().split()
        P, traded = P[keep], traded[keep]
    return P, P.notna(), traded


def load_policy_rate() -> pd.Series:
    """SBP policy rate (decimal), step function indexed by effective date."""
    r = pd.read_csv(r"D:\psx_rl_portfolio\data\macro\sbp_policy_rate.csv", parse_dates=["effective_date"])
    return r.set_index("effective_date").policy_rate_pct.sort_index() / 100.0


def split_slice(index: pd.DatetimeIndex, name: str):
    a, b = SPLITS[name]
    return index[(index >= a) & (index <= b)]


def load_kse100_close() -> pd.Series:
    """KSE-100 index close (price index, NO dividends). See scripts/clean_kse100.py."""
    f = r"D:\psx_rl_portfolio\data\benchmark_kse100.csv"
    return pd.read_csv(f, parse_dates=["date"]).set_index("date").close
