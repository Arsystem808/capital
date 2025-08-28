
# CapinteL-Q — Streamlit (Polygon) • без бэктеста

## Запуск
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# открой .env и вставь POLYGON_API_KEY=... (без кавычек)
streamlit run app.py
```

## Что делает
- Берёт дневные свечи из Polygon.
- Считает: многопериодные уровни (от прошлого периода), Heikin Ashi серии, MACD-hist стрики/замедление, RSI-перцентили, ATR.
- Склеивает сценарии «перегрев у крыши / перепроданность у дна» + правила по середине (mid/long).
- Выдаёт **человеческий текст** (вход/цели/защита/WAIT), без раскрытия формул.
- В expander — диагностическая инфа только для владельца.
