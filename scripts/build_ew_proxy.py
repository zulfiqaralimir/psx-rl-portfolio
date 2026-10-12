"""Equal-weight PROXY benchmark of the 29 tickers (NOT KSE-100). Daily rebalanced,
total-return (adj_close_fixed) returns, simple mean over tickers with a return that day.
No return-exclusion rule."""
import pandas as pd, glob, os
R=pd.DataFrame({os.path.basename(f)[:-4]:pd.read_csv(f,parse_dates=["date"]).set_index("date").adj_close_fixed.pct_change() for f in sorted(glob.glob(r"D:\psx_rl_portfolio\data\clean\*.csv"))})
out=pd.DataFrame({"ew_return":R.mean(axis=1),"n_tickers":R.notna().sum(axis=1)}).dropna()
out["ew_index"]=100*(1+out.ew_return).cumprod()
out.to_csv(r"D:\psx_rl_portfolio\data\benchmark_ew_proxy.csv")
y=(out.ew_index.iloc[-1]/100)**(365.25/(out.index[-1]-out.index[0]).days)-1
print(out.index[0].date(),out.index[-1].date(),len(out),"final",round(out.ew_index.iloc[-1],1),f"CAGR {y:.1%}")
print("n_tickers min/median",out.n_tickers.min(),out.n_tickers.median(),"days<20:",(out.n_tickers<20).sum())
print("max |ret|",out.ew_return.abs().max().round(3),out.ew_return.abs().idxmax().date(),"| worst 3:",out.ew_return.nsmallest(3).round(3).to_dict())
