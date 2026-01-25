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

ref_ticker = st.selectbox(
    "Elegí un ticker para ver precio absoluto",
    options=tickers,
    index=0
)

# 📅 Fechas
today = datetime.date.today()

if "start_date" not in st.session_state:
    st.session_state.start_date = datetime.date(2020, 1, 1)

if "end_date" not in st.session_state:
    st.session_state.end_date = today

st.subheader("⏱️ Período rápido")

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

# 📅 Fechas (SIEMPRE editables)
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Fecha inicio", key="start_date")

with col2:
    end_date = st.date_input("Fecha fin", key="end_date")

if start_date >= end_date:
    st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
    st.stop()

# ⚙️ Opciones de visualización
scale = st.radio("Escala del gráfico", ["Lineal", "Logarítmica"], horizontal=True)

days_range = (end_date - start_date).days
if days_range <= 7:
    interval = "1h"
elif days_range <= 60:
    interval = "1d"
else:
    interval = "1d"


@st.cache_data
def load_data(tickers, start, end):
    days_range = (end - start).days

    if days_range <= 7:
        interval = "1h"
    elif days_range <= 60:
        interval = "1d"
    else:
        interval = "1d"

    raw = yf.download(
        tickers,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,
        progress=False,
        group_by="ticker"
    )

    if len(tickers) == 1:
        df = raw["Close"].to_frame(tickers[0])
    else:
        df = raw.xs("Close", axis=1, level=1)

    df = df.dropna(axis=1, how="all")
    return df

data = load_data(tickers, start_date, end_date)

if data.empty or data.shape[1] == 0:
    st.warning("No hay datos válidos para los tickers seleccionados.")
    st.stop()

# 📊 Normalización base 100
norm = pd.DataFrame(index=data.index)

for col in data.columns:
    first_valid = data[col].dropna().iloc[0]
    norm[col] = data[col] / first_valid * 100

series = data[ref_ticker].dropna()

first_price = series.iloc[0]
last_price = series.iloc[-1]
first_date = series.index[0]
last_date = series.index[-1]

pct_change = (last_price / first_price - 1) * 100
col1, col2, col3 = st.columns(3)

col1.metric(
    label=f"{ref_ticker} – Último precio",
    value=f"{last_price:.2f}"
)

col2.metric(
    label="Cambio en el período",
    value=f"{pct_change:+.2f} %"
)

col3.caption(
    f"Desde {first_date.strftime('%Y-%m-%d')} "
    f"hasta {last_date.strftime('%Y-%m-%d')}"
)


# 📊 Graficos
st.subheader("📊 Evolución de mercado")

fig, (ax1, ax2) = plt.subplots(
    2, 1,
    figsize=(11, 7),
    sharex=True
)

norm.plot(ax=ax1, linewidth=2)
ax1.set_title("Desempeño relativo (Base = 100)")
ax1.set_ylabel("Índice")
ax1.grid(True, alpha=0.3)

if scale == "Logarítmica":
    ax1.set_yscale("log")

series = data[ref_ticker].dropna()
series.plot(ax=ax2, linewidth=2, color="black", label=ref_ticker)

last_date = series.index[-1]
last_price = series.iloc[-1]
pct_change = (last_price / series.iloc[0] - 1) * 100

ax2.scatter(last_date, last_price, s=60, zorder=3)

ax2.annotate(
    f"{last_price:.2f}\n({pct_change:+.2f}%)",
    xy=(last_date, last_price),
    xytext=(10, 10),
    textcoords="offset points",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8)
)

ax2.set_title(f"Precio absoluto – {ref_ticker}")
ax2.set_ylabel("Precio")
ax2.grid(True, alpha=0.3)
ax2.legend()

# 🕒 Formato dinámico del eje X
days_range = (end_date - start_date).days

if days_range <= 3:
    locator = mdates.HourLocator(interval=1)
    formatter = mdates.DateFormatter("%d-%m %H:%M")

elif days_range <= 7:
    locator = mdates.HourLocator(interval=3)
    formatter = mdates.DateFormatter("%d-%m %H:%M")

