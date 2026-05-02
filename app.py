"""Portfolio Net Worth Calculator — multi-account, powered by IBKR live data."""

import sys
import os
import asyncio

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from tools.ibkr import get_all_portfolios, get_all_account_values, _get_connections

# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------
DEMO_DATA = {
    "as_of": "2025-05-02T12:00:00",
    "accounts": ["U111111", "U222222"],
    "per_account": {
        "U111111": {
            "account": "U111111", "account_label": "U···111",
            "total_invested": 26250.00, "total_current_value": 30239.00,
            "total_unrealized_pnl": 3989.00, "total_unrealized_pnl_pct": 15.20,
            "holdings": [
                {"account": "U111111", "account_label": "U···111", "symbol": "AAPL",  "sec_type": "STK", "currency": "USD", "quantity": 50,  "avg_cost_per_share": 165.00, "invested_value": 8250.00,  "current_price": 189.50, "current_value": 9475.00,  "unrealized_pnl": 1225.00, "unrealized_pnl_pct": 14.85},
                {"account": "U111111", "account_label": "U···111", "symbol": "MSFT",  "sec_type": "STK", "currency": "USD", "quantity": 30,  "avg_cost_per_share": 310.00, "invested_value": 9300.00,  "current_price": 378.90, "current_value": 11367.00, "unrealized_pnl": 2067.00, "unrealized_pnl_pct": 22.23},
                {"account": "U111111", "account_label": "U···111", "symbol": "NVDA",  "sec_type": "STK", "currency": "USD", "quantity": 15,  "avg_cost_per_share": 450.00, "invested_value": 6750.00,  "current_price": 503.40, "current_value": 7551.00,  "unrealized_pnl":  801.00, "unrealized_pnl_pct": 11.87},
                {"account": "U111111", "account_label": "U···111", "symbol": "XEON",  "sec_type": "BOND","currency": "USD", "quantity": 25,  "avg_cost_per_share":  77.00, "invested_value": 1950.00,  "current_price":  75.06, "current_value": 1846.00,  "unrealized_pnl": -104.00, "unrealized_pnl_pct": -5.33},
            ],
        },
        "U222222": {
            "account": "U222222", "account_label": "U···222",
            "total_invested": 24625.00, "total_current_value": 26831.50,
            "total_unrealized_pnl": 2206.50, "total_unrealized_pnl_pct": 8.96,
            "holdings": [
                {"account": "U222222", "account_label": "U···222", "symbol": "GOOGL", "sec_type": "STK", "currency": "USD", "quantity": 20,  "avg_cost_per_share": 125.00, "invested_value": 2500.00,  "current_price": 142.30, "current_value": 2846.00,  "unrealized_pnl":  346.00, "unrealized_pnl_pct": 13.84},
                {"account": "U222222", "account_label": "U···222", "symbol": "AMZN",  "sec_type": "STK", "currency": "USD", "quantity": 25,  "avg_cost_per_share": 145.00, "invested_value": 3625.00,  "current_price": 132.10, "current_value": 3302.50,  "unrealized_pnl": -322.50, "unrealized_pnl_pct": -8.90},
                {"account": "U222222", "account_label": "U···222", "symbol": "MSFT",  "sec_type": "STK", "currency": "USD", "quantity": 20,  "avg_cost_per_share": 290.00, "invested_value": 5800.00,  "current_price": 378.90, "current_value": 7578.00,  "unrealized_pnl": 1778.00, "unrealized_pnl_pct": 30.65},
                {"account": "U222222", "account_label": "U···222", "symbol": "TLT",   "sec_type": "BOND","currency": "USD", "quantity": 100, "avg_cost_per_share":  92.00, "invested_value": 9200.00,  "current_price":  94.80, "current_value": 9480.00,  "unrealized_pnl":  280.00, "unrealized_pnl_pct":  3.04},
                {"account": "U222222", "account_label": "U···222", "symbol": "BND",   "sec_type": "BOND","currency": "USD", "quantity": 50,  "avg_cost_per_share":  76.25, "invested_value": 3812.50,  "current_price":  77.60, "current_value": 3880.00,  "unrealized_pnl":   67.50, "unrealized_pnl_pct":  1.77},
                {"account": "U222222", "account_label": "U···222", "symbol": "XEON",  "sec_type": "BOND","currency": "USD", "quantity": 10,  "avg_cost_per_share":  77.00, "invested_value":  687.50,  "current_price":  74.50, "current_value":  745.00,  "unrealized_pnl":   57.50, "unrealized_pnl_pct":  8.36},
            ],
        },
    },
    "combined": {
        "total_invested": 50875.00, "total_current_value": 57070.50,
        "total_unrealized_pnl": 6195.50, "total_unrealized_pnl_pct": 12.18,
        "holdings": [
            {"account": "combined", "account_label": "Combined", "symbol": "MSFT",  "sec_type": "STK", "currency": "USD", "quantity": 50,  "avg_cost_per_share": 302.00, "invested_value": 15100.00, "current_price": 378.90, "current_value": 18945.00, "unrealized_pnl": 3845.00, "unrealized_pnl_pct": 25.46},
            {"account": "combined", "account_label": "Combined", "symbol": "AAPL",  "sec_type": "STK", "currency": "USD", "quantity": 50,  "avg_cost_per_share": 165.00, "invested_value":  8250.00, "current_price": 189.50, "current_value":  9475.00, "unrealized_pnl": 1225.00, "unrealized_pnl_pct": 14.85},
            {"account": "combined", "account_label": "Combined", "symbol": "TLT",   "sec_type": "BOND","currency": "USD", "quantity": 100, "avg_cost_per_share":  92.00, "invested_value":  9200.00, "current_price":  94.80, "current_value":  9480.00, "unrealized_pnl":  280.00, "unrealized_pnl_pct":  3.04},
            {"account": "combined", "account_label": "Combined", "symbol": "NVDA",  "sec_type": "STK", "currency": "USD", "quantity": 15,  "avg_cost_per_share": 450.00, "invested_value":  6750.00, "current_price": 503.40, "current_value":  7551.00, "unrealized_pnl":  801.00, "unrealized_pnl_pct": 11.87},
            {"account": "combined", "account_label": "Combined", "symbol": "GOOGL", "sec_type": "STK", "currency": "USD", "quantity": 20,  "avg_cost_per_share": 125.00, "invested_value":  2500.00, "current_price": 142.30, "current_value":  2846.00, "unrealized_pnl":  346.00, "unrealized_pnl_pct": 13.84},
            {"account": "combined", "account_label": "Combined", "symbol": "AMZN",  "sec_type": "STK", "currency": "USD", "quantity": 25,  "avg_cost_per_share": 145.00, "invested_value":  3625.00, "current_price": 132.10, "current_value":  3302.50, "unrealized_pnl": -322.50, "unrealized_pnl_pct": -8.90},
            {"account": "combined", "account_label": "Combined", "symbol": "XEON",  "sec_type": "BOND","currency": "USD", "quantity": 35,  "avg_cost_per_share":  77.00, "invested_value":  2637.50, "current_price":  74.79, "current_value":  2618.00, "unrealized_pnl":  -19.50, "unrealized_pnl_pct": -0.74},
            {"account": "combined", "account_label": "Combined", "symbol": "BND",   "sec_type": "BOND","currency": "USD", "quantity": 50,  "avg_cost_per_share":  76.25, "invested_value":  3812.50, "current_price":  77.60, "current_value":  3880.00, "unrealized_pnl":   67.50, "unrealized_pnl_pct":  1.77},
        ],
    },
}
DEMO_ACCOUNTS = {
    "as_of": "2025-05-02T12:00:00",
    "per_account": [
        {"account": "U111111", "account_label": "U···111", "net_liquidation_value": 32239.00, "total_cash": 2000.00, "stock_value": 30239.00, "unrealized_pnl": 3989.00, "realized_pnl": 200.00, "currency": "USD"},
        {"account": "U222222", "account_label": "U···222", "net_liquidation_value": 27831.50, "total_cash": 1000.00, "stock_value": 26831.50, "unrealized_pnl": 2206.50, "realized_pnl": 150.00, "currency": "USD"},
    ],
    "combined": {"net_liquidation_value": 60070.50, "total_cash": 3000.00, "stock_value": 57070.50, "unrealized_pnl": 6195.50, "realized_pnl": 350.00},
}

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Portfolio Net Worth", page_icon="📈", layout="wide")

