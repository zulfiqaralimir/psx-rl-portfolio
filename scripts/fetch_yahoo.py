import time, yfinance as yf
T="ATRL BAFL BOP DGKC EFERT ENGROH FATIMA FCCL FFC HBL HUBC KEL LUCK MARI MCB MEBL MLCF NBP NRL OGDC PAEL POL PPL PSO PTC SAZEW SEARL SNGP SYS UBL".split()
out=r"D:\psx_rl_portfolio\data\raw"
for t in T:
    try:
        df=yf.Ticker(t+".KA").history(start="2013-01-01",auto_adjust=False,actions=False)
        if df.empty: print(t,"EMPTY"); continue
        df.index=df.index.tz_localize(None).strftime("%Y-%m-%d")
        df.index.name="date"
        df=df[["Open","High","Low","Close","Adj Close","Volume"]]
        df.columns=["open","high","low","close","adj_close","volume"]
        df.to_csv(f"{out}\\{t}.csv")
        print(t,len(df),df.index[0],df.index[-1])
    except Exception as e: print(t,"FAILED",str(e)[:80])
    time.sleep(1)
