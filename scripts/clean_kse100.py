"""Clean + validate data/raw/KSE100.csv (Investing.com export) -> data/benchmark_kse100.csv.
Kept OUT of data/clean/ on purpose: psx_rl.data.load_panel globs that folder as stock tickers.
Only reformatting is done (dates, thousands separators, volume suffix, sort); no value is altered or dropped."""
import pandas as pd, numpy as np

d = pd.read_csv(r"D:\psx_rl_portfolio\data\raw\KSE100.csv", encoding="utf-8-sig", thousands=",")
d["date"] = pd.to_datetime(d.Date, format="%m/%d/%Y")
vol = d["Vol."].astype(str).str.strip()
mult = vol.str[-1].map({"K": 1e3, "M": 1e6, "B": 1e9})
d["volume"] = pd.to_numeric(vol.str[:-1], errors="coerce") * mult
d = d.rename(columns={"Price": "close", "Open": "open", "High": "high", "Low": "low"})
d = d.sort_values("date").set_index("date")[["close", "open", "high", "low", "volume"]]
d["ret"] = d.close.pct_change()

# ---- validation ----
assert d.index.is_unique and d.index.is_monotonic_increasing
assert d[["close", "open", "high", "low"]].notna().all().all() and (d[["close", "open", "high", "low"]] > 0).all().all()
assert (d.index.dayofweek < 5).all()
print(f"{len(d)} rows {d.index[0].date()}..{d.index[-1].date()}")
chg = pd.read_csv(r"D:\psx_rl_portfolio\data\raw\KSE100.csv", encoding="utf-8-sig")
chg.index = pd.to_datetime(chg.Date, format="%m/%d/%Y"); chg = chg["Change %"].str.rstrip("%").astype(float).sort_index()
print("max |ret - reported Change%|:", round((d.ret * 100 - chg).abs().max(), 3), "pct points")
print("rows with |ret|>6%:", (d.ret.abs() > 0.06).sum(), " max |ret|", round(d.ret.abs().max(), 4))
bad = d[(d.close > d.high) | (d.close < d.low)]
dev = np.maximum(bad.close - bad.high, bad.low - bad.close) / bad.close
print(f"close outside [low, high]: {len(bad)} rows, max {dev.max():.4%} of close (feed mismatch, kept)")
print("high<low rows:", (d.high < d.low).sum(), " volume missing:", d.volume.isna().sum(), "(pre-2013-11 volume is blank in the source)")
g = d.index.to_series().diff().dt.days
print("largest calendar gap:", int(g.max()), "days on", g.idxmax().date())
d.to_csv(r"D:\psx_rl_portfolio\data\benchmark_kse100.csv")
