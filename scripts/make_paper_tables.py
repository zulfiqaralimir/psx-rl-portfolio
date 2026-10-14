"""docs/PAPER_TABLES.md: paper tables as markdown pipe tables (patched data; percentages 1 decimal, Sharpe 2 decimals).
Agents: results/stageC/stageC_summary.csv (0, 0.1, 0.18% = agents retrained on patched data; 0.25, 0.5% = saved checkpoints re-scored).
Baselines are recomputed at each cost (same code as analyze_stage_b.py); their Sharpe CI is a circular block bootstrap of test days (block 20, 4,000 draws).
Usage: python scripts/make_paper_tables.py"""
import sys
sys.path.insert(0, r"D:\psx_rl_portfolio")
import numpy as np, pandas as pd
from psx_rl.data import load_panel, load_policy_rate, split_slice, load_kse100_close
from psx_rl.env import PortfolioEnv
from psx_rl.metrics import metrics
from psx_rl import baselines as B

R = r"D:\psx_rl_portfolio\results"
S = pd.read_csv(R + r"\stageC\stageC_summary.csv"); G = pd.read_csv(R + r"\stageC\stageC_significance.csv")
WF = pd.read_csv(R + r"\tables\table4_walkforward_sharpe.csv"); WG = pd.read_csv(R + r"\walkforward\walkforward_significance.csv")
P, listed, _ = load_panel(); policy = load_policy_rate()
test = split_slice(P.index, "test"); train = split_slice(P.index, "train")
mv = B.fit_mean_variance(P, train, policy.reindex(train.union(policy.index)).ffill().reindex(train).mean())
NAMES = {"buy_and_hold": "Buy-and-hold", "equal_weight_monthly": "Equal-weight monthly", "mean_variance_monthly": "Mean-variance monthly", "kse100_benchmark": "KSE-100 (price index, excl. dividends)"}
ALGS = ["A2C", "PPO", "DDPG"]
pc = lambda x: f"{100 * x:.1f}%"
sh = lambda x: f"{x:.2f}"
RETRAINED = {0.0, 0.001, 0.0018}


def boot_ci(res, n=4000, block=20, seed=7):
    r = res.total_asset.pct_change().dropna()
    prev = res.index[:-1]
    ann = len(r) / ((res.index[-1] - res.index[0]).days / 365.25)
    rf = policy.reindex(prev.union(policy.index)).ffill().reindex(prev).to_numpy() / ann
    x = r.to_numpy(); T = len(x); nb = int(np.ceil(T / block)); rng = np.random.default_rng(seed)
    st = rng.integers(0, T, (n, nb)); ix = ((st[:, :, None] + np.arange(block)) % T).reshape(n, -1)[:, :T]
    xs, rs = x[ix], rf[ix]
    s = (xs - rs).mean(axis=1) / xs.std(axis=1, ddof=1) * np.sqrt(ann)
    return np.percentile(s, [2.5, 97.5])


_cache = {}
def baselines_at(cost):
    if cost in _cache: return _cache[cost]
    mk = lambda: PortfolioEnv(P, listed, test, cost=cost)
    res = {"buy_and_hold": B.buy_and_hold(mk()), "equal_weight_monthly": B.equal_weight_monthly(mk()), "mean_variance_monthly": B.mean_variance_monthly(mk(), mv)}
    k = load_kse100_close().reindex(P.index).ffill().loc[test]
    res["kse100_benchmark"] = pd.DataFrame({"total_asset": k / k.iloc[0]})
    out = {}
    for n, r in res.items():
        m = metrics(r, policy, turnover=n != "kse100_benchmark"); lo, hi = boot_ci(r)
        out[n] = dict(m, lo=lo, hi=hi)
    _cache[cost] = out
    return out


def main_table(cost):
    s = S[S.cost_per_side == cost].set_index("algo"); b = baselines_at(cost)
    rows = ["| Strategy | Annual return | Volatility | Sharpe [95% CI] | Max drawdown | Turnover/yr [95% CI] |", "|---|---|---|---|---|---|"]
    for n, label in NAMES.items():
        m = b[n]
        rows.append(f"| {label} | {pc(m['annual_return'])} | {pc(m['volatility'])} | {sh(m['sharpe'])} [{sh(m['lo'])}, {sh(m['hi'])}] | {pc(m['max_drawdown'])} | "
                    + ("n/a |" if n == "kse100_benchmark" else f"{m['turnover']:.2f} (deterministic) |"))
    for a in ALGS:
        x = s.loc[a]
        rows.append(f"| {a} (10-seed mean) | {pc(x.annual_return_mean)} | {pc(x.volatility_mean)} | {sh(x.sharpe_mean)} [{sh(x.sharpe_ci_lo)}, {sh(x.sharpe_ci_hi)}] | "
                    f"{pc(x.max_drawdown_mean)} | {x.turnover_mean:.2f} [{x.turnover_ci_lo:.2f}, {x.turnover_ci_hi:.2f}] |")
    return "\n".join(rows)


