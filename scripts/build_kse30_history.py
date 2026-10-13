"""Build data/kse30_history.csv (28 semi-annual reviews, effective 2013-2026) and data/kse30_membership_our29.csv.
Constituent lists come from PSX notice annexes (data/kse30_constituent_lists.csv, parsed from the PDFs). Changes for 2022H1 and 2024H2
are DERIVED by differencing PSX lists (the notices themselves were not found). Everything not found is marked 'unverified'."""
import pandas as pd

L = pd.read_csv(r"D:\psx_rl_portfolio\data\kse30_constituent_lists.csv")
lst = {d: set(g.symbol) for d, g in L.groupby("list_as_of")}
N91 = "https://dps.psx.com.pk/download/attachment/180575-1.pdf"
P = "https://www.psx.com.pk/psx/themes/psx/uploads/"
N99 = P + "Notice_99_KSE-30_Recomposition-31-Jan_2023.pdf"
N821 = P + "Notice-KSE-30-Index-Recomposition-June-2025.pdf"

# list in force before the 2022-03-15 change (H2 2021 notice N-91: in MTL GGL CNERGY NETSOL; out PIOC ININD ISL PRL)
before_n91 = (lst["2021-12-31"] - {"MTL", "GGL", "CNERGY", "NETSOL"}) | {"PIOC", "ININD", "ISL", "PRL"}
# list after the H1-2022 review (effective ~2022-09-15) = Dec-2022 list minus N-99 incomings plus N-99 outgoings
jun22 = (lst["2022-12-31"] - {"PRL", "NETSOL", "SNGP", "PAEL"}) | {"GGL", "MLCF", "TELE", "TREET"}
# list after the H2-2024 review (effective 2025-03-17) = Jun-2025 list minus N-821 incomings plus its outgoings (ENGROH was ENGRO before the rename)
dec24 = ((lst["2025-06-30"] - {"SNGP", "PRL", "BOP", "SSGC", "ENGROH"}) | {"AIRLINK", "DFML", "MTL", "NETSOL", "ENGRO"})
jun24 = lst["2024-06-28"]


def diff(a, b):
    """(added, removed) going from list a to list b"""
    return ", ".join(sorted(b - a)), ", ".join(sorted(a - b))


rows = []


def add(i, period, notice, eff, added, removed, url, stype, status, note=""):
    rows.append(dict(review_id=i, review_period=period, notice_date=notice, effective_date=eff, added=added, removed=removed,
                     source_url=url, source_type=stype, status=status, note=note))


UNV = "unverified (not found)"
slots = ["2012H2", "2013H1", "2013H2", "2014H1", "2014H2", "2015H1", "2015H2", "2016H1", "2016H2"]
effs = ["~2013-02", "~2013-08", "~2014-02", "~2014-08", "~2015-02", "~2015-08", "~2016-02", "~2016-08", "~2017-02"]
for k, (p, e) in enumerate(zip(slots, effs), 1):
    add(k, p, "", e, "", "", "", "", UNV, "effective date is the Feb/Aug-15 pattern, not a found date" if k == 1 else "")
add(10, "2017H1", "2017-08-10 (article)", "2017-08-15", "International Steels (ISL), Millat Tractors (MTL)", "Dawood Hercules (DAWH), Mari Petroleum (MARI)",
    "https://profit.pakistantoday.com.pk/?p=47465 ; https://tribune.com.pk/story/1478579/psx-replaces-two-companies-kse-30-index",
    "news (Profit page read; Tribune from search summary)", "found (news, notice not seen)", "effective date from the Tribune summary")
add(11, "2017H2", "", "2018-02-15", "Sui Southern Gas (SSGC), Engro Polymer (EPCL), Bank AL Habib (BAHL), Aisha Steel (ASL)",
    "Engro Foods (EFOODS), K-Electric (KEL), Hascol Petroleum (HASCOL), Honda Atlas Cars (HCAR)",
    "https://tribune.com.pk/story/1633111/stock-exchange-replaces-four-companies-kse-30-index", "news (search summary only; page returned 403)",
    "found (news summary only)", "review period not stated in what I could read")
add(12, "2018H1", "", "~2018-08 (not stated)", "Bank Alfalah (BAFL), Honda Atlas Cars (HCAR), Mari Petroleum (MARI)",
    "Maple Leaf Cement (MLCF), National Refinery (NRL), Aisha Steel (ASL)",
    "Profit by Pakistan Today (page URL not identified; seen only in a search summary)", "news (search summary only)",
    "found (news summary only)", "HCAR and ASL reverse the Feb-2018 swap; plausible but unconfirmed")