# ---------------------------------------------------------------------------
# Classify holdings
# ---------------------------------------------------------------------------
EQUITY_TYPES = {"STK", "ETF"}
DEBT_TYPES   = {"BOND", "BILL", "FIXED"}
SYMBOL_OVERRIDES: dict[str, str] = {"XEON": "Debt"}

def classify(symbol: str, sec_type: str) -> str:
    if symbol.upper() in SYMBOL_OVERRIDES:
        return SYMBOL_OVERRIDES[symbol.upper()]
    return "Equity" if sec_type.upper() in EQUITY_TYPES else "Debt" if sec_type.upper() in DEBT_TYPES else "Equity"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fmt(v: float) -> str:
    return f"${v:,.2f}" if v >= 0 else f"-${abs(v):,.2f}"

def _pct(v: float) -> str:
    return f"+{v:.2f}%" if v >= 0 else f"{v:.2f}%"

def _to_df(holdings: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(holdings)
    df["category"] = df.apply(lambda r: classify(r["symbol"], r["sec_type"]), axis=1)
    return df

# ---------------------------------------------------------------------------
# Connections — cached as a resource so one connection is made per server
# lifetime, not on every page reload.
# ---------------------------------------------------------------------------
@st.cache_resource
def _init_connections():
    return _get_connections()

# ---------------------------------------------------------------------------
# Load data — fetches fresh portfolio data using the cached connections
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_data() -> tuple[dict, dict, bool, str]:
    try:
        _init_connections()          # ensure connection is alive before fetching
        return get_all_portfolios(), get_all_account_values(), False, ""
    except Exception as e:
        return DEMO_DATA, DEMO_ACCOUNTS, True, str(e)

# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------
def render_metrics(summary: dict, account_data: dict):
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Net Worth",      _fmt(account_data["net_liquidation_value"]))
    m2.metric("Stock Value",    _fmt(account_data["stock_value"]))
    m3.metric("Cash",           _fmt(account_data["total_cash"]))
    m4.metric("Total Invested", _fmt(summary["total_invested"]))
    m5.metric("Unrealized P&L", _fmt(summary["total_unrealized_pnl"]),
              delta=_pct(summary["total_unrealized_pnl_pct"]))

def render_allocation(df: pd.DataFrame):
    equity_val = df[df["category"] == "Equity"]["current_value"].sum()
    debt_val   = df[df["category"] == "Debt"]["current_value"].sum()
    equity_inv = df[df["category"] == "Equity"]["invested_value"].sum()
    debt_inv   = df[df["category"] == "Debt"]["invested_value"].sum()

    cat_labels, cat_current, cat_invested = [], [], []
    for label, cur, inv in [("Equity", equity_val, equity_inv), ("Debt", debt_val, debt_inv)]:
        if cur > 0:
            cat_labels.append(label); cat_current.append(cur); cat_invested.append(inv)

    left, right = st.columns(2)
    with left:
        fig = go.Figure(go.Pie(
            labels=cat_labels, values=cat_current, hole=0.55,
            marker_colors=["#3b82f6", "#f59e0b"],
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>",
        ))
        fig.update_layout(title="Allocation", showlegend=False, height=300, margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Invested",      x=cat_labels, y=cat_invested,
                              marker_color="#94a3b8", text=[_fmt(v) for v in cat_invested], textposition="outside"))
        fig2.add_trace(go.Bar(name="Current Value", x=cat_labels, y=cat_current,
                              marker_color=["#3b82f6","#f59e0b"][:len(cat_labels)],
                              text=[_fmt(v) for v in cat_current], textposition="outside"))
        fig2.update_layout(title="Invested vs Current", barmode="group", height=300,
                           margin=dict(t=40,b=0,l=0,r=0), legend=dict(orientation="h",y=-0.2),
                           yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig2, use_container_width=True)

    c1, c2 = st.columns(2)
    for col, label, cur, inv in [(c1,"Equity",equity_val,equity_inv),(c2,"Debt",debt_val,debt_inv)]:
        pnl = cur - inv
        with col:
            st.markdown(f"**{label}**")
            a, b, c = st.columns(3)
            a.metric("Invested",      _fmt(inv))
            b.metric("Current Value", _fmt(cur))
            c.metric("P&L",           _fmt(pnl), delta=_pct((pnl/inv*100) if inv else 0))

