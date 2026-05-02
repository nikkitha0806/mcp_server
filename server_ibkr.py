"""MCP server for IBKR portfolio tracking — read-only, no trading actions.

Prerequisites:
  1. TWS or IB Gateway must be running with API access enabled.
  2. In TWS: Edit → Global Configuration → API → Settings
       ✓ Enable ActiveX and Socket Clients
       Socket port: 7497 (paper) or 7496 (live)
       ✓ Allow connections from localhost only

Environment variables (optional):
  IBKR_HOST       default 127.0.0.1
  IBKR_PORT       default 7497
  IBKR_CLIENT_ID  default 1
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP
from tools.ibkr import get_account_value, get_portfolio

mcp = FastMCP(
    name="ibkr-portfolio",
    instructions=(
        "Read-only IBKR portfolio tracker. "
        "Use ibkr_portfolio to see all stock holdings with quantity, "
        "invested value, current value, and P&L. "
        "Use ibkr_account to see overall account balances."
    ),
)


@mcp.tool()
def ibkr_portfolio() -> dict:
    """
    Show all stock holdings with:
      - symbol and quantity held
      - average cost per share (what you paid)
      - invested value  (quantity × avg cost)
      - current price   (live market price)
      - current value   (quantity × current price)
      - unrealized P&L  and P&L percentage

    Results are sorted by current value (largest position first).
    Also includes a portfolio summary with totals.
    """
    return get_portfolio()


@mcp.tool()
def ibkr_account() -> dict:
    """
    Show top-level account balances:
      - net liquidation value (total account worth)
      - total cash balance
      - total stock market value
      - unrealized and realized P&L
    """
    return get_account_value()


if __name__ == "__main__":
    mcp.run(transport="stdio")
