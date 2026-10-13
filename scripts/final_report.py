"""Consolidated final report (facts and tables only) -> docs/FINAL_REPORT.md. Baselines are recomputed on the patched data at 0.1% and 0.18%
(Sharpe 95% CI: circular block bootstrap of test days, block 20, 4000 draws); RL = mean [95% t-interval over 10 seeds] from stageB (0.1%) and stageC/c0018 (0.18%)."""
import sys
sys.path.insert(0, r"D:\psx_rl_portfolio")
import numpy as np, pandas as pd
from psx_rl.data import load_panel, load_policy_rate, split_slice, load_kse100_close
from psx_rl.env import PortfolioEnv
from psx_rl.metrics import metrics
from psx_rl import baselines as B

R = r"D:\psx_rl_portfolio\results"
P, listed, _ = load_panel(); policy = load_policy_rate()
tr = split_slice(P.index, "train"); te = split_slice(P.index, "test")
w_mv = B.fit_mean_variance(P, tr, policy.reindex(tr.union(policy.index)).ffill().reindex(tr).mean())
kse = load_kse100_close().reindex(P.index).ffill()
rng = np.random.default_rng(12345)


def boot_ci(res, n=4000, blk=20):
    a = res.total_asset; r = a.pct_change().dropna().to_numpy(); years = (a.index[-1] - a.index[0]).days / 365.25; ann = len(r) / years
    rf = policy.reindex(a.index[:-1].union(policy.index)).ffill().reindex(a.index[:-1]).to_numpy() / ann
    T = len(r); nb = int(np.ceil(T / blk)); out = []
    for _ in range(n):
        idx = ((rng.integers(0, T, nb)[:, None] + np.arange(blk)) % T).ravel()[:T]
        out.append((r[idx] - rf[idx]).mean() / r[idx].std(ddof=1) * np.sqrt(ann))
    return np.percentile(out, 2.5), np.percentile(out, 97.5)


def f(x, k, pct=True): return f"{x * 100:.1f}%" if pct else f"{x:.2f}"


def rl_row(s, name):
    g = lambda c, pct: (f"{s[c + '_mean'] * 100:.1f}% [{s[c + '_ci_lo'] * 100:.1f}, {s[c + '_ci_hi'] * 100:.1f}]" if pct else f"{s[c + '_mean']:.2f} [{s[c + '_ci_lo']:.2f}, {s[c + '_ci_hi']:.2f}]")
    return f"| {name} (10-seed mean) | {g('annual_return', 1)} | {g('volatility', 1)} | {g('sharpe', 0)} | {g('max_drawdown', 1)} | {g('turnover', 0)} |"


L = ["# Consolidated results (patched data; facts and tables only)", "",
     "Test split 2022-01-03..2026-10-09. RL cells: mean [95% t-interval over 10 seeds]. Baseline cells: single deterministic run; Sharpe cell has a block-bootstrap 95% interval; the other baseline metrics have no interval.",
     "RL models were trained before the data patch and re-scored on the patched data without retraining (see section b).", ""]
for cost, lab, sumfile in [(0.001, "0.1%", R + r"\stageB\stageB_summary.csv"), (0.0018, "0.18% (realistic PSX/CDC/SECP)", R + r"\stageC\c0018\stageB_summary.csv")]:
    S = pd.read_csv(sumfile).set_index("algo")
    L += [f"## a) Main 29-stock results, {lab} cost per side", "", "| Strategy | Annual return | Volatility | Sharpe | Max drawdown | Turnover/yr |", "|---|---|---|---|---|---|"]
    base = {}
    for name, fn in [("Buy-and-hold", B.buy_and_hold), ("Equal-weight monthly", B.equal_weight_monthly), ("Mean-variance monthly", lambda e: B.mean_variance_monthly(e, w_mv))]:
        res = fn(PortfolioEnv(P, listed, te, cost=cost)); m = metrics(res, policy); lo, hi = boot_ci(res)
        L.append(f"| {name} | {m['annual_return'] * 100:.1f}% | {m['volatility'] * 100:.1f}% | {m['sharpe']:.2f} [{lo:.2f}, {hi:.2f}] | {m['max_drawdown'] * 100:.1f}% | {m['turnover']:.2f} |")
    a = 1e6 * kse.loc[te] / kse.loc[te[0]]; res = pd.DataFrame({"total_asset": a}); m = metrics(res, policy, turnover=False); lo, hi = boot_ci(res)
    L.append(f"| KSE-100 (price index) | {m['annual_return'] * 100:.1f}% | {m['volatility'] * 100:.1f}% | {m['sharpe']:.2f} [{lo:.2f}, {hi:.2f}] | {m['max_drawdown'] * 100:.1f}% | n/a |")
    for algo in ("A2C", "PPO", "DDPG"): L.append(rl_row(S.loc[algo], algo))
    sig = pd.read_csv((R + r"\stageB" if cost == 0.001 else R + r"\stageC\c0018") + r"\stageB_significance.csv")
    L += ["", f"Sharpe difference (algorithm minus baseline), circular block bootstrap: smallest p = {sig.p_two_sided.min():.3f}; comparisons with p < 0.05: {(sig.p_two_sided < 0.05).sum()} of {len(sig)}.", ""]