add(13, "2018H2", "", "~2019-02", "", "", "", "", UNV)
add(14, "2019H1", "", "~2019-08", "", "", "", "", UNV)
add(15, "2019H2", "2020-02-20 (article)", "2020-03-13", "Attock Refinery (ATRL), International Steels (ISL)", "Bank of Punjab (BOP), Kot Addu Power (KAPCO)",
    "https://mettisglobal.news/psx-withdraws-kapco-bop-from-kse-30-index", "news (page read)", "found (news, notice not seen)")
add(16, "2020H1", "", "~2020-09", "", "", "", "", UNV)
add(17, "2020H2", "2021-02-01 (article)", "2021-03-15",
    "Attock Refinery (ATRL), Systems (SYS), Ghandhara Industries (GHNI), Pioneer Cement (PIOC), Kot Addu Power (KAPCO), Dawood Hercules (DAWH)",
    "Fauji Cement (FCCL), Hascol Petroleum (HASCOL), Sui Northern Gas (SNGP), National Bank of Pakistan (NBP), Bank Alfalah (BAFL), Bank of Punjab (BOP)",
    "https://dailytimes.com.pk/719399/kse-30-index-recomposed-with-six-modifications/ ; https://profit.pakistantoday.com.pk/2021/01/31/kse-30-index-recomposed-with-six-modifications",
    "news (Daily Times page read)", "found (news, notice not seen)")
add(18, "2021H1", "", "~2021-09", "", "", "", "", UNV, "PSX notice not found; its changes are unknown")
add(19, "2021H2", "2022-01-27", "2022-03-15", "Millat Tractors (MTL), Ghani Global (GGL), Cnergyico (CNERGY), NetSol (NETSOL)",
    "Pioneer Cement (PIOC), International Industries (ININD), International Steels (ISL), Pakistan Refinery (PRL)", N91, "PSX notice N-91", "verified (PSX notice)")
a, r = diff(lst["2021-12-31"], jun22)
add(20, "2022H1", "", "~2022-09-15 (not found)", a, r, "derived from " + N91 + " and " + N99, "derived from PSX lists", "derived (PSX notice not found)",
    "difference between the Dec-2021 list and the Jun-2022 list implied by notice N-99; Telecard (TELE) and Treet (TREET) are inferred members")
add(21, "2022H2", "2023-01-31", "2023-03-15", "Pakistan Refinery (PRL), NetSol (NETSOL), Sui Northern Gas (SNGP), Pak Elektron (PAEL)",
    "Ghani Global (GGL), Maple Leaf Cement (MLCF), Telecard (TELE), Treet (TREET)", N99, "PSX notice N-99", "verified (PSX notice)")
add(22, "2023H1", "2023-07-31", "2023-09-15",
    "Attock Petroleum (APL), Bank Alfalah (BAFL), Cherat Cement (CHCC), Fauji Cement (FCCL), Maple Leaf Cement (MLCF), Pioneer Cement (PIOC)",
    "NetSol (NETSOL), National Refinery (NRL), Pak Elektron (PAEL), Pakistan Refinery (PRL), TPL Properties (TPLP), Unity Foods (UNITY)",
    P + "Notice-784_KSE-30_Recomposition-June-23.pdf", "PSX notice N-784", "verified (PSX notice)")
add(23, "2023H2", "2024-01-31", "2024-03-15",
    "National Refinery (NRL), Shell Pakistan (SHEL), Pakistan Refinery (PRL), Colgate-Palmolive (COLG), Searle (SEARL), TPL Properties (TPLP)",
    "Attock Petroleum (APL), Avanceon (AVN), Engro Polymer (EPCL), Fauji Cement (FCCL), Kot Addu Power (KAPCO), Pioneer Cement (PIOC)",
    P + "Notice_KSE-30_Index_Recomposition-_Dec_2023.pdf", "PSX notice N-99 (2024)", "verified (PSX notice)")
add(24, "2024H1", "2024-07-31", "2024-09-16",
    "Fauji Fertilizer Bin Qasim (FFBL), Fauji Cement (FCCL), Sazgar (SAZEW), Pioneer Cement (PIOC), Pak Elektron (PAEL)",
    "Cherat Cement (CHCC), Colgate-Palmolive (COLG), Shell Pakistan (SHEL), TPL Properties (TPLP), TRG Pakistan (TRG)",
    "https://dps.psx.com.pk/download/attachment/234730-1.pdf", "PSX notice N-735", "verified (PSX notice)")
