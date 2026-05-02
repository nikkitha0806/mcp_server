"""Portfolio Net Worth Calculator — powered by IBKR live data."""

import sys
import os
import asyncio

# Streamlit runs in a worker thread that has no event loop.
# eventkit (used by ib_insync) grabs the loop at import time, so we must
# create one before the import happens.
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from tools.ibkr import get_portfolio, get_account_value, get_eur_usd_rate

# ---------------------------------------------------------------------------
# Demo data — used when TWS is not running
# ---------------------------------------------------------------------------
DEMO_PORTFOLIO = {
    "as_of": "2025-05-02T12:00:00",
    "total_positions": 6,
    "summary": {
        "total_invested":        42500.00,
        "total_current_value":   48320.50,
        "total_unrealized_pnl":   5820.50,
        "total_unrealized_pnl_pct": 13.69,
    },
    "holdings": [
        {"symbol": "AAPL",  "sec_type": "STK", "currency": "USD", "quantity": 50,  "avg_cost_per_share": 165.00, "invested_value": 8250.00,  "current_price": 189.50, "current_value": 9475.00,  "unrealized_pnl": 1225.00, "unrealized_pnl_pct": 14.85},
        {"symbol": "MSFT",  "sec_type": "STK", "currency": "USD", "quantity": 30,  "avg_cost_per_share": 310.00, "invested_value": 9300.00,  "current_price": 378.90, "current_value": 11367.00, "unrealized_pnl": 2067.00, "unrealized_pnl_pct": 22.23},
        {"symbol": "GOOGL", "sec_type": "STK", "currency": "USD", "quantity": 20,  "avg_cost_per_share": 125.00, "invested_value": 2500.00,  "current_price": 142.30, "current_value": 2846.00,  "unrealized_pnl":  346.00, "unrealized_pnl_pct": 13.84},
        {"symbol": "AMZN",  "sec_type": "STK", "currency": "USD", "quantity": 25,  "avg_cost_per_share": 145.00, "invested_value": 3625.00,  "current_price": 132.10, "current_value": 3302.50,  "unrealized_pnl": -322.50, "unrealized_pnl_pct": -8.90},
        {"symbol": "TLT",   "sec_type": "BOND","currency": "USD", "quantity": 100, "avg_cost_per_share":  92.00, "invested_value": 9200.00,  "current_price":  94.80, "current_value": 9480.00,  "unrealized_pnl":  280.00, "unrealized_pnl_pct":  3.04},
        {"symbol": "BND",   "sec_type": "BOND","currency": "USD", "quantity": 100, "avg_cost_per_share":  76.25, "invested_value": 7625.00,  "current_price":  77.60, "current_value": 7760.00,  "unrealized_pnl":  135.00, "unrealized_pnl_pct":  1.77},
        {"symbol": "NVDA",  "sec_type": "STK", "currency": "USD", "quantity": 15,  "avg_cost_per_share": 450.00, "invested_value": 6750.00,  "current_price": 503.40, "current_value": 7551.00,  "unrealized_pnl":  801.00, "unrealized_pnl_pct": 11.87},
    ],
}
DEMO_ACCOUNT = {
    "as_of": "2025-05-02T12:00:00",
    "account": "DEMO123",
    "net_liquidation_value": 51320.50,
    "total_cash":             3000.00,
    "stock_value":           48320.50,
    "unrealized_pnl":         5820.50,
    "realized_pnl":            420.00,
    "currency": "USD",
}
DEMO_EUR_USD = 1.0842

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Portfolio Net Worth",
    page_icon="📈",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Classify holdings into Equity / Debt / Other
# ---------------------------------------------------------------------------
EQUITY_TYPES = {"STK", "ETF"}
DEBT_TYPES   = {"BOND", "BILL", "FIXED"}

def classify(sec_type: str) -> str:
    s = sec_type.upper()
    if s in EQUITY_TYPES:
        return "Equity"
    if s in DEBT_TYPES:
        return "Debt"
    return "Other"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fmt(value: float) -> str:
    """Format a number as Euro currency string."""
    if value >= 0:
        return f"€{value:,.2f}"
    return f"-€{abs(value):,.2f}"

def _pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"