# ---- b) patch effect
E = pd.read_csv(R + r"\patch_effect.csv")
L += ["## b) Effect of the PSX data patch (test Sharpe before -> after)", "",
      "Patch: rows restored/added/date-corrected for MARI, LUCK, BAFL, SYS, UBL from PSX tables; PAEL pre-2013-08-29 rescale 0.7031 (2014 bonus not applied). Trained models re-scored, not retrained; the PAEL change touches training data, so its effect on trained agents is unmeasured.", "",
      "| Cost/side | Strategy | Before | After | Change |", "|---|---|---|---|---|"]
for _, r in E[E.cost_per_side.isin([0.001, 0.0018])].iterrows():
    L.append(f"| {r.cost_per_side * 100:g}% | {r.algo} ({r.kind}) | {r.sharpe_mean_before:.4f} | {r.sharpe_mean_after:.4f} | {r.sharpe_mean_after - r.sharpe_mean_before:+.4f} |")
chg = (E.sharpe_mean_after - E.sharpe_mean_before).abs()
L += ["", f"All {len(E)} rows (5 cost levels): max |Sharpe change| = {chg.max():.4f} ({E.loc[chg.idxmax(), 'algo']}, {E.loc[chg.idxmax(), 'cost_per_side'] * 100:g}%). Significance: 60 comparisons, 0 with p < 0.05 before and after; max change in a Sharpe difference 0.0097. Full table: `results/patch_effect.csv`.", ""]

# ---- c) small-break scan
S = pd.read_csv(r"D:\psx_rl_portfolio\data\small_breaks.csv")
fl = S[S.flag.notna()]
L += ["## c) Small-break scan (`data/small_breaks.csv`)", "",
      "Scan of all 29 tickers for 5-30% daily close moves, compared with adj_close; run BEFORE the data patch and not re-run after it. Candidates are not corrections: nothing in data/clean was changed because of this scan.", "",
      f"- Candidates: {len(S)}; adj_close status: " + ", ".join(f"{k} {v}" for k, v in S.adj_close_status.value_counts().items()) + f"; persistent (level shift that stays): {int(S.persistent.sum())}; beyond the empirical daily price limit (7.5% until mid-2024, 10% after): {int(S.beyond_daily_limit.sum())}.",
      f"- Flagged 'CHECK: drop beyond daily limit, not market-wide, adj_close did not (fully) adjust': {len(fl)} rows ({int(fl.persistent.sum())} persistent), in {fl.ticker.nunique()} tickers: " + ", ".join(f"{k} {v}" for k, v in fl.ticker.value_counts().items()) + ".",
      "- The five split-type breaks (MARI, LUCK, BAFL, SYS, UBL) and PAEL were examined against PSX tables (`data/split_events.csv`, `data/split_verification.csv`); the other flagged rows are unreviewed (status: unverified).", ""]
top = fl.assign(a=fl.close_ret.abs()).sort_values("a", ascending=False).head(15)
L += ["Largest flagged rows:", "", "| Ticker | Date | Close return | adj_close status | Persistent |", "|---|---|---|---|---|"]
for _, r in top.iterrows(): L.append(f"| {r.ticker} | {r.date} | {r.close_ret * 100:+.1f}% | {r.adj_close_status} | {r.persistent} |")
L.append("")

# ---- d) cost sensitivity and walk-forward
t2 = pd.read_csv(R + r"\tables\table2_sharpe_by_cost.csv"); t4 = pd.read_csv(R + r"\tables\table4_walkforward_sharpe.csv")
L += ["## d) Cost sensitivity (test Sharpe; RL mean [95% CI over 10 seeds]; patched data)", "", t2.to_markdown(index=False), "",
      "## d) Walk-forward (0.1% cost; patched data; RL models trained pre-patch and re-scored)", "", t4.to_markdown(index=False), ""]
open(r"D:\psx_rl_portfolio\docs\FINAL_REPORT.md", "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
