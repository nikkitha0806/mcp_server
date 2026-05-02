"""Interactive Brokers multi-account portfolio tracker using ib_insync.

Supports two scenarios:
  A) Same TWS login  — both accounts visible under one TWS (e.g. individual + IRA).
     ib.managedAccounts() returns all account IDs automatically.
     Override which accounts to use: IBKR_ACCOUNTS=U111111,U222222

  B) Two separate TWS instances on different ports.
     Set IBKR_PORT_2 (and optionally IBKR_HOST_2) for the second TWS.

Connection env vars:
  IBKR_HOST        default: 127.0.0.1
  IBKR_PORT        default: 7497
  IBKR_CLIENT_ID   default: 10  (auto-increments to find a free ID)
  IBKR_ACCOUNTS    default: all managed accounts (comma-separated to filter)
  IBKR_HOST_2      default: same as IBKR_HOST   (second TWS, optional)
  IBKR_PORT_2      default: unset               (if set, connects a second TWS)
"""

import os
from datetime import datetime

from ib_insync import IB, util

# ── Primary connection ────────────────────────────────────────────────────────
IBKR_HOST      = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT      = int(os.getenv("IBKR_PORT", "7497"))
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "10"))
IBKR_ACCOUNTS  = os.getenv("IBKR_ACCOUNTS", "")   # optional comma-separated filter

# ── Secondary connection (optional second TWS) ────────────────────────────────
IBKR_HOST_2    = os.getenv("IBKR_HOST_2", IBKR_HOST)
IBKR_PORT_2    = int(os.getenv("IBKR_PORT_2", "0"))   # 0 = not configured

_connections: dict[str, IB] = {}   # key = "host:port"


def _connect(host: str, port: int, base_client_id: int) -> IB:
    """Connect to a TWS instance, auto-retrying client IDs until one is free."""
    util.startLoop()
    key = f"{host}:{port}"
    ib = _connections.get(key)
    if ib and ib.isConnected():
        return ib

    last_error = None
    for client_id in range(base_client_id, base_client_id + 10):
        try:
            ib = IB()
            ib.connect(host, port, clientId=client_id, readonly=True, timeout=10)
            _connections[key] = ib
            return ib
        except Exception as e:
            last_error = e
            continue

    raise ConnectionError(
        f"Could not connect to TWS on {host}:{port} — "
        f"all client IDs {base_client_id}–{base_client_id+9} in use. "
        f"Last error: {last_error}"
    )


def _get_connections() -> list[IB]:
    """Return list of active IB connections (1 or 2 depending on config)."""
    connections = [_connect(IBKR_HOST, IBKR_PORT, IBKR_CLIENT_ID)]
    if IBKR_PORT_2:
        connections.append(_connect(IBKR_HOST_2, IBKR_PORT_2, IBKR_CLIENT_ID + 20))
    return connections


def _account_label(account_id: str) -> str:
    """Shorten account ID for display: U1234567 → U···567"""
    if len(account_id) > 6:
        return f"{account_id[:1]}···{account_id[-3:]}"
    return account_id


def _portfolio_items_for(ib: IB, account_id: str) -> list[dict]:
    """Fetch portfolio items for a single account on a single connection."""
    items = ib.portfolio(account=account_id)
    holdings = []
    for item in items:
        c = item.contract
        quantity     = item.position
        avg_cost     = item.averageCost
        current_price= item.marketPrice
        current_value= item.marketValue
        invested_value = round(quantity * avg_cost, 2)
        unrealized_pnl = item.unrealizedPNL
        pnl_pct = round((unrealized_pnl / invested_value) * 100, 2) if invested_value else 0.0
        holdings.append({
            "account":            account_id,
            "account_label":      _account_label(account_id),
            "symbol":             c.symbol,
            "sec_type":           c.secType,
            "currency":           c.currency,
            "quantity":           quantity,
            "avg_cost_per_share": round(avg_cost, 4),
            "invested_value":     invested_value,
            "current_price":      round(current_price, 4),
            "current_value":      round(current_value, 2),
            "unrealized_pnl":     round(unrealized_pnl, 2),
            "unrealized_pnl_pct": pnl_pct,
        })
    return holdings


