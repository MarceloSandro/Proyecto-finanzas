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
days_range = (end_date - start_date).days
if days_range <= 7:
    interval = "1h"
else:
    interval = "1d"

st.write(f"Rango de días: {days_range}, Intervalo usado: {interval}")
#...............
@st.cache_data
def load_data(tickers, start, end):
    """Descarga precios de cierre y devuelve df + tickers inválidos"""
    days_range = (end - start).days
    interval = "1h" if days_range <= 7 else "1d"

    raw = yf.download(
        tickers,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,
        progress=False,
        group_by="ticker"
    )

    if raw.empty:
        return pd.DataFrame(), tickers

    # Unificar DataFrame
    if isinstance(raw.columns, pd.MultiIndex):
        df = raw["Close"]
    else:
        df = raw.to_frame(name=tickers[0]) if len(tickers) == 1 else raw

    df = df.dropna(axis=1, how="all")
    valid_tickers = df.columns.tolist()
    invalid_tickers = set(tickers) - set(valid_tickers)

    return df, invalid_tickers

# ===============================
# 🔹 Cargar datos
# ===============================
data, invalid_tickers = load_data(tickers, start_date, end_date)
if invalid_tickers:
    st.warning(f"Algunos tickers no tienen datos válidos: {', '.join(invalid_tickers)}")

if data.empty or data.shape[1] == 0:
    st.warning("No hay datos válidos para los tickers seleccionados.")
    st.stop()

# ===============================
# 🔹 Normalización base 100
# ===============================
norm = pd.DataFrame(index=data.index)
for col in data.columns:
    first_valid = data[col].dropna().iloc[0]
    norm[col] = data[col] / first_valid * 100

series = data[ref_ticker].dropna()
first_price, last_price = series.iloc[0], series.iloc[-1]
first_date, last_date = series.index[0], series.index[-1]
pct_change = (last_price / first_price - 1) * 100

col1, col2, col3 = st.columns(3)
col1.metric(f"{ref_ticker} – Último precio", f"{last_price:.2f}")
col2.metric("Cambio en el período", f"{pct_change:+.2f} %")
col3.caption(f"Desde {first_date.strftime('%Y-%m-%d')} hasta {last_date.strftime('%Y-%m-%d')}")

# ===============================
# 🔹 Gráficos
# ===============================
st.subheader("📊 Evolución de mercado")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11,7), sharex=True)

norm.plot(ax=ax1, linewidth=2)
ax1.set_title("Desempeño relativo (Base = 100)")
ax1.set_ylabel("Índice")
ax1.grid(True, alpha=0.3)
if scale == "Logarítmica":
    ax1.set_yscale("log")

series.plot(ax=ax2, linewidth=2, color="black", label=ref_ticker)
ax2.scatter(last_date, last_price, s=60, zorder=3)
ax2.annotate(f"{last_price:.2f}\n({pct_change:+.2f}%)",
             xy=(last_date, last_price), xytext=(10,10),
             textcoords="offset points", fontsize=9,
             bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
ax2.set_title(f"Precio absoluto – {ref_ticker}")
ax2.set_ylabel("Precio")
ax2.grid(True, alpha=0.3)
ax2.legend()

# Formato dinámico del eje X
days_range = (end_date - start_date).days
if days_range <= 3:
    locator, formatter = mdates.HourLocator(interval=1), mdates.DateFormatter("%d-%m %H:%M")
elif days_range <= 7:
    locator, formatter = mdates.HourLocator(interval=3), mdates.DateFormatter("%d-%m %H:%M")
elif days_range <= 30:
    locator, formatter = mdates.DayLocator(interval=1), mdates.DateFormatter("%d-%m")
elif days_range <= 180:
    locator, formatter = mdates.DayLocator(interval=7), mdates.DateFormatter("%d-%m")
else:
    locator, formatter = mdates.MonthLocator(interval=1), mdates.DateFormatter("%m-%Y")

for ax in [ax1, ax2]:
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    if days_range <= 7:
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    ax.grid(True, which="major", alpha=0.4)
    ax.grid(True, which="minor", alpha=0.15)
    ax.tick_params(axis="x", rotation=90, labelsize=8)

plt.tight_layout()
st.pyplot(fig)
