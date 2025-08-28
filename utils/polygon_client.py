import os
import datetime as dt
import requests
import pandas as pd

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "").strip()

BASE = "https://api.polygon.io/v2/aggs/ticker"

def _daterange(days: int):
    to = dt.datetime.utcnow().date()
    frm = to - dt.timedelta(days=days)
    return frm.isoformat(), to.isoformat()

def fetch_daily(ticker: str, days: int = 420, adjusted: bool = True) -> pd.DataFrame:
    """
    Загружает дневные свечи 1d c Polygon.io для тикера (например: QQQ, AAPL, X:BTCUSD).
    Возвращает DataFrame с колонками: Date, Open, High, Low, Close, Volume.
    """
    if not POLYGON_API_KEY:
        raise RuntimeError("POLYGON_API_KEY отсутствует в окружении/секретах")

    frm, to = _daterange(days)
    params = {
        "adjusted": str(adjusted).lower(),
        "sort": "asc",
        "limit": 50000,
        "apiKey": POLYGON_API_KEY,
    }
    url = f"{BASE}/{ticker}/range/1/day/{frm}/{to}"
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Polygon может возвращать {"results":[],"status":"OK"} или {"status":"DELAYED"} — учитываем это
    results = (data or {}).get("results") or []
    if not results:
        status = (data or {}).get("status")
        raise RuntimeError(f"Polygon вернул пусто (status={status})")

    rows = []
    for x in results:
        # ts millis -> date
        d = dt.datetime.utcfromtimestamp(int(x["t"]) / 1000).date()
        rows.append({
            "Date": d,
            "Open": float(x["o"]),
            "High": float(x["h"]),
            "Low": float(x["l"]),
            "Close": float(x["c"]),
            "Volume": float(x.get("v", 0.0)),
        })

    df = pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)
    return df
