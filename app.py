
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
# --- выбор горизонта ---
h_label = st.selectbox(
    "Горизонт:",
    ["short (1–5 дней)", "mid (1–4 недели)", "long (1–6 месяцев)"]
)

# ключ горизонта: 'short' | 'mid' | 'long'
if h_label.startswith("short"):
    horizon = "short"
elif h_label.startswith("mid"):
    horizon = "mid"
else:
    horizon = "long"

# сколько дней тянем историю для анализа (int!)
LOOKBACK_BY_HZ = {"short": 90, "mid": 400, "long": 1200}
lookback_days = int(LOOKBACK_BY_HZ[horizon])
