"""Interactive Brokers portfolio tracker using ib_insync.

Read-only — fetches positions with quantity, invested value, and current value.

Connection settings (override via environment variables):
  IBKR_HOST       default: 127.0.0.1
  IBKR_PORT       default: 7497  (TWS paper trading — safest default)
  IBKR_CLIENT_ID  default: 1

Port reference:
  7497 — TWS paper trading
  7496 — TWS live trading
  4002 — IB Gateway paper
  4001 — IB Gateway live
"""

import os
from datetime import datetime

from ib_insync import IB, util

IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IBKR_PORT", "7497"))
# MCP server uses client ID 1; app uses 10 to avoid "client id already in use" errors.
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "10"))

_ib: IB | None = None


def _get_ib() -> IB:
    """Return a connected, read-only IB instance.

    Tries IBKR_CLIENT_ID first, then increments up to +9 until a free ID is found.
    """
    global _ib
    util.startLoop()
    if _ib is not None and _ib.isConnected():
        return _ib

    last_error = None
    for client_id in range(IBKR_CLIENT_ID, IBKR_CLIENT_ID + 10):
        try:
            ib = IB()
            ib.connect(IBKR_HOST, IBKR_PORT, clientId=client_id, readonly=True, timeout=10)
            _ib = ib
            return _ib
        except Exception as e:
            last_error = e
            continue

    raise ConnectionError(f"Could not connect to TWS on {IBKR_HOST}:{IBKR_PORT} — all client IDs {IBKR_CLIENT_ID}–{IBKR_CLIENT_ID+9} in use. Last error: {last_error}")


def get_portfolio() -> dict:
    """
    Return every stock position with quantity, invested value,
    current market value, and unrealized P&L.

    Uses ib.portfolio() which provides live market prices directly —
    no extra market-data requests needed.
    """
    ib = _get_ib()
    items = ib.portfolio()

    holdings = []
    total_invested = 0.0
    total_current = 0.0

    for item in items:
        c = item.contract
        quantity = item.position
        avg_cost = item.averageCost          # cost per share (includes commissions)
        current_price = item.marketPrice     # live market price per share
        current_value = item.marketValue     # quantity × current_price
        invested_value = round(quantity * avg_cost, 2)
        unrealized_pnl = item.unrealizedPNL
        pnl_pct = round((unrealized_pnl / invested_value) * 100, 2) if invested_value else 0.0

        total_invested += invested_value
        total_current += current_value

        holdings.append({
            "symbol": c.symbol,
            "sec_type": c.secType,
            "currency": c.currency,
            "quantity": quantity,
            "avg_cost_per_share": round(avg_cost, 4),
            "invested_value": invested_value,
            "current_price": round(current_price, 4),
            "current_value": round(current_value, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pnl_pct": pnl_pct,
        })

    # Sort by current value descending (largest holding first)
    holdings.sort(key=lambda x: x["current_value"], reverse=True)

    total_pnl = round(total_current - total_invested, 2)
    total_pnl_pct = round((total_pnl / total_invested) * 100, 2) if total_invested else 0.0

    return {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "total_positions": len(holdings),
        "summary": {
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_current, 2),
            "total_unrealized_pnl": total_pnl,
            "total_unrealized_pnl_pct": total_pnl_pct,
        },
        "holdings": holdings,
    }


def get_account_value() -> dict:
    """
    Return top-level account balances: net liquidation value, cash,
    and total stock value.
    """
    ib = _get_ib()
    tags = {item.tag: item.value for item in ib.accountSummary()}

    def _f(key: str) -> float:
        try:
            return round(float(tags.get(key, 0)), 2)
        except ValueError:
            return 0.0

    return {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "account": tags.get("AccountCode", ""),
        "net_liquidation_value": _f("NetLiquidation"),
        "total_cash": _f("TotalCashValue"),
        "stock_value": _f("StockMarketValue"),
        "unrealized_pnl": _f("UnrealizedPnL"),
        "realized_pnl": _f("RealizedPnL"),
        "currency": tags.get("Currency", "USD"),
    }
