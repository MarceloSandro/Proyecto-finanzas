import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import datetime
import pandas as pd

# ===============================
# 🎨 Estilo Yahoo Finance
# ===============================
YAHOO_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"
]

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#DDDDDD",
    "axes.labelcolor": "#333333",
    "xtick.color": "#555555",
    "ytick.color": "#555555",
    "grid.color": "#E6E6E6",
    "grid.linewidth": 0.6,
    "font.size": 10
})

# ===============================
# 🚀 Streamlit config
# ===============================
st.set_page_config(page_title="Proyecto Finanzas", layout="wide")
st.title("📈 Proyecto Finanzas")

# ===============================
# 📂 Presets
# ===============================
presets = {
    "Tecnología": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
    "Finanzas": ["JPM", "BAC", "GS"],
    "Oil & Gas ADR": ["YPF", "VIST", "PAM", "TGS", "PBR"],
    "Oil & Gas Globales": ["CVX", "XOM"],
    "Oil & Gas ETFs": ["XLE", "XLU"],
    "Nucleares": ["OKLO", "CCJ", "LEU", "UEC", "CEG", "URA"],
    "Robótica – Acciones": ["NVDA", "ISRG", "TSLA", "ROK", "TER"],
    "Robótica – ETFs": ["ROBO", "BOTZ"],
    "Custom": []
}

# ===============================
# 🎛️ Selectores
# ===============================
category = st.selectbox("Categoría", list(presets.keys()))

tickers_selected = st.multiselect(
    "Tickers sugeridos",
    presets[category],
    default=presets[category]
)

tickers_manual = st.text_input(
    "Agregar tickers manualmente (separados por coma)",
    ""
)

tickers = set(tickers_selected)
if tickers_manual.strip():
    tickers.update(t.strip().upper() for t in tickers_manual.split(","))

tickers = sorted(tickers)

if not tickers:
    st.warning("Seleccioná al menos un ticker.")
    st.stop()

ref_ticker = st.selectbox(
    "🎯 Ticker de referencia",
    tickers,
    index=0
)

# ===============================
# ⏱️ Períodos rápidos (RESTAURADO)
# ===============================
st.subheader("⏱️ Período rápido")

today = datetime.date.today()

if "start_date" not in st.session_state:
    st.session_state.start_date = today - datetime.timedelta(days=30)
if "end_date" not in st.session_state:
    st.session_state.end_date = today

periods = {
    "1D": 1,
    "5D": 5,
    "1W": 7,
    "1M": 30,
    "1Y": 365,
    "5Y": 365 * 5
}

cols = st.columns(len(periods))
for col, (label, days) in zip(cols, periods.items()):
    if col.button(label):
        st.session_state.start_date = today - datetime.timedelta(days=days)
        st.session_state.end_date = today

# ===============================
# 📅 Fechas editables
# ===============================
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Fecha inicio", key="start_date")
with col2:
    end_date = st.date_input("Fecha fin", key="end_date")

if start_date >= end_date:
    st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
    st.stop()

scale = st.radio(
    "Escala del gráfico",
    ["Lineal", "Logarítmica"],
    horizontal=True
)

# ===============================
# 📥 Carga de datos
# ===============================
@st.cache_data
def load_data(tickers, start, end):
    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)
    days = (end_ts - start_ts).days

    if days <= 1:
        interval = "1m"
    elif days <= 5:
        interval = "5m"
    elif days <= 7:
        interval = "15m"
    else:
        interval = "1d"

    raw = yf.download(
        tickers,
        start=start_ts,
        end=end_ts,
        interval=interval,
        auto_adjust=True,
        progress=False
    )

    if raw.empty:
        return pd.DataFrame(), []

    if isinstance(raw, pd.Series):
        df = raw.to_frame(name=tickers[0])
    else:
        df = raw["Close"] if "Close" in raw.columns else raw

    df = df.dropna(axis=1, how="all")
    return df, []

data, _ = load_data(tickers, start_date, end_date)

if data.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

# ===============================
# 🔢 Normalización Base 100
# ===============================
norm = data / data.iloc[0] * 100

series = data[ref_ticker].dropna()
first_price, last_price = series.iloc[0], series.iloc[-1]
pct_change = (last_price / first_price - 1) * 100

st.metric(
    f"{ref_ticker} – Último precio",
    f"{last_price:.2f}",
    f"{pct_change:+.2f}%"
)

# ===============================
# 📊 Gráficos SIN huecos
# ===============================
x = range(len(data.index))
x_labels = data.index

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

# 🔹 Desempeño relativo
for i, col in enumerate(norm.columns):
    ax1.plot(
        x,
        norm[col],
        linewidth=2.2 if col == ref_ticker else 1.6,
        alpha=1.0 if col == ref_ticker else 0.75,
        color=YAHOO_COLORS[i % len(YAHOO_COLORS)],
        label=col
    )

ax1.set_title("Desempeño relativo (Base 100)", loc="left", fontsize=13, fontweight="bold")
ax1.set_ylabel("Índice")
ax1.grid(True)
ax1.legend(ncol=4, frameon=False)

if scale == "Logarítmica":
    ax1.set_yscale("log")

# 🔹 Precio absoluto
ax2.plot(x, series.values, linewidth=2.6, color="black")
ax2.fill_between(x, series.values, min(series.values), alpha=0.05)

ax2.scatter(len(series) - 1, last_price, s=70, color="black", zorder=5)

ax2.annotate(
    f"{last_price:.2f}\n({pct_change:+.2f}%)",
    xy=(len(series) - 1, last_price),
    xytext=(12, 12),
    textcoords="offset points",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#CCCCCC")
)

ax2.set_title(f"Precio – {ref_ticker}", loc="left", fontsize=13, fontweight="bold")
ax2.set_ylabel("Precio")
ax2.grid(True)

# 🔹 Eje X limpio
step = max(len(x) // 10, 1)
ticks = list(range(0, len(x), step))

ax2.set_xticks(ticks)
ax2.set_xticklabels(
    [x_labels[i].strftime("%Y-%m-%d") for i in ticks],
    rotation=45,
    fontsize=8
)

for ax in [ax1, ax2]:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

plt.tight_layout()
st.pyplot(fig)
