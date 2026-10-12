"""Run after clean_and_audit.py + despike.py.
1) drops reviewed multi-day bad windows (appended to data/removed_rows.csv)
2) adds adj_close_fixed = adj_close / ratio for rows before each persistent split break
3) writes data/split_events.csv"""
import pandas as pd
base=r"D:\psx_rl_portfolio\data"
WINDOWS=[("LUCK","2025-02-26","2025-02-28","scale_glitch: ~1/5 of true price (291 vs ~1450), reverts 2025-03-03"),
 ("UBL","2025-06-12","2025-06-13","scale_glitch: pre-split scale (~520) between post-split rows (~258)"),
 ("UBL","2025-06-19","2025-06-20","scale_glitch: pre-split scale (~520) between post-split rows (~258)"),
 ("SYS","2025-04-09","2025-04-11","scale_glitch: ~1/5 of true price (~100 vs ~503), reverts 2025-04-14"),
 ("SYS","2025-05-19","2025-05-26","scale_glitch: ~1/2 of true price (~270 vs ~540) before the real 5:1 break on 2025-05-27")]
EVENTS=[("MARI","2024-09-05",9.0,"price 3641.42->398.97 (9.13x), persists; Yahoo split table 9:1 dated 2024-09-16","yahoo_only"),
 ("BAFL","2026-04-09",2.0,"price 121.63->60.21 (2.02x), persists; Yahoo split table 2:1 dated 2026-04-20","yahoo_only"),
 ("LUCK","2025-04-10",5.0,"price 1560.98->320.37 (4.87x), persists; Yahoo split table 5:1 dated 2025-04-21","yahoo_only"),
 ("SYS","2025-05-27",5.0,"price 543.79->108.82 (5.00x vs last clean row 2025-05-16), persists; Yahoo split table 5:1 dated 2025-05-29","yahoo_only"),
 ("UBL","2025-06-10",2.0,"price 513.26->256.52 (2.00x), persists; Yahoo split table 2:1 dated 2025-06-24","yahoo_only"),
 ("PAEL","2013-08-29",1.5,"price 15.62->10.42 (1.50x), persists; NO matching Yahoo split record (ratio inferred from price only)","unverified")]
rem=pd.read_csv(base+r"\removed_rows.csv"); new=[]
for t,a,b,why in WINDOWS:
    c=pd.read_csv(rf"{base}\clean\{t}.csv"); m=(c.date>=a)&(c.date<=b)
    new.append(c[m].assign(ticker=t,reason=why)); c[~m].to_csv(rf"{base}\clean\{t}.csv",index=False)
rem=pd.concat([rem]+new,ignore_index=True).drop_duplicates(["ticker","date"]); rem.to_csv(base+r"\removed_rows.csv",index=False)
print("removed_rows total",len(rem)); print(rem.groupby("ticker").size().to_string())
import glob, os
for f in glob.glob(base+r"\clean\*.csv"):
    t=os.path.basename(f)[:-4]; c=pd.read_csv(f); c["adj_close_fixed"]=c.adj_close
    for tk,d,k,_,_ in EVENTS:
        if tk==t: c.loc[c.date<d,"adj_close_fixed"]=c.adj_close_fixed/k
    c.to_csv(f,index=False)
pd.DataFrame(EVENTS,columns=["ticker","break_date","ratio","evidence","status"]).to_csv(base+r"\split_events.csv",index=False)
