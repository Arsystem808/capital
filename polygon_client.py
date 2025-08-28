
import os, time, requests, pandas as pd

BASE = "https://api.polygon.io"

def fetch_daily(ticker: str, start: str, end: str, api_key: str|None=None) -> pd.DataFrame:
    api_key = api_key or os.getenv("POLYGON_API_KEY","").strip()
    if not api_key:
        raise RuntimeError("POLYGON_API_KEY is not set in environment/.env")
    url = f"{BASE}/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
    params = {"adjusted":"true","sort":"asc","limit":50000,"apiKey":api_key}
    r = requests.get(url, params=params, timeout=30, headers={"User-Agent":"CapinteLQ/streamlit"})
    if r.status_code == 429:
        time.sleep(1.5)
        r = requests.get(url, params=params, timeout=30, headers={"User-Agent":"CapinteLQ/streamlit"})
    r.raise_for_status()
    js = r.json()
    rows = js.get("results", [])
    if not rows: 
        return pd.DataFrame(columns=["open","high","low","close","volume"])
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_convert("UTC").dt.normalize()
    df = df.groupby("date").agg(open=("o","first"), high=("h","max"), low=("l","min"), close=("c","last"), volume=("v","sum"))
    df.index.name = "date"
    return df