def _account_summary_for(ib: IB, account_id: str) -> dict:
    """Fetch account summary for a single account."""
    tags = {
        item.tag: item.value
        for item in ib.accountSummary(account=account_id)
        if item.account == account_id
    }

    def _f(key: str) -> float:
        try:
            return round(float(tags.get(key, 0)), 2)
        except ValueError:
            return 0.0

    return {
        "account":              account_id,
        "account_label":        _account_label(account_id),
        "net_liquidation_value":_f("NetLiquidation"),
        "total_cash":           _f("TotalCashValue"),
        "stock_value":          _f("StockMarketValue"),
        "unrealized_pnl":       _f("UnrealizedPnL"),
        "realized_pnl":         _f("RealizedPnL"),
        "currency":             tags.get("Currency", "USD"),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_all_portfolios() -> dict:
    """
    Fetch portfolio holdings from all configured accounts across all connections.
    Returns per-account holdings plus a combined aggregate view.
    """
    all_holdings: list[dict] = []
    accounts_seen: list[str] = []

    for ib in _get_connections():
        managed = ib.managedAccounts()
        # Apply account filter if set
        if IBKR_ACCOUNTS:
            filter_ids = [a.strip() for a in IBKR_ACCOUNTS.split(",")]
            managed = [a for a in managed if a in filter_ids]

        for acct in managed:
            if acct not in accounts_seen:
                accounts_seen.append(acct)
            all_holdings.extend(_portfolio_items_for(ib, acct))

    # ── Per-account summaries ────────────────────────────────────────────────
    per_account: dict[str, dict] = {}
    for acct in accounts_seen:
        acct_holdings = [h for h in all_holdings if h["account"] == acct]
        invested = sum(h["invested_value"] for h in acct_holdings)
        current  = sum(h["current_value"]  for h in acct_holdings)
        pnl      = round(current - invested, 2)
        per_account[acct] = {
            "account":       acct,
            "account_label": _account_label(acct),
            "total_invested":      round(invested, 2),
            "total_current_value": round(current, 2),
            "total_unrealized_pnl":pnl,
            "total_unrealized_pnl_pct": round((pnl / invested * 100), 2) if invested else 0.0,
            "holdings": sorted(acct_holdings, key=lambda x: x["current_value"], reverse=True),
        }

    # ── Combined aggregate ───────────────────────────────────────────────────
    combined_map: dict[str, dict] = {}
    for h in all_holdings:
        sym = h["symbol"]
        if sym not in combined_map:
            combined_map[sym] = {**h, "account": "combined", "account_label": "Combined"}
        else:
            existing = combined_map[sym]
            new_qty   = existing["quantity"] + h["quantity"]
            new_inv   = existing["invested_value"] + h["invested_value"]
            new_cur   = existing["current_value"]  + h["current_value"]
            new_pnl   = existing["unrealized_pnl"] + h["unrealized_pnl"]
            combined_map[sym].update({
                "quantity":           new_qty,
                "invested_value":     round(new_inv, 2),
                "current_value":      round(new_cur, 2),
                "unrealized_pnl":     round(new_pnl, 2),
                "avg_cost_per_share": round(new_inv / new_qty, 4) if new_qty else 0,
                "unrealized_pnl_pct": round((new_pnl / new_inv * 100), 2) if new_inv else 0.0,
            })

    combined_holdings = sorted(combined_map.values(), key=lambda x: x["current_value"], reverse=True)
    total_invested = sum(h["invested_value"] for h in combined_holdings)
    total_current  = sum(h["current_value"]  for h in combined_holdings)
    total_pnl      = round(total_current - total_invested, 2)

    return {
        "as_of":      datetime.now().isoformat(timespec="seconds"),
        "accounts":   accounts_seen,
        "per_account": per_account,
        "combined": {
            "total_invested":          round(total_invested, 2),
            "total_current_value":     round(total_current, 2),
            "total_unrealized_pnl":    total_pnl,
            "total_unrealized_pnl_pct":round((total_pnl / total_invested * 100), 2) if total_invested else 0.0,
            "holdings": combined_holdings,
        },
    }


def get_all_account_values() -> dict:
    """
    Fetch account balances from all configured accounts.
    Returns per-account values plus combined totals.
    """
    per_account = []
    for ib in _get_connections():
        managed = ib.managedAccounts()
        if IBKR_ACCOUNTS:
            filter_ids = [a.strip() for a in IBKR_ACCOUNTS.split(",")]
            managed = [a for a in managed if a in filter_ids]
        for acct in managed:
            per_account.append(_account_summary_for(ib, acct))

    # Deduplicate (same account can appear on both connections in edge cases)
    seen, unique = set(), []
    for a in per_account:
        if a["account"] not in seen:
            seen.add(a["account"])
            unique.append(a)

    combined = {
        "net_liquidation_value": round(sum(a["net_liquidation_value"] for a in unique), 2),
        "total_cash":            round(sum(a["total_cash"]            for a in unique), 2),
        "stock_value":           round(sum(a["stock_value"]           for a in unique), 2),
        "unrealized_pnl":        round(sum(a["unrealized_pnl"]        for a in unique), 2),
        "realized_pnl":          round(sum(a["realized_pnl"]          for a in unique), 2),
    }

    return {
        "as_of":       datetime.now().isoformat(timespec="seconds"),
        "per_account": unique,
        "combined":    combined,
    }
