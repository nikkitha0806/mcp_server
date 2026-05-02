"""MCP server exposing Interactive Brokers (IBKR) trading tools via ib_insync.

Prerequisites:
  1. TWS or IB Gateway must be running with API access enabled.
  2. In TWS: Edit → Global Configuration → API → Settings
       ✓ Enable ActiveX and Socket Clients
       Socket port: 7497 (paper) or 7496 (live)
       ✓ Allow connections from localhost only

Environment variables (optional overrides):
  IBKR_HOST      — default 127.0.0.1
  IBKR_PORT      — default 7497  (paper TWS; use 7496 for live)
  IBKR_CLIENT_ID — default 1
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP

from tools.ibkr import (
    cancel_order,
    get_account_summary,
    get_historical_bars,
    get_open_orders,
    get_pnl,
    get_positions,
    get_quote,
    get_trades,
    place_order,
    search_contract,
)

mcp = FastMCP(
    name="ibkr",
    instructions=(
        "Interactive Brokers trading assistant. "
        "Use ibkr_account for balances, ibkr_positions for holdings, "
        "ibkr_quote for live prices, ibkr_history for OHLCV bars, "
        "ibkr_place_order to trade, and ibkr_orders to manage open orders. "
        "Always confirm before placing or cancelling orders."
    ),
)

# ---------------------------------------------------------------------------
# Account & Portfolio
# ---------------------------------------------------------------------------

@mcp.tool()
def ibkr_account() -> dict:
    """
    Get a full account summary: net liquidation value, total cash,
    buying power, gross position value, unrealized/realized P&L,
    and margin requirements.
    """
    return get_account_summary()


@mcp.tool()
def ibkr_positions() -> dict:
    """
    List all current portfolio positions with symbol, quantity,
    average cost, and estimated market value.
    """
    return get_positions()


@mcp.tool()
def ibkr_pnl() -> dict:
    """
    Get today's daily P&L and total unrealized/realized P&L
    across the entire portfolio.
    """
    return get_pnl()


# ---------------------------------------------------------------------------
# Market Data
# ---------------------------------------------------------------------------

@mcp.tool()
def ibkr_quote(symbol: str, exchange: str = "SMART", currency: str = "USD") -> dict:
    """
    Get the latest real-time quote for a stock: bid, ask, last price,
    today's high/low, volume, and previous close.

    Args:
        symbol: Ticker symbol, e.g. 'AAPL', 'TSLA', 'MSFT'.
        exchange: Exchange to route to (default SMART = best execution).
        currency: Currency, e.g. 'USD', 'GBP', 'EUR'.
    """
    return get_quote(symbol, exchange=exchange, currency=currency)


@mcp.tool()
def ibkr_history(
    symbol: str,
    duration: str = "1 M",
    bar_size: str = "1 day",
    exchange: str = "SMART",
    currency: str = "USD",
) -> dict:
    """
    Fetch historical OHLCV price bars for a stock.

    duration examples : '1 D', '1 W', '1 M', '3 M', '1 Y', '5 Y'
    bar_size examples : '1 min', '5 mins', '15 mins', '1 hour', '1 day', '1 week'

    Args:
        symbol: Ticker symbol, e.g. 'AAPL'.
        duration: How far back to fetch data.
        bar_size: Granularity of each bar.
        exchange: Exchange (default SMART).
        currency: Currency (default USD).
    """
    return get_historical_bars(symbol, duration=duration, bar_size=bar_size,
                               exchange=exchange, currency=currency)


@mcp.tool()
def ibkr_search(symbol: str, sec_type: str = "STK", currency: str = "USD") -> dict:
    """
    Search for a contract by symbol to get its contract ID,
    exchange, and available derivative types.

    Args:
        symbol: Partial or full ticker symbol to search.
        sec_type: Security type — STK, OPT, FUT, FOREX, IND, BOND, FUND.
        currency: Filter by currency, e.g. 'USD', 'GBP'.
    """
    return search_contract(symbol, sec_type=sec_type, currency=currency)


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@mcp.tool()
def ibkr_open_orders() -> dict:
    """
    List all currently open (pending/working) orders with their
    order ID, symbol, action, type, quantity, fill status, and price.
    """
    return get_open_orders()


@mcp.tool()
def ibkr_place_order(
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
    Place a stock order. THIS WILL EXECUTE A REAL TRADE on live accounts.
    Use paper trading (port 7497) while testing.

    Args:
        symbol: Ticker symbol, e.g. 'AAPL'.
        action: 'BUY' or 'SELL'.
        quantity: Number of shares.
        order_type: 'MKT' (market), 'LMT' (limit), or 'STP' (stop).
        limit_price: Required if order_type is 'LMT'.
        stop_price: Required if order_type is 'STP'.
        exchange: Routing exchange (default SMART).
        currency: Currency (default USD).
    """
    return place_order(
        symbol, action, quantity,
        order_type=order_type,
        limit_price=limit_price,
        stop_price=stop_price,
        exchange=exchange,
        currency=currency,
    )


@mcp.tool()
def ibkr_cancel_order(order_id: int) -> dict:
    """
    Cancel an open order by its order ID.
    Use ibkr_open_orders first to get the correct order ID.

    Args:
        order_id: The integer order ID from ibkr_open_orders.
    """
    return cancel_order(order_id)


@mcp.tool()
def ibkr_trades() -> dict:
    """
    Return all trade executions (fills) from the current session:
    symbol, side, quantity, fill price, exchange, and timestamp.
    """
    return get_trades()


if __name__ == "__main__":
    mcp.run(transport="stdio")
