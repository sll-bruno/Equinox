"""Idempotent public-data collector for the Bybit BTCUSDT pilot."""
from __future__ import annotations
import argparse, hashlib, json, time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; BASE="https://api.bybit.com"
SPECS={
"spot_candles":("/v5/market/kline",{"category":"spot","symbol":"BTCUSDT","interval":"60","limit":1000}),
"perp_candles":("/v5/market/kline",{"category":"linear","symbol":"BTCUSDT","interval":"60","limit":1000}),
"mark_price":("/v5/market/mark-price-kline",{"category":"linear","symbol":"BTCUSDT","interval":"60","limit":1000}),
"index_price":("/v5/market/index-price-kline",{"category":"linear","symbol":"BTCUSDT","interval":"60","limit":1000}),
"premium_index":("/v5/market/premium-index-price-kline",{"category":"linear","symbol":"BTCUSDT","interval":"60","limit":1000}),
"funding":("/v5/market/funding/history",{"category":"linear","symbol":"BTCUSDT","limit":200}),
"open_interest":("/v5/market/open-interest",{"category":"linear","symbol":"BTCUSDT","intervalTime":"1h","limit":200}),
"account_ratio":("/v5/market/account-ratio",{"category":"linear","symbol":"BTCUSDT","period":"1h","limit":500})}
def ms(x): return int(x.timestamp()*1000)
def get(path,p):
 for n in range(5):
  try:
   url=f"{BASE}{path}?{urlencode(p)}"
   with urlopen(url,timeout=30) as r: d=json.loads(r.read())
   if d.get("retCode")==0:return d,url
   raise RuntimeError(d.get("retMsg"))
  except Exception:
   if n==4:raise
   time.sleep(2**n)
def raw(name,d,url):
 b=json.dumps(d,sort_keys=True,separators=(",",":")).encode(); h=hashlib.sha256(b).hexdigest(); p=ROOT/"data/raw/bybit"/name/f"{h}.json";p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():p.write_bytes(b)
 m={"dataset":name,"url":url,"collected_at_utc":datetime.now(UTC).isoformat(),"sha256":h,"file":str(p.relative_to(ROOT)),"api_time_ms":d.get("time")}; q=ROOT/"data/manifests"/f"{name}-{h}.json";q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(m,indent=2));return d["result"].get("list",[])
def norm(name,rows):
 if not rows:return
 if name.endswith("candles") or name in {"mark_price","index_price","premium_index"}:
  cols=["timestamp_ms","open","high","low","close"]+(["volume","turnover"] if name.endswith("candles") else []);df=pd.DataFrame(rows,columns=cols)
 else:df=pd.DataFrame(rows)
 t=next(c for c in ("timestamp_ms","fundingRateTimestamp","timestamp") if c in df);df["timestamp_utc"]=pd.to_datetime(pd.to_numeric(df[t]),unit="ms",utc=True);df=df.sort_values("timestamp_utc").drop_duplicates("timestamp_utc")
 p=ROOT/"data/normalized/bybit"/f"{name}.parquet";p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():df=pd.concat([pd.read_parquet(p),df]).sort_values("timestamp_utc").drop_duplicates("timestamp_utc")
 df.to_parquet(p,index=False)
def collect(name,start,end):
 path,base=SPECS[name];all=[]
 while start<end:
  # Keep every request within the endpoint's documented row limit; interval pagination is deterministic.
  days=40 if name in {"spot_candles","perp_candles","mark_price","index_price","premium_index","funding"} else (8 if name=="open_interest" else 20)
  stop=min(end,start+timedelta(days=days));p={**base,"start":ms(start),"end":ms(stop)}
  if name in {"funding","open_interest","account_ratio"}:p={**base,"startTime":ms(start),"endTime":ms(stop)}
  d,url=get(path,p);all+=raw(name,d,url);start=stop;time.sleep(.15)
 norm(name,all)
def main():
 a=argparse.ArgumentParser();a.add_argument("--months",type=int,default=3);a.add_argument("--start");a.add_argument("--end");n=a.parse_args()
 def parse_utc(value):
  parsed=datetime.fromisoformat(value.replace("Z","+00:00"));return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
 if bool(n.start)!=bool(n.end): a.error("--start and --end must be supplied together")
 if n.start:
  start,end=parse_utc(n.start),parse_utc(n.end)
  if start>=end:a.error("--start must precede --end")
 else:
  end=datetime.now(UTC).replace(minute=0,second=0,microsecond=0);start=end-timedelta(days=31*n.months)
 for x in SPECS:collect(x,start,end)
 for cat in ("spot","linear"):
  d,url=get("/v5/market/instruments-info",{"category":cat,"symbol":"BTCUSDT"});raw(f"instrument_{cat}",d,url)
if __name__=="__main__":main()
