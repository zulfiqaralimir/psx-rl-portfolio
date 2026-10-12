"""Parse SBP's 'Reverse Repo, Repo and Policy (Target) Rates' PDF text into data/macro/sbp_policy_rate.csv.
Source: https://archive.sbp.org.pk/ecodata/OVR-Repo-History.pdf (SBP DMMD).
Footnote 1 of that document: the reverse-repo (ceiling) rate 'remained as SBP Policy rate till May 24, 2015';
the Policy (Target) Rate column exists from 25-May-2015. So policy rate = 3rd column if present, else the ceiling."""
import re, csv, datetime as dt, pypdf

r = pypdf.PdfReader(r"D:\psx_rl_portfolio\data\macro\sbp_OVR-Repo-History.pdf")
text = "\n".join(p.extract_text(extraction_mode="layout") for p in r.pages)
out = []
for line in text.splitlines():
    m = re.match(r"\s*(\d{1,2}-[A-Za-z]{3}-\d{2})\s+([\d.]+)%(?:\s+([\d.]+)%)?(?:\s+([\d.]+)%)?\s*$", line)
    if not m:
        continue
    d, ceil, floor, pol = m.groups()
    date = dt.datetime.strptime(d, "%d-%b-%y").date()
    if date < dt.date(2012, 12, 1):
        continue
    out.append((date.isoformat(), float(pol) if pol else float(ceil), ceil, floor, pol))
with open(r"D:\psx_rl_portfolio\data\macro\sbp_policy_rate.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["effective_date", "policy_rate_pct", "ceiling_raw", "floor_raw", "policy_col_raw"])
    w.writerows(out)
print(len(out), out[0], out[-1])