def render_table(df: pd.DataFrame):
    if df.empty:
        st.info("No holdings.")
        return
    cols_in  = ["symbol","category","quantity","avg_cost_per_share","invested_value",
                "current_price","current_value","unrealized_pnl","unrealized_pnl_pct"]
    cols_out = ["Symbol","Type","Qty","Avg Cost","Invested ($)",
                "Price ($)","Current Value ($)","P&L ($)","P&L %"]
    display = df[cols_in].copy()
    display.columns = cols_out
    def _style(v):
        return f"color:{'green' if v>=0 else 'red'};font-weight:bold"
    styled = (display.style
        .map(_style, subset=["P&L ($)","P&L %"])
        .format({"Avg Cost":"${:,.4f}","Invested ($)":"${:,.2f}","Price ($)":"${:,.4f}",
                 "Current Value ($)":"${:,.2f}","P&L ($)":"${:,.2f}","P&L %":"{:+.2f}%","Qty":"{:,.0f}"}))
    st.dataframe(styled, use_container_width=True, hide_index=True)

def render_bar_chart(df: pd.DataFrame):
    fig = px.bar(df.sort_values("current_value", ascending=True),
                 x="current_value", y="symbol", color="category", orientation="h",
                 text="current_value",
                 color_discrete_map={"Equity":"#3b82f6","Debt":"#f59e0b"},
                 labels={"current_value":"Current Value ($)","symbol":""})
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(height=max(300, len(df)*40), margin=dict(t=20,b=0,l=0,r=80),
                      xaxis_tickprefix="$", xaxis_tickformat=",.0f", legend_title="")
    st.plotly_chart(fig, use_container_width=True)

