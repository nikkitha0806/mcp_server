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

from ib_insync import IB, Forex, util

IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IBKR_PORT", "7497"))
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "1"))

_ib: IB | None = None


def _get_ib() -> IB:
    """Return a connected, read-only IB instance."""
    global _ib
    util.startLoop()
    if _ib is None or not _ib.isConnected():
        _ib = IB()
        _ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID, readonly=True)
    return _ib


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


def get_eur_usd_rate() -> float:
    """
    Fetch the live EUR/USD exchange rate from IBKR.
    Returns how many USD equal 1 EUR (e.g. 1.08).
    Dividing a USD value by this gives the EUR equivalent.
    """
    ib = _get_ib()
    contract = Forex("EURUSD")
    ib.qualifyContracts(contract)
    ticker = ib.reqMktData(contract, "", False, False)
    ib.sleep(1)
    rate = ticker.last or ticker.bid or ticker.ask
    ib.cancelMktData(contract)
    if not rate or rate != rate:   # guard against NaN
        raise ValueError("Could not retrieve EUR/USD rate from IBKR")
    return float(rate)


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
