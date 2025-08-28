
from __future__ import annotations
import numpy as np, pandas as pd, datetime as dt
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from utils.polygon_client import fetch_daily

@dataclass
class Decision:
    stance: str                # "BUY" | "SHORT" | "WAIT"
    entry: tuple|None
    target1: float|None
    target2: float|None
    stop: float|None
    meta: dict

def heikin_ashi(df: pd.DataFrame) -> pd.DataFrame:
    ha = pd.DataFrame(index=df.index, columns=["ha_o","ha_h","ha_l","ha_c"], dtype=float)
    ha["ha_c"] = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    ha_o = []
    for i,(o,c) in enumerate(zip(df["open"].values, df["close"].values)):
        ha_o.append((o+c)/2 if i==0 else (ha_o[i-1] + ha["ha_c"].iloc[i-1]) / 2)
    ha["ha_o"] = ha_o
    ha["ha_h"] = np.maximum.reduce([df["high"].values, ha["ha_o"].values, ha["ha_c"].values])
    ha["ha_l"] = np.minimum.reduce([df["low"].values, ha["ha_o"].values, ha["ha_c"].values])
    return ha

def _last_color_run(ha_c: pd.Series) -> tuple[str,int]:
    d = ha_c.diff().fillna(0)
    color = np.where(d>=0, 1, -1)
    run = 1
    for i in range(len(color)-1, 0, -1):
        if color[i]==color[i-1]: run += 1
        else: break
    return ("green" if color[-1]==1 else "red", int(run))

def ema(s: pd.Series, n:int)->pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def macd_hist(c: pd.Series)->pd.Series:
    m = ema(c,12) - ema(c,26)
    sig = ema(m,9)
    return m - sig

def rsi(s: pd.Series, n:int=14)->pd.Series:
    d = s.diff()
    up = d.clip(lower=0); dn = -d.clip(upper=0)
    ru = up.ewm(alpha=1/n, adjust=False).mean()
    rd = dn.ewm(alpha=1/n, adjust=False).mean()
    rs = ru/(rd+1e-9)
    return 100 - 100/(1+rs)

