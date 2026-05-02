"""Interactive Brokers API wrapper using ib_insync.

Requires TWS or IB Gateway running locally with API access enabled.
Connection settings are read from environment variables:
  IBKR_HOST      (default: 127.0.0.1)
  IBKR_PORT      (default: 7497  — TWS paper trading)
  IBKR_CLIENT_ID (default: 1)

Port reference:
  7496 — TWS live trading
  7497 — TWS paper trading  ← default (safest)
  4001 — IB Gateway live
  4002 — IB Gateway paper
"""

import os
from datetime import datetime

import ib_insync
from ib_insync import (
    IB,
    Contract,
    Forex,
    Future,
    LimitOrder,
    MarketOrder,
    Option,
    Stock,
    StopOrder,
    util,
)

# ── connection config (override via env vars) ───────────────────────────────
IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IBKR_PORT", "7497"))   # paper TWS by default
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "1"))

# Shared IB instance — connected lazily on first use
_ib: IB | None = None


def _get_ib() -> IB:
    """Return a connected IB instance, reconnecting if needed."""
    global _ib
    util.startLoop()          # patches the event loop so sync calls work
    if _ib is None or not _ib.isConnected():
        _ib = IB()
        _ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID, readonly=False)
    return _ib


def _make_stock(symbol: str, exchange: str = "SMART", currency: str = "USD") -> Stock:
    return Stock(symbol.upper(), exchange, currency)


def _order_dict(trade: ib_insync.Trade) -> dict:
    o = trade.order
    s = trade.orderStatus
    return {
        "order_id": o.orderId,
        "symbol": trade.contract.symbol,
        "action": o.action,
        "order_type": o.orderType,
        "quantity": o.totalQuantity,
        "limit_price": o.lmtPrice if o.lmtPrice else None,
        "aux_price": o.auxPrice if o.auxPrice else None,
        "status": s.status,
        "filled": s.filled,
        "remaining": s.remaining,
        "avg_fill_price": s.avgFillPrice,
    }


# ---------------------------------------------------------------------------
# Account & Portfolio
# ---------------------------------------------------------------------------

def get_account_summary() -> dict:
    """
    Return key account metrics: net liquidation value, cash, buying power,
    unrealized P&L, realized P&L, and margin requirements.
    """
    ib = _get_ib()
    summary = ib.accountSummary()
    data = {item.tag: item.value for item in summary}

    def _f(key: str):
        v = data.get(key, "0")
        try:
            return float(v)
        except ValueError:
            return v

    return {
        "account": data.get("AccountCode", ""),
        "net_liquidation": _f("NetLiquidation"),
        "total_cash": _f("TotalCashValue"),
        "buying_power": _f("BuyingPower"),
        "gross_position_value": _f("GrossPositionValue"),
        "unrealized_pnl": _f("UnrealizedPnL"),
        "realized_pnl": _f("RealizedPnL"),
        "initial_margin": _f("InitMarginReq"),
        "maintenance_margin": _f("MaintMarginReq"),
        "currency": data.get("Currency", "USD"),
    }


def get_positions() -> dict:
    """
    Return all current portfolio positions with average cost and unrealized P&L.
    """
    ib = _get_ib()
    positions = ib.positions()

    result = []
    for pos in positions:
        c = pos.contract
        result.append({
            "symbol": c.symbol,
            "sec_type": c.secType,
            "exchange": c.exchange,
            "currency": c.currency,
            "quantity": pos.position,
            "avg_cost": pos.avgCost,
            "market_value": round(pos.position * pos.avgCost, 2),
        })

    return {
        "account": positions[0].account if positions else "",
        "total_positions": len(result),
        "positions": sorted(result, key=lambda x: x["symbol"]),
    }


def get_pnl() -> dict:
    """
    Return daily and total P&L across the whole portfolio.
    """
    ib = _get_ib()
    account = ib.managedAccounts()[0]
    pnl = ib.reqPnL(account)
    ib.sleep(0.5)  # allow data to populate

    return {
        "account": account,
        "daily_pnl": round(pnl.dailyPnL or 0, 2),
        "unrealized_pnl": round(pnl.unrealizedPnL or 0, 2),
        "realized_pnl": round(pnl.realizedPnL or 0, 2),
    }


# ---------------------------------------------------------------------------
# Market Data
# ---------------------------------------------------------------------------

def get_quote(symbol: str, exchange: str = "SMART", currency: str = "USD") -> dict:
    """
    Get the latest bid, ask, last price, and volume for a stock.
    """
    ib = _get_ib()
    contract = _make_stock(symbol, exchange, currency)
    ib.qualifyContracts(contract)

    ticker = ib.reqMktData(contract, "", False, False)
    ib.sleep(1)  # wait for snapshot

    return {
        "symbol": symbol.upper(),
        "exchange": exchange,
        "currency": currency,
        "bid": ticker.bid,
        "ask": ticker.ask,
        "last": ticker.last,
        "close": ticker.close,
        "volume": ticker.volume,
        "high": ticker.high,
        "low": ticker.low,
        "timestamp": datetime.now().isoformat(),
    }