def render_account_view(summary: dict, account_data: dict, holdings: list[dict]):
    df = _to_df(holdings)
    render_metrics(summary, account_data)
    st.markdown("---")
    render_allocation(df)
    st.markdown("---")
    t1, t2, t3 = st.tabs(["All Holdings", "Equity", "Debt"])
    with t1: render_table(df)
    with t2: render_table(df[df["category"]=="Equity"])
    with t3: render_table(df[df["category"]=="Debt"])
    st.markdown("---")
    render_bar_chart(df)

# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------
st.title("📈 Portfolio Net Worth")
st.caption("Live data from Interactive Brokers · USD · refreshes every 60 seconds")

col_refresh, col_time = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

with st.spinner("Connecting to IBKR..."):
    portfolio_data, account_data, is_demo, conn_error = load_data()

if is_demo:
    st.warning("⚠️ Showing **demo data** — could not connect to IBKR. Start TWS and click 🔄 Refresh.")
    with st.expander("🔍 Connection error details"):
        st.code(conn_error or "Unknown error")
        st.markdown("**Common causes:**\n"
                    "- TWS is not running\n"
                    "- API not enabled: TWS → Edit → Global Configuration → API → Settings → ✅ Enable ActiveX and Socket Clients\n"
                    "- Wrong port: confirm `7497` (paper) or `7496` (live)\n"
                    "- Restart TWS after enabling the API")

with col_time:
    st.caption(f"{'Demo' if is_demo else 'Live'} · As of {portfolio_data['as_of']}")

accounts      = portfolio_data["accounts"]
per_account   = portfolio_data["per_account"]
combined      = portfolio_data["combined"]
acct_combined = account_data["combined"]
acct_per      = {a["account"]: a for a in account_data["per_account"]}

# ── Account tabs: Combined + one per account ─────────────────────────────────
tab_labels = ["Combined"] + [per_account[a]["account_label"] for a in accounts]
tabs = st.tabs(tab_labels)

with tabs[0]:
    render_account_view(
        summary      = combined,
        account_data = acct_combined,
        holdings     = combined["holdings"],
    )

for i, acct_id in enumerate(accounts):
    with tabs[i + 1]:
        acct_summary = per_account[acct_id]
        acct_values  = acct_per.get(acct_id, acct_combined)
        render_account_view(
            summary      = acct_summary,
            account_data = acct_values,
            holdings     = acct_summary["holdings"],
        )
