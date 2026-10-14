# Exposure, cash share and the trade-size cap

Retrained agents on patched data, 0.18% per-side cost, test period 2022-01-03 to 2026-10-09, 10 seeds per algorithm (`results/retrain_patched/c0018`). Script: `scripts/exposure_and_cap.py`; per-run numbers in `results/exposure_cap/exposure_runs.csv`. All cap experiments re-score the saved checkpoints; nothing was retrained.

## 1. Exposure and cash (seed means; min-max across seeds in brackets)

| Algorithm | Mean exposure (stocks / portfolio) | Mean cash share | Share of days with cash > 50% |
|---|---|---|---|
| A2C | 99.3% [98.5, 99.6] | 0.7% | 0.7% [0.4, 1.5] |
| DDPG | 99.3% [98.5, 99.7] | 0.7% | 0.5% [0.3, 0.8] |
| PPO | 94.1% [87.4, 97.3] | 5.9% | 5.6% [2.1, 12.2] |

Exposure is stock value / total asset, averaged over test days after day 0 (day 0 is all cash). All three agents are almost fully invested, so their results are close to a long-only equity portfolio; PPO holds more cash than the other two.

## 2. The action cap

- Training and evaluation use `hmax = 100` shares: each action in [-1, 1] per stock is scaled to a trade of up to +/-100 shares per stock per day (`psx_rl/gym_env.py`, `psx_rl/env.py`). The episode starts with Rs 1,000,000 cash.
- In rupees: the median adjusted price over listed test stock-days is about Rs 85 (`adj_close_fixed`, so not nominal prices), so 100 shares is about Rs 8,500 per stock per day, 0.85% of starting capital. If all 29 stocks traded at the cap on one day that would be about Rs 250,000 (25% of starting capital).
- Does it bind? "Hit the cap" here means the policy's action is saturated, |action| >= 0.999 after clipping to [-1, 1] (the trade is then exactly 100 shares). Trades are also limited by holdings (sells) and cash (buys). Share of listed stock-days with a saturated action:

| Algorithm | Saturated actions | Actions with abs value >= 0.5 | Days with at least one saturated action |
|---|---|---|---|
| A2C | 26.6% | 49.4% | 84.0% |
| DDPG | 83.0% | 97.3% | 99.9% |
| PPO | 0.0% | 1.2% | 0.01% |

DDPG sits at the cap on most stock-days (its policy is close to bang-bang), A2C at it on about a quarter of them, and PPO almost never. For DDPG and A2C the cap does bind.

## 3. Cap doubled and removed (no retraining)

`hmax = 200`, and "removed" = `hmax = 1e9` (sells limited by holdings, buys by cash). The policies were trained with `hmax = 100`, so these runs show how sensitive the saved policies are to the trade scale, not what an agent trained without a cap would do. Test Sharpe, 10-seed mean:

| Algorithm | hmax 100 (trained) | hmax 200 | Change | No cap | Change | Exposure at no cap | Turnover at 100 / 200 / no cap |
|---|---|---|---|---|---|---|---|
| A2C | 0.825 | 0.815 | -0.009 | 0.800 | -0.024 | 100% | 0.08 / 0.09 / 0.31 |
| DDPG | 0.788 | 0.699 | -0.089 | 0.455 | -0.333 | 100% | 4.9 / 9.2 / 29.0 |
| PPO | 0.781 | 0.683 | -0.098 | 0.232 | -0.549 | 100% | 0.7 / 1.1 / 23.3 |

Significance (same circular block bootstrap as the main analysis, 12 comparisons per setting: 3 algorithms x 4 baselines):

- hmax 100: no p < 0.05 (smallest 0.36).
- hmax 200: no p < 0.05 (smallest 0.14).
- No cap: 6 of 12 cross below 0.05, all with the agent below the baseline: PPO vs buy-and-hold (p < 0.001), PPO vs equal-weight (p < 0.001), PPO vs KSE-100 (0.015), PPO vs mean-variance (0.011), DDPG vs buy-and-hold (0.027), DDPG vs equal-weight (0.0495). DDPG vs mean-variance is 0.085. No comparison has an agent significantly above a baseline in any setting.

Sharpe only falls when the cap is raised, for every algorithm, and A2C is least affected. Raising the cap does not produce a better agent, and there is no sign that the 100-share cap is what holds the results back. The significant results in the no-cap row come from the saved policies trading much larger amounts (turnover column above), not from any change in what they learned.
