"""Exposure / cash share and trade-size-cap (hmax) analysis on the retrained 0.18% models (results/retrain_patched/c0018), test split, no retraining.
Rolls each saved model out with hmax = 100 (training value), 200 and effectively unlimited (1e9: sells limited by holdings, buys by cash).
Writes results/exposure_cap/<cap100|cap200|capinf>/ (run JSONs + test_series, for analyze_stage_b.py) and results/exposure_cap/exposure_runs.csv.
Usage: python scripts/exposure_and_cap.py"""
import sys, os, json, glob
sys.path.insert(0, r"D:\psx_rl_portfolio")
import numpy as np, pandas as pd, torch
from stable_baselines3 import PPO, A2C, DDPG
from psx_rl.data import load_panel, load_policy_rate, split_slice
from psx_rl.gym_env import PSXGymEnv
from psx_rl.metrics import metrics

torch.set_num_threads(1)
SRC = r"D:\psx_rl_portfolio\results\retrain_patched\c0018"; OUT = r"D:\psx_rl_portfolio\results\exposure_cap"
CAPS = {"cap100": 100.0, "cap200": 200.0, "capinf": 1e9}
ALG = {"PPO": PPO, "A2C": A2C, "DDPG": DDPG}
P, listed, _ = load_panel(); policy = load_policy_rate(); test = split_slice(P.index, "test")
rows = []
for tag, hmax in CAPS.items():
    os.makedirs(rf"{OUT}\{tag}\test_series", exist_ok=True)
    for f in sorted(glob.glob(SRC + r"\*_[0-9].json")):
        j = json.load(open(f)); a, s = j["algo"], j["seed"]
        model = ALG[a].load(rf"{SRC}\models\{a}_{s}", device="cpu")
        env = PSXGymEnv(P, listed, test, cost=0.0018, hmax=hmax)
        obs, _ = env.reset(); done = False
        recs = [{"date": env.core.log["date"][0], "total_asset": env.core.initial, "stock_value": 0.0, "traded": 0.0}]
        sat = nz = big = n_ok = 0; sat_day = 0; days = 0
        while not done:
            act, _ = model.predict(obs, deterministic=True)
            ok = env.core.listed_mask()
            x = np.abs(np.clip(act, -1, 1))[ok]
            sat += int((x >= 0.999).sum()); big += int((x >= 0.5).sum()); n_ok += int(ok.sum()); sat_day += int((x >= 0.999).any()); days += 1
            obs, _, done, _, info = env.step(act)
            recs.append({k: info[k] for k in ("date", "total_asset", "stock_value", "traded")})
        res = pd.DataFrame(recs).set_index("date")
        j.update({f"test_{k}": float(v) for k, v in metrics(res, policy).items()})
        json.dump(j, open(rf"{OUT}\{tag}\{a}_{s}.json", "w")); res.to_csv(rf"{OUT}\{tag}\test_series\{a}_{s}.csv")
        cash = 1 - (res.stock_value / res.total_asset).iloc[1:]   # drop the all-cash day 0
        rows.append({"cap": tag, "hmax": hmax, "algo": a, "seed": s, "exposure": 1 - cash.mean(), "cash_share": cash.mean(), "days_cash_gt50": (cash > 0.5).mean(),
                     "share_actions_saturated": sat / n_ok, "share_actions_ge_half": big / n_ok, "share_days_any_saturated": sat_day / days, "sharpe": j["test_sharpe"]})
    print(tag, "done", flush=True)
pd.DataFrame(rows).to_csv(OUT + r"\exposure_runs.csv", index=False)
px = P.loc[test]; ok = listed.loc[test]
print("median adjusted price over listed test stock-days:", float(np.nanmedian(px.where(ok).to_numpy())))
