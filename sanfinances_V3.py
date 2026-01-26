import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import pandas as pd

st.set_page_config(page_title="Proyecto Finanzas", layout="wide")
st.title("📈 Proyecto Finanzas")

# 📂 Presets por categoría
presets = {
    "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
    "Finanzas": ["JPM", "BAC", "GS"],
    "Energía": ["XOM", "CVX", "YPF"],
    "Nucleares": ["OKLO", "CCJ", "LEU", "UEC", "CEG", "URA"],
    "Robótica – Acciones": ["NVDA", "ISRG", "TSLA", "ROK", "TER"],
    "Robótica – ETFs": ["ROBO", "BOTZ"],
    "Robótica – ADRs": ["ABBNY", "FANUY"],
    "Custom": []
}

# 1️⃣ Selector de categoría
category = st.selectbox("Categoría", list(presets.keys()))

# 2️⃣ Multiselect con preset
tickers_selected = st.multiselect(
    "Tickers sugeridos",
    presets[category],
    default=presets[category]
)

# 3️⃣ Entrada manual
tickers_manual = st.text_input(
    "Agregar tickers manualmente (separados por coma)",
    ""
)

# 4️⃣ Unificación y limpieza
tickers = set(tickers_selected)
if tickers_manual.strip():
    manual_list = [t.strip().upper() for t in tickers_manual.split(",")]
    tickers.update(manual_list)
tickers = sorted(tickers)

if len(tickers) == 0:
    st.warning("Seleccioná al menos un ticker.")
    st.stop()

st.subheader("🎯 Ticker de referencia")
ref_ticker = st.selectbox("Elegí un ticker para ver precio absoluto", options=tickers, index=0)

# 📅 Fechas
today = datetime.date.today()
if "start_date" not in st.session_state:
    st.session_state.start_date = datetime.date(2020, 1, 1)
if "end_date" not in st.session_state:
    st.session_state.end_date = today

st.subheader("⏱️ Período rápido")
periods = {"1D": 1, "5D": 5, "1W": 7, "1M": 30, "1Y": 365, "5Y": 365*5}
cols = st.columns(len(periods))
for col, (label, days) in zip(cols, periods.items()):
    if col.button(label):
        st.session_state.start_date = today - datetime.timedelta(days=days)
        st.session_state.end_date = today

# 📅 Fechas editables
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Fecha inicio", key="start_date")
with col2:
    end_date = st.date_input("Fecha fin", key="end_date")

if start_date >= end_date:
    st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
    st.stop()

# ⚙️ Escala del gráfico
scale = st.radio("Escala del gráfico", ["Lineal", "Logarítmica"], horizontal=True)

# ===============================
# 🔹 Función de carga de datos robusta
# ===============================
@st.cache_data
def load_data(tickers, start,_
