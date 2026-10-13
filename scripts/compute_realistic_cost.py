"""Realistic one-way (per-side) cost of a PSX ready-market equity trade, in % of trade value.
Writes data/fee_schedule.csv (each item with source, source date, primary/secondary) and results/realistic_cost.csv (scenarios).
Percent rates are of trade value; 'per 100k' items are Rs per Rs 100,000 traded (x 0.001 -> %). Sales tax applies to commission and PSX trading fee only."""
import pandas as pd

PSX = "https://psx.com.pk/psx/themes/psx/uploads/Schedule-of-Charges-Updated-as-on-December-18-2024.pdf"
TA = "https://www.tickeranalysts.com/blog/psx-trading-fees-charges-explained"
rows = [
 # item, value_pct, unit, source, source_date, type, note
 ("PSX trading fee (ready market)", 0.0035, "% of value (Rs 3.50 per Rs 100,000)", PSX, "2024-12-18", "primary (PSX schedule, read from the PDF)", "taxed with sales tax"),
 ("SECP levy", 0.00065, "% of value (Rs 0.65 per Rs 100,000)", PSX, "2024-12-18", "primary", ""),
 ("PSX regulatory fee (ready market)", 0.00062084, "% of value (Rs 0.62084 per Rs 100,000)", PSX, "2024-12-18", "primary", "schedule says it is discontinued from 2025-08-29 or when SECP specifies; whether it is still collected is unverified, kept (negligible)"),
 ("CVT", 0.0, "% of purchase value", PSX, "2024-12-18", "primary", "0.00% in the PSX schedule"),
 ("Advance tax / withholding on trade value", 0.0, "% of purchase and sale value", PSX, "2024-12-18", "primary", "0.00% in the PSX schedule ('in lieu of brokerage commission')"),
 ("NCCPL trade fee", 0.00081, "% of value (Rs 0.81 per Rs 100,000)", TA, "2026-07-22 (page); cites NCCPL schedule Mar 2025", "secondary (not checked against NCCPL)", ""),
 ("NCCPL SECP fee", 0.0003, "% of value (Rs 0.30 per Rs 100,000)", TA, "2026-07-22 (page); cites NCCPL schedule Mar 2025", "secondary", ""),
 ("CDC transaction fee", 0.0036, "% of value, min Rs 5, max Rs 25,000, both sides", TA, "2026-07-22 (page); cites CDC schedule Mar 2025", "secondary", "Rs 5 minimum is ignored; it would add about 0.01 pt for Rs 35k trades"),
 ("Sales tax on commission and PSX trading fee", None, "13% Sindh, 16% Punjab, 15% KP, 15% Balochistan, 16% Islamabad (FED)", TA, "2026-07-22", "secondary", "the PSX schedule only says 'as notified'; KASB's sheet says SST 15% (https://kasb.com/wp-content/uploads/2025/01/commision-Structure.pdf, file uploaded 2025-01); central case uses 15%"),
 ("Brokerage commission, discount broker", 0.15, "% of value", TA, "2026-07-22", "secondary", "PSX allowed minimum 0.15% for shares priced Rs 20 and above (same page); no official rate, each broker sets its own"),
 ("Brokerage commission, full-service broker", 0.30, "% of value (6 paisa/share minimum)", "https://kasb.com/wp-content/uploads/2025/01/commision-Structure.pdf", "2025-01 (file path)", "broker's own commission sheet", "one broker's published rate"),
 ("Capital gains tax", None, "15% of net gains (filer); non-filer higher", "https://www.investify.pk/blog/psx-trading-fees-and-charges", "2026-06-25", "secondary", "tax on profit, not on trade value: NOT in the per-side cost; the backtest is pre-tax"),
 ("Dividend withholding tax", None, "15% filer / 30% non-filer", "https://www.investify.pk/blog/psx-trading-fees-and-charges", "2026-06-25", "secondary", "tax on income; NOT in the per-side cost; adj_close reinvests dividends gross"),
]
sched = pd.DataFrame(rows, columns=["item", "rate_pct", "unit", "source", "source_date", "source_type", "note"])
sched.to_csv(r"D:\psx_rl_portfolio\data\fee_schedule.csv", index=False)

fixed_other = 0.00065 + 0.00062084 + 0.00081 + 0.0003 + 0.0036   # SECP + regulatory + NCCPL x2 + CDC, no sales tax
def one_way(comm, tax):
    return comm * (1 + tax) + 0.0035 * (1 + tax) + fixed_other
sc = pd.DataFrame([
    ("low: 0.15% commission, 13% sales tax", 0.15, 0.13), ("central: 0.15% commission, 15% sales tax", 0.15, 0.15),
    ("high: 0.30% commission, 16% sales tax", 0.30, 0.16)], columns=["scenario", "commission_pct", "sales_tax"])
sc["one_way_pct"] = [one_way(c, t) for c, t in zip(sc.commission_pct, sc.sales_tax)]
sc["round_trip_pct"] = 2 * sc.one_way_pct
sc.to_csv(r"D:\psx_rl_portfolio\results\realistic_cost.csv", index=False)
print(sc.round(4).to_string(index=False))
print("non-commission, non-tax items per side (%):", round(0.0035 * 1.15 + fixed_other, 5))