a, r = diff(jun24, dec24)
add(25, "2024H2", "2025-02-01 (Mettis article)", "2025-03-17", a, r,
    "https://mettisglobal.news/re-composition-ghni-gal-netsol-nbp-dfml-added-to-kse-30-index/ ; derived from PSX lists (" + N821 + ")",
    "derived from PSX lists + news", "derived (PSX notice not found)",
    "Mettis lists only 5 in / 5 out (GHNI GAL NETSOL NBP DFML / BAFL NRL PIOC PRL SNGP); the PSX lists imply 6 / 6, adding AIRLINK in and FFBL out")
add(26, "2025H1", "2025-07-31", "2025-09-15", "Sui Northern Gas (SNGP), Pakistan Refinery (PRL), Bank of Punjab (BOP), Sui Southern Gas (SSGC)",
    "Air Link (AIRLINK), Dewan Farooque Motors (DFML), Millat Tractors (MTL), NetSol (NETSOL)", N821, "PSX notice N-821", "verified (PSX notice)")
add(27, "2025H2", "2026-01-30", "2026-03-16", "Air Link (AIRLINK), National Refinery (NRL)", "Bank AL Habib (BAHL), Pakistan Refinery (PRL)",
    "https://dps.psx.com.pk/download/attachment/269514-1.pdf", "PSX notice N-142", "verified (PSX notice)")
add(28, "2026H1", "2026-07-31", "2026-09-15", "Pakistan Telecommunication (PTC), Bank Alfalah (BAFL), K-Electric (KEL), Fatima Fertilizer (FATIMA)",
    "Air Link (AIRLINK), Ghandhara Automobiles (GAL), Ghandhara Industries (GHNI), Sui Southern Gas (SSGC)",
    "https://dps.psx.com.pk/download/attachment/280653-1.pdf", "PSX notice N-961", "verified (PSX notice)")
rows.append(dict(review_id="x", review_period="year unverified (a January-June review, 2013-2016 likely)", notice_date="",
                 effective_date="Aug 15 (year not shown)", added="Fatima Fertilizer, Engro Foods, Jahangir Siddiqui & Co",
                 removed="ICI Pakistan, Lotte Pakistan, Nestle Pakistan", source_url="https://www.brecorder.com/news/72730",
                 source_type="news (search summary only; page returned 403)", status="unverified (year unknown)",
                 note="Karachi Stock Exchange era; cannot be placed in a slot"))
H = pd.DataFrame(rows)
H.to_csv(r"D:\psx_rl_portfolio\data\kse30_history.csv", index=False)
print(H.status.value_counts().to_string())

# ---- membership of our 29 over the windows where the list in force is known ----
our = ["ATRL", "BAFL", "BOP", "DGKC", "EFERT", "FATIMA", "FCCL", "FFC", "HBL", "HUBC", "KEL", "LUCK", "MARI", "MCB", "MEBL", "MLCF", "NBP",
       "NRL", "OGDC", "PAEL", "POL", "PPL", "PSO", "PTC", "SAZEW", "SEARL", "SNGP", "SYS", "UBL"]
win = [("2022-01-03", "2022-03-14", before_n91), ("2022-03-15", "2022-09-14", lst["2021-12-31"]), ("2022-09-15", "2023-03-14", jun22),
       ("2023-03-15", "2023-09-14", lst["2022-12-31"]), ("2023-09-15", "2024-03-14", lst["2023-06-30"]), ("2024-03-15", "2024-09-15", lst["2023-12-29"]),
       ("2024-09-16", "2025-03-16", jun24), ("2025-03-17", "2025-09-14", dec24), ("2025-09-15", "2026-03-15", lst["2025-06-30"]),
       ("2026-03-16", "2026-09-14", lst["2025-12-31"]), ("2026-09-15", "2026-10-09", lst["2026-06-30"])]
M = pd.DataFrame({"ticker": our})
for s, e, S_ in win:
    M[f"{s}..{e}"] = [t in S_ for t in our]
M.to_csv(r"D:\psx_rl_portfolio\data\kse30_membership_our29.csv", index=False)
days = pd.bdate_range("2022-01-03", "2026-10-09")
frac = {t: sum(len(days[(days >= s) & (days <= e)]) for s, e, S_ in win if t in S_) / len(days) for t in our}
F = pd.Series(frac).sort_values()
print("share of weekdays 2022-01-03..2026-10-09 each of the 29 was a KSE-30 member:")
print(F.round(2).to_string())
print("number of our 29 in the index per window:", [int(sum(t in S_ for t in our)) for s, e, S_ in win])