def _to_eur(value: float, rate: float) -> float:
    """Convert a USD value to EUR using the EUR/USD rate."""
    return value / rate

# ---------------------------------------------------------------------------
# Load data (cached for 60 s so refresh doesn't hammer IBKR)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_data() -> tuple[dict, dict, float, bool]:
    """Returns (portfolio, account, eur_usd_rate, is_demo)."""
    try:
        portfolio = get_portfolio()
        account   = get_account_value()
        eur_usd   = get_eur_usd_rate()
        return portfolio, account, eur_usd, False
    except Exception:
        return DEMO_PORTFOLIO, DEMO_ACCOUNT, DEMO_EUR_USD, True

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("📈 Portfolio Net Worth")
st.caption("Live data from Interactive Brokers · all values in Euro · refreshes every 60 seconds")

col_refresh, col_time = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# ── Load ────────────────────────────────────────────────────────────────────
with st.spinner("Connecting to IBKR..."):
    portfolio, account, eur_usd_rate, is_demo = load_data()

if is_demo:
    st.warning(
        "⚠️ TWS is not reachable on port 7497 — showing **demo data**. "
        "Start TWS and click 🔄 Refresh to load your live portfolio.",
        icon="⚠️",
    )

with col_time:
    label = "Demo" if is_demo else "Live"
    st.caption(f"{label} · As of {portfolio['as_of']} · EUR/USD: {eur_usd_rate:.4f}")

holdings = portfolio["holdings"]
summary  = portfolio["summary"]

if not holdings:
    st.warning("No positions found in your account.")
    st.stop()

# ── Convert all monetary values USD → EUR ───────────────────────────────────
r = eur_usd_rate

df = pd.DataFrame(holdings)
df["category"]         = df["sec_type"].apply(classify)
df["invested_value"]   = df["invested_value"].apply(lambda v: _to_eur(v, r))
df["current_value"]    = df["current_value"].apply(lambda v: _to_eur(v, r))
df["unrealized_pnl"]   = df["unrealized_pnl"].apply(lambda v: _to_eur(v, r))
df["avg_cost_per_share"]= df["avg_cost_per_share"].apply(lambda v: _to_eur(v, r))
df["current_price"]    = df["current_price"].apply(lambda v: _to_eur(v, r))

# ── Top metrics ─────────────────────────────────────────────────────────────
st.markdown("---")
m1, m2, m3, m4, m5 = st.columns(5)

net_liq       = _to_eur(account["net_liquidation_value"], r)
total_stocks  = _to_eur(account["stock_value"],           r)
total_cash    = _to_eur(account["total_cash"],            r)
total_invested= _to_eur(summary["total_invested"],        r)
total_pnl     = _to_eur(summary["total_unrealized_pnl"],  r)
total_pnl_pct = summary["total_unrealized_pnl_pct"]       # % is currency-neutral

m1.metric("Net Worth",      _fmt(net_liq))
m2.metric("Stock Value",    _fmt(total_stocks))
m3.metric("Cash",           _fmt(total_cash))
m4.metric("Total Invested", _fmt(total_invested))
m5.metric("Unrealized P&L", _fmt(total_pnl), delta=_pct(total_pnl_pct))

st.markdown("---")

# ── Equity vs Debt breakdown ─────────────────────────────────────────────────
st.subheader("Equity vs Debt Allocation")

equity_val = df[df["category"] == "Equity"]["current_value"].sum()
debt_val   = df[df["category"] == "Debt"]["current_value"].sum()
other_val  = df[df["category"] == "Other"]["current_value"].sum()
equity_inv = df[df["category"] == "Equity"]["invested_value"].sum()
debt_inv   = df[df["category"] == "Debt"]["invested_value"].sum()

cat_labels, cat_current, cat_invested = [], [], []
for label, cur, inv in [("Equity", equity_val, equity_inv),
                         ("Debt",   debt_val,   debt_inv),
                         ("Other",  other_val,  0)]:
    if cur > 0:
        cat_labels.append(label)
        cat_current.append(cur)
        cat_invested.append(inv)

left, right = st.columns(2)

