"""No-HMM, point-in-time baselines for the Bybit BTCUSDT carry pilot."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/"data/normalized/bybit"; OUT=ROOT/"reports"
# VIP-0 taker fee-only round trip: 2 x (10 bps spot + 5.5 bps perp) = 31 bps.
# Base and stress add explicit, non-historical execution allowances.
COSTS={"optimistic_documented_fee_only":31,"base_conservative":50,"stress":100} # bps per full round trip of both legs
def p(name): return pd.read_parquet(D/f"{name}.parquet").sort_values("timestamp_utc")
def max_dd(x): return (x/x.cummax()-1).min()
def build():
 s=p("spot_candles")[["timestamp_utc","open","close"]].rename(columns={"open":"spot_open","close":"spot_close"})
 q=p("perp_candles")[["timestamp_utc","open","close"]].rename(columns={"open":"perp_open","close":"perp_close"})
 m=p("mark_price")[["timestamp_utc","close"]].rename(columns={"close":"mark_close"})
 x=s.merge(q,on="timestamp_utc").merge(m,on="timestamp_utc")
 for c in x.columns[1:]: x[c]=pd.to_numeric(x[c])
 x["basis"]=(x.mark_close-x.spot_close)/x.spot_close
 x["spot_ret"]=x.spot_open.pct_change().shift(-1);x["perp_ret"]=x.perp_open.pct_change().shift(-1)
 x["hedged_return"]=x.spot_ret-x.perp_ret
 f=p("funding")[["timestamp_utc","fundingRate"]];f.fundingRate=pd.to_numeric(f.fundingRate)
 x=x.merge(f.rename(columns={"fundingRate":"funding_settled"}),on="timestamp_utc",how="left")
 # only settlement strictly before signal timestamp may be a feature
 x["last_settled_funding"]=x.funding_settled.ffill().shift(1)
 x["vol_24h"]=x.spot_ret.rolling(24).std().shift(1)
 x["basis_lag"]=x.basis.shift(1)
 return x
def evaluate(x,name,signal):
 # Signal made from closed candle t; execution/holding begins at next open.
 position=signal.fillna(False).astype(int).shift(1).fillna(0)
 z=x.copy();z["position"]=position;z["turnover"]=position.diff().abs().fillna(position.abs())
 z["gross_return"]=z.position*(z.hedged_return+z.funding_settled.fillna(0))
 rows=[]
 for scenario,bps in COSTS.items():
  # bps is an explicit two-leg round-trip assumption; one entry or exit pays half.
  z["net_return"]=z.gross_return-z.turnover*(bps/20000)
  z["equity"]=(1+z.net_return.fillna(0)).cumprod(); active=z.position.mean(); n=z.net_return.dropna()
  rows.append({"strategy":name,"cost_scenario":scenario,"net_return":z.equity.iloc[-1]-1,"gross_return":(1+z.gross_return.fillna(0)).prod()-1,"funding_return":(z.position*z.funding_settled.fillna(0)).sum(),"basis_plus_price_return":(z.position*z.hedged_return).sum(),"max_drawdown":max_dd(z.equity),"annualized_volatility":n.std()*(24*365)**.5,"turnover_events":z.turnover.sum(),"exposure":active})
  OUT.mkdir(exist_ok=True);z.to_parquet(OUT/f"pilot_{name}_{scenario}.parquet",index=False)
 return rows
def funding_rebalance_signal(x, rule):
    """Change exposure only after a settled funding observation, then execute t+1."""
    updates=pd.Series(pd.NA,index=x.index,dtype="object")
    at_settlement=x.funding_settled.notna()
    updates.loc[at_settlement]=rule.loc[at_settlement].astype(int)
    return updates.ffill().fillna(0).astype(bool)
def main():
 x=build(); threshold=0.00005 # 0.5 bp per funding window; candidate hurdle, not optimized
 signals={"always_on":pd.Series(True,index=x.index),"positive_last_settled_funding":funding_rebalance_signal(x,x.last_settled_funding>0),"funding_above_threshold":funding_rebalance_signal(x,x.last_settled_funding>threshold),"positive_funding_low_vol_or_basis":funding_rebalance_signal(x,(x.last_settled_funding>0)&((x.vol_24h<x.vol_24h.expanding().median())|(x.basis_lag>0)))}
 result=[]
 for n,s in signals.items():result+=evaluate(x,n,s)
 r=pd.DataFrame(result);r.to_csv(OUT/"baseline_summary.csv",index=False);print(r.to_string(index=False,float_format=lambda v:f"{v:.4%}"))
if __name__=="__main__":main()
