"""Drop spike-and-reverse rows from data/clean: |1-day close move| > 40% and the
next row brings the close back to within 15% of the pre-spike close.
Run after clean_and_audit.py. Removed rows -> data/removed_rows.csv."""
import pandas as pd, glob, os
base=r"D:\psx_rl_portfolio\data"; removed=[]; unrev=[]
for f in sorted(glob.glob(base+r"\clean\*.csv")):
    t=os.path.basename(f)[:-4]; df=pd.read_csv(f,parse_dates=["date"])
    while True:
        r=df.close.pct_change(); back=df.close.shift(-1)/df.close.shift(1)-1
        m=(r.abs()>.4)&(back.abs()<.15)
        if not m.any(): break
        for i in df.index[m]:
            removed.append({"ticker":t,**df.loc[i].to_dict(),"reason":"spike_reverse","ret_in":r[i],"ret_next":df.close.shift(-1)[i]/df.close[i]-1})
        df=df[~m].reset_index(drop=True)
    r=df.close.pct_change()
    for i in df.index[r.abs()>.4]: unrev.append((t,df.date[i].date(),round(r[i],3)))
    df.to_csv(f,index=False)
out=pd.DataFrame(removed); out["date"]=out.date.dt.strftime("%Y-%m-%d"); out.to_csv(base+r"\removed_rows.csv",index=False)
print("removed",len(out)); print(out.groupby("ticker").size().to_string())
print("remaining >40% moves that do NOT revert:",unrev)