# Donut chart — current allocation
with left:
    fig_donut = go.Figure(go.Pie(
        labels=cat_labels,
        values=cat_current,
        hole=0.55,
        marker_colors=["#3b82f6", "#f59e0b", "#8b5cf6"],
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Current Value: €%{value:,.2f}<extra></extra>",
    ))
    fig_donut.update_layout(
        title="Current Value Allocation",
        showlegend=False,
        height=320,
        margin=dict(t=40, b=0, l=0, r=0),
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# Bar chart — invested vs current per category
with right:
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Invested",
        x=cat_labels,
        y=cat_invested,
        marker_color="#94a3b8",
        text=[_fmt(v) for v in cat_invested],
        textposition="outside",
    ))
    fig_bar.add_trace(go.Bar(
        name="Current Value",
        x=cat_labels,
        y=cat_current,
        marker_color=["#3b82f6", "#f59e0b", "#8b5cf6"][:len(cat_labels)],
        text=[_fmt(v) for v in cat_current],
        textposition="outside",
    ))
    fig_bar.update_layout(
        title="Invested vs Current Value",
        barmode="group",
        height=320,
        margin=dict(t=40, b=0, l=0, r=0),
        legend=dict(orientation="h", y=-0.15),
        yaxis_tickprefix="€",
        yaxis_tickformat=",.0f",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Equity / Debt summary cards ──────────────────────────────────────────────
c1, c2 = st.columns(2)
for col, label, cur, inv in [(c1, "Equity", equity_val, equity_inv),
                               (c2, "Debt",   debt_val,   debt_inv)]:
    pnl = cur - inv
    pnl_pct = (pnl / inv * 100) if inv else 0.0
    with col:
        st.markdown(f"### {label}")
        a, b, c = st.columns(3)
        a.metric("Invested",      _fmt(inv))
        b.metric("Current Value", _fmt(cur))
        c.metric("P&L",           _fmt(pnl), delta=_pct(pnl_pct))

st.markdown("---")

# ── Holdings table ───────────────────────────────────────────────────────────
st.subheader("Holdings")

tab_all, tab_equity, tab_debt = st.tabs(["All", "Equity", "Debt"])

def render_table(data: pd.DataFrame):
    if data.empty:
        st.info("No holdings in this category.")
        return

    display = data[[
        "symbol", "category", "quantity",
        "avg_cost_per_share", "invested_value",
        "current_price", "current_value",
        "unrealized_pnl", "unrealized_pnl_pct",
    ]].copy()

    display.columns = [
        "Symbol", "Type", "Quantity",
        "Avg Cost (€)", "Invested (€)",
        "Current Price (€)", "Current Value (€)",
        "Unrealized P&L (€)", "P&L %",
    ]

    def style_pnl(val):
        color = "green" if val >= 0 else "red"
        return f"color: {color}; font-weight: bold"

    styled = (
        display.style
        .map(style_pnl, subset=["Unrealized P&L (€)", "P&L %"])
        .format({
            "Avg Cost (€)":        "€{:,.4f}",
            "Invested (€)":        "€{:,.2f}",
            "Current Price (€)":   "€{:,.4f}",
            "Current Value (€)":   "€{:,.2f}",
            "Unrealized P&L (€)":  "€{:,.2f}",
            "P&L %":               "{:+.2f}%",
            "Quantity":            "{:,.0f}",
        })
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

with tab_all:
    render_table(df)
with tab_equity:
    render_table(df[df["category"] == "Equity"])
with tab_debt:
    render_table(df[df["category"] == "Debt"])

# ── Per-stock bar chart ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Current Value per Stock")

fig_stocks = px.bar(
    df.sort_values("current_value", ascending=True),
    x="current_value",
    y="symbol",
    color="category",
    orientation="h",
    text="current_value",
    color_discrete_map={"Equity": "#3b82f6", "Debt": "#f59e0b", "Other": "#8b5cf6"},
    labels={"current_value": "Current Value (€)", "symbol": ""},
)
fig_stocks.update_traces(texttemplate="€%{text:,.0f}", textposition="outside")
fig_stocks.update_layout(
    height=max(300, len(df) * 40),
    margin=dict(t=20, b=0, l=0, r=80),
    xaxis_tickprefix="€",
    xaxis_tickformat=",.0f",
    legend_title="",
)
st.plotly_chart(fig_stocks, use_container_width=True)