def sig_line(g, what):
    n = len(g); k = int((g.p_two_sided < 0.05).sum()); i = g.p_two_sided.idxmin(); r = g.loc[i]
    return f"*{what}: {n} comparisons (algorithm vs baseline, Sharpe difference, circular block bootstrap), {k} with p < 0.05, smallest p = {r.p_two_sided:.3f} ({r.algo} vs {r.baseline.replace('_', ' ')}).*"


doc = ["# Paper tables (patched data)", "",
       "All results use the patched price data (`data/patch/`, applied 2026-10-13). Test period 2022-01-03 to 2026-10-09 unless stated. Sharpe is over the SBP policy rate. "
       "Turnover = one-way traded value / mean asset value / year. Agents are 10-seed means; Sharpe CI for agents = 95% t-interval over seeds, "
       "for baselines = circular block bootstrap of test days (block 20, 4,000 draws); turnover CI for agents = percentile bootstrap over seeds (baselines are deterministic). "
       "Regenerate with `python scripts/make_paper_tables.py`.", ""]
for cost, title in [(0.0018, "0.18% per side (realistic PSX/CDC/SECP fees)"), (0.001, "0.1% per side")]:
    doc += [f"## Table 1{'a' if cost == 0.0018 else 'b'}: test results at {title}", "", "Agents are retrained on the patched data at this cost.", "", main_table(cost), "",
            sig_line(G[G.cost_per_side == cost], f"Significance at {cost * 100:g}% cost"), ""]

# cost sensitivity
doc += ["## Table 2: test Sharpe by cost per side (agents: mean [95% CI over 10 seeds]; baselines: Sharpe [95% block-bootstrap CI])", "",
        "| Cost/side | Agents | " + " | ".join(ALGS) + " | " + " | ".join(NAMES[k].split(" (")[0] for k in NAMES) + " |", "|---|---|" + "---|" * (len(ALGS) + len(NAMES))]
for c in sorted(S.cost_per_side.unique()):
    s = S[S.cost_per_side == c].set_index("algo"); b = baselines_at(c)
    cells = [f"{sh(s.loc[a].sharpe_mean)} [{sh(s.loc[a].sharpe_ci_lo)}, {sh(s.loc[a].sharpe_ci_hi)}]" for a in ALGS]
    cells += [f"{sh(b[k]['sharpe'])} [{sh(b[k]['lo'])}, {sh(b[k]['hi'])}]" for k in NAMES]
    doc.append(f"| {c * 100:g}% | {'retrained' if c in RETRAINED else 're-scored'} | " + " | ".join(cells) + " |")
doc += ["", "*Retrained* = agents trained from scratch on the patched data at that cost (seeds 0-9). *Re-scored* = checkpoints trained before the patch, evaluated on the patched test split "
        "(valid because the patch only changes rows from 2025-04, inside the test split; training and validation data are unchanged). Baselines are recomputed at each cost.", "",
        sig_line(G, "Significance across all five cost levels"), ""]

# walk-forward
doc += ["## Table 3: walk-forward test Sharpe (0.1% cost; agents: mean [95% CI over 10 seeds]; baselines: point Sharpe)", "",
        "| Window | Test period | " + " | ".join(ALGS) + " | Buy-and-hold | Equal-weight monthly | Mean-variance monthly | KSE-100 (price index) |", "|---|---|" + "---|" * 7]
for _, r in WF.iterrows():
    doc.append(f"| {r.window} | {r.test_period} | " + " | ".join(r[a] for a in ALGS) + " | " + " | ".join(f"{r[k]:.2f}" for k in NAMES) + " |")
doc += ["", "Training/validation/test windows: w1 train 2013-2015, validation 2016-2017, test 2018-2019; w2 train 2013-2017, validation 2018-2019, test 2020-2021; main train 2013-2019, validation 2020-2021, test 2022-2026.",
        "**w1 and w2 were neither retrained nor re-scored after the patch:** they were trained once, before the patch, and the patch changes no row before 2025-04, so their data are identical to the patched data and the results are unaffected. "
        "The main row (2022-2026) is the retrained 0.1% agents.", "",
        sig_line(WG, "Significance across the three windows") + " All with p < 0.05 have the agent below the baseline.", ""]
open(r"D:\psx_rl_portfolio\docs\PAPER_TABLES.md", "w", encoding="utf-8").write("\n".join(doc))
print("\n".join(doc))
