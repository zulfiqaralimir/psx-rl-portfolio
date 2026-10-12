import pandas as pd
for t in ["KEL","UBL","SYS","LUCK","MARI","HUBC","NBP"]:
    c=pd.read_csv(rf"D:\psx_rl_portfolio\data\clean\{t}.csv",parse_dates=["date"]); c["cr"]=c.close.pct_change(); c["ar"]=c.adj_close.pct_change()
    x=c[c.cr.abs()>.15]
    for _,r in x.iterrows(): print(t,r.date.date(),f"close {r.cr:+.0%} adj {r.ar:+.0%}")
