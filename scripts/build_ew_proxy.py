"""Equal-weight PROXY benchmark of the 29 tickers (NOT KSE-100). Daily rebalanced,
total-return (adj_close) returns, mean over tickers with a return that day.
Returns with |r|>40% are treated as missing (unadjusted splits / bad prints)."""
import pandas as pd, glob, os
R={}
for f in sorted(glob.glob(r"D:\psx_rl_portfolio\data\clean\*.csv")):
    c=pd.read_csv(f,parse_dates=["date"]).set_index("date"); r=c.adj_close.pct_change(); R[os.path.basename(f)[:-4]]=r.where(r.abs()<=.4)
R=pd.DataFrame(R)
out=pd.DataFrame({"ew_return":R.mean(axis=1),"n_tickers":R.notna().sum(axis=1)}).dropna()
out["ew_index"]=100*(1+out.ew_return).cumprod()
out.to_csv(r"D:\psx_rl_portfolio\data\benchmark_ew_proxy.csv")
print(out.index[0].date(),out.index[-1].date(),len(out),round(out.ew_index.iloc[-1],1),"n range",out.n_tickers.min(),out.n_tickers.max())
y=(out.ew_index.iloc[-1]/100)**(365.25/(out.index[-1]-out.index[0]).days)-1; print(f"CAGR {y:.1%}")
