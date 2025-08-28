
import os, streamlit as st
from dotenv import load_dotenv
from core_strategy import analyze_ticker
from narrator import humanize

load_dotenv()

st.set_page_config(page_title="CapinteL-Q (Streamlit • Polygon)", page_icon="📈", layout="centered")
st.title("CapinteL-Q — Анализ рынков (Polygon)")

with st.sidebar:
    st.subheader("Служебно")
    st.caption(f"Polygon key: {'OK' if os.getenv('POLYGON_API_KEY') else '—'}")
    st.caption("Источник данных: Polygon.io (дневные агрегаты).")

ticker = st.text_input("Тикер:", value="QQQ").strip().upper()
hz = st.selectbox("Горизонт:", ["short (1–5 дней)","mid (1–4 недели)","long (1–6 месяцев)"], index=1)
hz = hz.split()[0]

if st.button("Проанализировать", type="primary"):
    with st.spinner("Собираю картину…"):
        try:
            d = analyze_ticker(ticker, horizon=hz)
            st.success(humanize(d, ticker))
            with st.expander("Диагностика (для владельца)"):
                st.json(d.meta)
        except Exception as e:
            st.error(f"Ошибка: {e}")
else:
    st.info("Укажи тикер, выбери горизонт и нажми «Проанализировать».")
