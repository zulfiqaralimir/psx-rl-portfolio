import pandas as pd, glob, os
raw=r"D:\psx_rl_portfolio\data\raw"; out=r"D:\psx_rl_portfolio\data\clean"
D={os.path.basename(f)[:-4]:pd.read_csv(f,parse_dates=["date"]) for f in glob.glob(raw+r"\*.csv")}
# market-wide holiday dates: >=80% of tickers that exist on the date have zero volume
allv=pd.concat([d.assign(t=t) for t,d in D.items()])
share=allv.groupby("date").apply(lambda g:(g.volume==0).mean())
hol=set(share[share>=0.8].index)
print("market-wide zero-volume dates:",len(hol),"of",len(share))
rows=[]
for t,d in sorted(D.items()):
    zero=d.volume==0; onhol=d.date.isin(hol)
    stale=(~zero)&(d[["open","high","low","close"]].diff().abs().sum(axis=1)==0)
    c=d[~zero].copy()
    c.to_csv(f"{out}\\{t}.csv",index=False)
    first=c.date.min()
    lead=d[d.date<first]
    # leading run of constant OHLC among kept rows
    k=c.reset_index(drop=True); ch=(k[["open","high","low","close"]].diff().abs().sum(axis=1)>0)
    lead_const=int(ch.values.argmax()) if ch.any() else len(k)
    cr=c.close.pct_change().abs(); ar=c.adj_close.pct_change().abs()
    A=int(((cr>.15)&(ar<=.15)).sum()); B=int(((cr>.15)&(ar>.15)).sum())
    rows.append(dict(t=t,raw=len(d),removed=int(zero.sum()),on_hol=int((zero&onhol).sum()),nonhol_zero=int((zero&~onhol).sum()),stale_nonzero=int(stale.sum()),kept=len(c),
      first_raw=d.date.min().date(),first_trade=first.date(),lead_zero_rows=len(lead),lead_const=lead_const,last=c.date.max().date(),A_covered=A,B_uncovered_or_real=B))
r=pd.DataFrame(rows); pd.set_option("display.width",250); print(r.to_string(index=False))
print(r[["raw","removed","on_hol","nonhol_zero","stale_nonzero","A_covered","B_uncovered_or_real"]].sum())
