"""Before/after effect of the PSX data patch on the test results. Reads results/pre_patch/ (saved before the patch) and the regenerated results.
Writes results/patch_effect.csv and prints the Sharpe changes."""
import pandas as pd
R = r"D:\psx_rl_portfolio\results"
pre_s = pd.read_csv(R + r"\pre_patch\stageC_summary.csv"); new_s = pd.read_csv(R + r"\stageC\stageC_summary.csv")
pre_g = pd.read_csv(R + r"\pre_patch\stageC_significance.csv"); new_g = pd.read_csv(R + r"\stageC\stageC_significance.csv")
k = ["cost_per_side", "algo"]
m = pre_s[k + ["annual_return_mean", "sharpe_mean", "sharpe_ci_lo", "sharpe_ci_hi"]].merge(new_s[k + ["annual_return_mean", "sharpe_mean", "sharpe_ci_lo", "sharpe_ci_hi"]], on=k, suffixes=("_before", "_after"))
m["sharpe_change"] = m.sharpe_mean_after - m.sharpe_mean_before; m["annual_return_change"] = m.annual_return_mean_after - m.annual_return_mean_before
m.insert(2, "kind", "RL (10-seed mean)")
b = lambda g: g.drop_duplicates(["cost_per_side", "baseline"])[["cost_per_side", "baseline", "baseline_sharpe"]]
bm = b(pre_g).merge(b(new_g), on=["cost_per_side", "baseline"], suffixes=("_before", "_after")).rename(columns={"baseline": "algo"})
bm["kind"] = "baseline"; bm["sharpe_mean_before"], bm["sharpe_mean_after"] = bm.baseline_sharpe_before, bm.baseline_sharpe_after
bm["sharpe_change"] = bm.sharpe_mean_after - bm.sharpe_mean_before
out = pd.concat([m, bm[["cost_per_side", "algo", "kind", "sharpe_mean_before", "sharpe_mean_after", "sharpe_change"]]], ignore_index=True)
out.to_csv(R + r"\patch_effect.csv", index=False)
pd.set_option("display.width", 200)
print(out[["cost_per_side", "algo", "kind", "sharpe_mean_before", "sharpe_mean_after", "sharpe_change"]].round(4).to_string(index=False))
key = ["cost_per_side", "algo", "baseline"]
p = pre_g[key + ["sharpe_diff", "p_two_sided"]].merge(new_g[key + ["sharpe_diff", "p_two_sided"]], on=key, suffixes=("_before", "_after"))
print("comparisons:", len(p), "| p<0.05 before:", int((p.p_two_sided_before < 0.05).sum()), "after:", int((p.p_two_sided_after < 0.05).sum()),
      "| max |change in Sharpe difference|:", round(float((p.sharpe_diff_after - p.sharpe_diff_before).abs().max()), 4), "| min p before/after:", p.p_two_sided_before.min(), p.p_two_sided_after.min())
p.to_csv(R + r"\patch_effect_significance.csv", index=False)
