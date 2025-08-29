
 import os
import datetime as dt
import requests

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "").strip()

# сколько дней тянем историю в зависимости от горизонта
LOOKBACK_BY_HZ = {
    "short": 90,    # 1–5 дней анализа => последние ~3 месяца
    "mid": 400,     # 1–4 недели анализа => последние ~1.5 года
    "long": 1200    # 1–6 месяцев анализа => последние ~5 лет
}

class Decision(dict):
    def __str__(self):
        return (
            f"Decision(stance='{self.get('stance')}', "
            f"entry={self.get('entry')}, "
            f"target1={self.get('target1')}, "
            f"target2={self.get('target2')}, "
            f"stop={self.get('stop')}, "
            f"meta={self.get('meta')})"
        )

# функция получения котировок с Polygon
def fetch_daily(ticker: str, days: int = 400):
    days = int(days)
    if not POLYGON_API_KEY:
        raise RuntimeError("❌ POLYGON_API_KEY отсутствует в .env")

    _from = (dt.datetime.utcnow() - dt.timedelta(days=days)).date().isoformat()
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{_from}/{dt.date.today().isoformat()}"

    r = requests.get(url, params={"adjusted": "true", "apiKey": POLYGON_API_KEY})
    r.raise_for_status()
    data = r.json()
    return data.get("results", [])

# основной анализ
def analyze_ticker(ticker: str, horizon: str = "mid", lookback_days: int = None):
    horizon = horizon.lower().strip()
    if horizon not in LOOKBACK_BY_HZ:
        raise ValueError(f"Неверный горизонт: {horizon}")

    if lookback_days is None:
        lookback_days = LOOKBACK_BY_HZ[horizon]

    candles = fetch_daily(ticker, days=lookback_days)

    if not candles:
        return Decision(
            stance="WAIT",
            entry=None,
            target1=None,
            target2=None,
            stop=None,
            meta={"error": "Нет данных от Polygon"}
        )

    # очень упрощённый пример логики — вместо твоей полной стратегии
    last_close = candles[-1]["c"]

    if horizon == "short":
        stance = "BUY" if last_close % 2 == 0 else "WAIT"
    elif horizon == "mid":
        stance = "WAIT"
    else:
        stance = "LONG" if last_close > candles[0]["c"] else "SHORT"

    return Decision(
        stance=stance,
        entry=(last_close * 0.99, last_close * 1.01),
        target1=last_close * 1.02,
        target2=last_close * 1.05,
        stop=last_close * 0.97,
        meta={"price": last_close, "horizon": horizon}
    )