def atr(df: pd.DataFrame, n:int=14)->pd.Series:
    h,l,c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat([h-l,(h-pc).abs(),(l-pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def _prev_period_ohlc(df: pd.DataFrame, horizon:str):
    if horizon=="short":
        grp = df.resample("W-FRI").agg({"high":"max","low":"min","close":"last"}).dropna()
    elif horizon=="mid":
        grp = df.resample("M").agg({"high":"max","low":"min","close":"last"}).dropna()
    else:
        grp = df.resample("Y").agg({"high":"max","low":"min","close":"last"}).dropna()
    if len(grp)<2: raise RuntimeError("Недостаточно истории для прошлого периода.")
    prev = grp.iloc[-2]
    return float(prev["high"]), float(prev["low"]), float(prev["close"])

def fib_pivots_from_prev(df: pd.DataFrame, horizon:str)->dict:
    H,L,C = _prev_period_ohlc(df, horizon)
    P = (H+L+C)/3.0; rng = H-L
    return {
        "P":P, "R1":P+0.382*rng, "R2":P+0.618*rng, "R3":P+1.000*rng,
        "S1":P-0.382*rng, "S2":P-0.618*rng, "S3":P-1.000*rng
    }

def _tol(h:str)->float:
    return {"short":0.008, "mid":0.010, "long":0.012}[h]

def _ha_thr(h:str)->int:
    return {"short":4,"mid":5,"long":6}[h]

def _macd_thr(h:str)->int:
    return {"short":4,"mid":6,"long":8}[h]

def _streak(s: pd.Series, positive: bool=True)->int:
    arr = (s>0) if positive else (s<0)
    run=0
    for v in arr[::-1]:
        if v: run+=1
        else: break
    return run

def analyze_ticker(ticker:str, horizon:str="mid", years:int=5)->Decision:
    end = dt.date.today(); start = end - relativedelta(years=years)
    df = fetch_daily(ticker, start.isoformat(), end.isoformat())
    if df.empty or len(df)<60: raise RuntimeError("Нет данных или слишком короткая история.")
    price = float(df["close"].iloc[-1])

    ha = heikin_ashi(df); ha_color, ha_run = _last_color_run(ha["ha_c"].dropna())
    macdh = macd_hist(df["close"]).dropna()
    macd_pos = _streak(macdh, True); macd_neg = _streak(macdh, False)
    macd_decel_up = False
    if len(macdh)>=4:
        last = macdh.iloc[-4:]
        macd_decel_up = all(np.diff(last.values)<0) and last.iloc[-1]>0
    rsi14 = rsi(df["close"]).dropna()
    win = 180 if len(rsi14)>=180 else max(20, int(len(rsi14)*0.6))
    recent = rsi14.iloc[-win:]
    rhi = float(np.quantile(recent,0.8)); rlo = float(np.quantile(recent,0.2))
    rnow = float(rsi14.iloc[-1])
    atr14 = float(atr(df).iloc[-1])

    piv = fib_pivots_from_prev(df, horizon); tol = _tol(horizon)
    def near(x,y): return abs(x-y)/max(1e-9, y)<=tol

    over_roof = price >= piv["R2"]*(1 - tol)
    at_R3 = near(price, piv["R3"]) or price>piv["R3"]
    at_R2 = near(price, piv["R2"]) and not at_R3
    over_floor = price <= piv["S2"]*(1 + tol)
    at_S3 = near(price, piv["S3"]) or price<piv["S3"]
    at_S2 = near(price, piv["S2"]) and not at_S3

    ha_ok_up = (ha_color=="green" and ha_run>=_ha_thr(horizon))
    ha_ok_dn = (ha_color=="red" and ha_run>=_ha_thr(horizon))
    macd_up_ok = (macd_pos>=_macd_thr(horizon)) or macd_decel_up
    macd_dn_ok = (macd_neg>=_macd_thr(horizon))

    meta = {
        "price": round(price,2),
        "horizon": horizon,
        "diag": {
            "ha":{"color":ha_color,"run":int(ha_run)},
            "macd":{"pos_run":int(macd_pos),"neg_run":int(macd_neg),"decel_up":bool(macd_decel_up)},
            "rsi":{"now":round(rnow,2),"hi_thr":round(rhi,2),"lo_thr":round(rlo,2)},
            "atr": round(atr14,2)
        }
    }

    def rp(x): return round(x,2)
    def zone(a,b): 
        lo=min(a,b); hi=max(a,b)
        return (rp(lo), rp(hi))

    # A) перегрев у крыши — агрессивный SHORT
    if over_roof and ha_ok_up and macd_up_ok:
        if at_R3:
            entry = zone(price*0.995, price*1.003)
            t1, t2 = piv["R2"], piv["P"]
            stop = piv["R3"]*(1+tol)
        else:
            entry = zone(price*0.995, price*1.003)
            t1, t2 = (piv["P"]+piv["S1"])/2, piv["S1"]
            stop = piv["R2"]*(1+tol)
        return Decision("SHORT", entry, rp(t1), rp(t2), rp(stop), meta)

    # B) перепроданность у дна — LONG
    if over_floor and ha_ok_dn and macd_dn_ok:
        if at_S3:
            entry = zone(price*0.997, price*1.003)
            t1, t2 = piv["S2"], piv["P"]
            stop = piv["S3"]*(1-tol)
        else:
            entry = zone(price*0.997, price*1.003)
            t1, t2 = (piv["P"]+piv["R1"])/2, piv["R1"]
            stop = piv["S2"]*(1-tol)
        return Decision("BUY", entry, rp(t1), rp(t2), rp(stop), meta)

    # C) середина — правила для mid/long, краткосрок ждёт край
    if horizon=="short":
        return Decision("WAIT", None, None, None, None, meta)
    elif horizon=="mid":
        if price>piv["P"] and price<piv["R2"]:
            entry = zone(piv["P"]*0.995, piv["R1"]*1.005)
            t1, t2 = piv["R1"], piv["R2"]
            stop = piv["P"] - 0.8*atr14
            return Decision("BUY", entry, rp(t1), rp(t2), rp(stop), meta)
        elif price<piv["P"] and price>piv["S2"]:
            entry = zone(piv["S1"]*0.995, piv["P"]*1.005)
            t1, t2 = piv["P"], piv["R1"]
            stop = piv["S1"] - 0.8*atr14
            return Decision("BUY", entry, rp(t1), rp(t2), rp(stop), meta)
        else:
            return Decision("WAIT", None, None, None, None, meta)
    else:  # long
        if price<=piv["P"]:
            entry = zone(piv["S1"], piv["P"])
            t1, t2 = piv["R1"], piv["R2"]
            stop = piv["S1"] - 1.3*atr14
            return Decision("BUY", entry, rp(t1), rp(t2), rp(stop), meta)
        else:
            return Decision("WAIT", None, None, None, None, meta)
