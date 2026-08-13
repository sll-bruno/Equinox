"""Fail-fast quality checks for normalized Bybit pilot data."""
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/"data/normalized/bybit"
def load(name): return pd.read_parquet(D/f"{name}.parquet").sort_values("timestamp_utc")
def main():
 names=["spot_candles","perp_candles","mark_price","index_price","premium_index","open_interest","account_ratio","funding"]
 for n in names:
  x=load(n); assert x.timestamp_utc.is_unique, f"duplicates: {n}"; assert x.timestamp_utc.dt.tz is not None, f"non-UTC: {n}"; assert len(x), f"empty: {n}"
  if n!="funding":
   # Two declared research windows are stored: the original 2026 pilot and the
   # separate 2023-24 rally stress window. Only the gap between them is allowed;
   # they are never silently joined into one backtest.
   previous=x.timestamp_utc.shift();gaps=x.timestamp_utc.diff()
   allowed=(previous<=pd.Timestamp("2024-09-01T00:00:00Z")) & (x.timestamp_utc>=pd.Timestamp("2026-05-12T00:00:00Z"))
   unexpected=(gaps>pd.Timedelta("2h")) & ~allowed
   assert not unexpected.any(), f"unexpected gap >2h: {n}"
 for n in ("spot_candles","perp_candles","mark_price","index_price"):
  x=load(n); assert (pd.to_numeric(x.close)>0).all(), f"nonpositive price: {n}"
 x=load("open_interest"); assert (pd.to_numeric(x.openInterest)>=0).all(), "negative OI"
 f=load("funding"); assert (pd.to_numeric(f.fundingRate).abs()<=0.01).all(), "implausible funding"
 s=set(load("spot_candles").timestamp_utc); p=set(load("perp_candles").timestamp_utc); assert len(s&p)>100, "spot/perp join too small"
 print("PASS: normalized Bybit pilot quality checks")
if __name__=="__main__": main()