elif days_range <= 30:
    locator = mdates.DayLocator(interval=1)
    formatter = mdates.DateFormatter("%d-%m")

elif days_range <= 180:
    locator = mdates.DayLocator(interval=7)
    formatter = mdates.DateFormatter("%d-%m")

else:
    locator = mdates.MonthLocator(interval=1)
    formatter = mdates.DateFormatter("%m-%Y")

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

# 📋 Tabla resumen
st.subheader("📋 Rendimiento acumulado")
returns = (norm.iloc[-1] - 100).sort_values(ascending=False)
st.dataframe(
    returns.to_frame("Retorno %")
    .style.format("{:.2f}")
    .background_gradient(cmap="RdYlGn")
)
import numpy as np

st.subheader("📌 Snapshot de mercado (corto plazo)")

snapshot = []

for col in data.columns:
    prices = data[col].dropna()

    if len(prices) < 2:
        continue

    last = prices.iloc[-1]
    prev_1d = prices.iloc[-2]
    prev_5d = prices.iloc[-6] if len(prices) > 5 else np.nan
    prev_20d = prices.iloc[-21] if len(prices) > 20 else np.nan

    snapshot.append({
        "Ticker": col,
        "Precio actual": last,
        "Día %": (last / prev_1d - 1) * 100,
        "5 días %": (last / prev_5d - 1) * 100 if not np.isnan(prev_5d) else np.nan,
        "20 días %": (last / prev_20d - 1) * 100 if not np.isnan(prev_20d) else np.nan
    })

df_snapshot = pd.DataFrame(snapshot).set_index("Ticker")

st.dataframe(
    df_snapshot.style
    .format({
        "Precio actual": "{:.2f}",
        "Día %": "{:+.2f}",
        "5 días %": "{:+.2f}",
        "20 días %": "{:+.2f}"
    })
    .background_gradient(cmap="RdYlGn", subset=["Día %", "5 días %", "20 días %"])
)
st.subheader("📋 Métricas financieras (análisis profundo)")

# Retornos
returns_daily = data.pct_change().dropna()
returns_monthly = data.resample("M").last().pct_change().dropna()

# Benchmark
spy = yf.download(
    "SPY",
    start=start_date,
    end=end_date,
    auto_adjust=True,
    progress=False
)["Close"]

spy_ret = spy.pct_change().dropna()

stats = {}

for col in data.columns:
    r = returns_daily[col].dropna()
    rm = returns_monthly[col].dropna()

    if len(r) < 50:
        continue

    # Retorno total
    total_return = (data[col].iloc[-1] / data[col].iloc[0] - 1) * 100

    # CAGR
    years = (data.index[-1] - data.index[0]).days / 365.25
    cagr = ((data[col].iloc[-1] / data[col].iloc[0]) ** (1 / years) - 1) * 100

    # Volatilidad
    vol = r.std() * np.sqrt(252) * 100

    # Drawdown
    cum = (1 + r).cumprod()
    dd = (cum / cum.cummax() - 1).min() * 100

    # Sharpe (rf = 0)
    sharpe = (r.mean() / r.std()) * np.sqrt(252)

    # Beta vs SPY
    aligned = pd.concat([r, spy_ret], axis=1).dropna()
    beta = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0][1] / aligned.iloc[:, 1].var()

    stats[col] = {
        "Retorno total %": total_return,
        "CAGR %": cagr,
        "Volatilidad %": vol,
        "Max Drawdown %": dd,
        "Sharpe": sharpe,
        "Beta SPY": beta,
        "% Meses +": (rm > 0).mean() * 100,
        "Mejor mes %": rm.max() * 100,
        "Peor mes %": rm.min() * 100
    }

df_stats = (
    pd.DataFrame(stats).T
    .sort_values("CAGR %", ascending=False)
)

st.dataframe(
    df_stats.style
    .format("{:.2f}")
    .background_gradient(cmap="RdYlGn", subset=["CAGR %", "Sharpe"])
    .background_gradient(cmap="Reds", subset=["Max Drawdown %"])
)