def get_historical_bars(
    symbol: str,
    duration: str = "1 M",
    bar_size: str = "1 day",
    exchange: str = "SMART",
    currency: str = "USD",
) -> dict:
    """
    Fetch historical OHLCV bars for a stock.

    duration examples : '1 D', '1 W', '1 M', '1 Y', '5 Y'
    bar_size examples : '1 min', '5 mins', '1 hour', '1 day', '1 week'
    """
    ib = _get_ib()
    contract = _make_stock(symbol, exchange, currency)
    ib.qualifyContracts(contract)

    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow="TRADES",
        useRTH=True,
        formatDate=1,
    )

    return {
        "symbol": symbol.upper(),
        "duration": duration,
        "bar_size": bar_size,
        "total_bars": len(bars),
        "bars": [
            {
                "date": str(b.date),
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in bars
        ],
    }


def search_contract(symbol: str, sec_type: str = "STK", currency: str = "USD") -> dict:
    """
    Search for a contract by symbol and security type.
    sec_type: STK, OPT, FUT, FOREX, CFD, FUND, BOND, CMDTY, IND
    """
    ib = _get_ib()
    results = ib.reqMatchingSymbols(symbol)
    ib.sleep(0.5)

    matches = []
    for cd in results:
        c = cd.contract
        if sec_type and c.secType != sec_type:
            continue
        if currency and c.currency != currency:
            continue
        matches.append({
            "symbol": c.symbol,
            "con_id": c.conId,
            "sec_type": c.secType,
            "exchange": c.primaryExch,
            "currency": c.currency,
            "description": cd.derivativeSecTypes,
        })

    return {
        "query": symbol,
        "sec_type": sec_type,
        "total_found": len(matches),
        "matches": matches,
    }


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

def get_open_orders() -> dict:
    """
    Return all currently open (unfilled) orders.
    """
    ib = _get_ib()
    trades = ib.openTrades()
    return {
        "total_open_orders": len(trades),
        "orders": [_order_dict(t) for t in trades],
    }


def place_order(
    symbol: str,
    action: str,
    quantity: float,
    order_type: str = "MKT",
    limit_price: float | None = None,
    stop_price: float | None = None,
    exchange: str = "SMART",
    currency: str = "USD",
) -> dict:
    """
    Place a stock order.

    action     : BUY or SELL
    order_type : MKT, LMT, STP
    quantity   : number of shares
    limit_price: required for LMT orders
    stop_price : required for STP orders
    """
    ib = _get_ib()
    contract = _make_stock(symbol, exchange, currency)
    ib.qualifyContracts(contract)

    action = action.upper()
    order_type = order_type.upper()

    if order_type == "MKT":
        order = MarketOrder(action, quantity)
    elif order_type == "LMT":
        if limit_price is None:
            raise ValueError("limit_price required for LMT orders")
        order = LimitOrder(action, quantity, limit_price)
    elif order_type == "STP":
        if stop_price is None:
            raise ValueError("stop_price required for STP orders")
        order = StopOrder(action, quantity, stop_price)
    else:
        raise ValueError(f"Unsupported order_type: {order_type}. Use MKT, LMT, or STP.")

    trade = ib.placeOrder(contract, order)
    ib.sleep(0.5)

    return {
        "status": "submitted",
        "order_id": trade.order.orderId,
        "symbol": symbol.upper(),
        "action": action,
        "order_type": order_type,
        "quantity": quantity,
        "limit_price": limit_price,
        "stop_price": stop_price,
        "order_status": trade.orderStatus.status,
    }


def cancel_order(order_id: int) -> dict:
    """
    Cancel an open order by its order ID.
    """
    ib = _get_ib()
    open_trades = {t.order.orderId: t for t in ib.openTrades()}

    if order_id not in open_trades:
        return {"order_id": order_id, "status": "not_found"}

    trade = open_trades[order_id]
    ib.cancelOrder(trade.order)
    ib.sleep(0.5)

    return {
        "order_id": order_id,
        "symbol": trade.contract.symbol,
        "status": "cancel_requested",
    }


def get_trades(days: int = 1) -> dict:
    """
    Return recent trade executions (fills) for today or past N days.
    """
    ib = _get_ib()
    fills = ib.fills()

    result = []
    for fill in fills:
        c = fill.contract
        e = fill.execution
        result.append({
            "exec_id": e.execId,
            "symbol": c.symbol,
            "side": e.side,
            "quantity": e.shares,
            "price": e.price,
            "time": e.time.isoformat() if hasattr(e.time, "isoformat") else str(e.time),
            "exchange": e.exchange,
            "order_id": e.orderId,
        })

    return {
        "total_fills": len(result),
        "fills": sorted(result, key=lambda x: x["time"], reverse=True),
    }
