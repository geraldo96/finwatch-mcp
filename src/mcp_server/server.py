"""finwatch-mcp: MCP Server for financial portfolio monitoring and risk analysis.

Exposes 6 tools via the Model Context Protocol (Streamable HTTP transport):
- get_portfolio: Current portfolio holdings and P&L
- analyze_risk: Risk metrics (VaR, Sharpe, Beta, drawdown)
- detect_anomaly: Flag unusual market movements
- search_filings: RAG search over SEC filings
- get_market_kpi: Macro indicators from FRED
- compliance_check: Portfolio limit validation
"""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.mcp_server.tools.portfolio import get_portfolio
from src.mcp_server.tools.risk import analyze_risk
from src.mcp_server.tools.anomaly import detect_anomaly
from src.mcp_server.tools.filings import search_filings
from src.mcp_server.tools.market_kpi import get_market_kpi
from src.mcp_server.tools.compliance import compliance_check

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- MCP Server Setup ---
server = Server("finwatch-mcp")

# --- Tool Definitions ---
TOOLS: list[Tool] = [
    Tool(
        name="get_portfolio",
        description=(
            "Get current portfolio status including holdings, total value, "
            "P&L (profit/loss), and sector allocation. "
            "Optionally filter by ticker symbol."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Optional: filter by specific ticker symbol (e.g. 'AAPL')",
                },
            },
        },
    ),
    Tool(
        name="analyze_risk",
        description=(
            "Calculate portfolio risk metrics: Value at Risk (VaR), "
            "Sharpe ratio, Beta vs benchmark, max drawdown, and volatility. "
            "Supports different time windows."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "window_days": {
                    "type": "integer",
                    "description": "Lookback window in days (default: 30)",
                    "default": 30,
                },
                "confidence_level": {
                    "type": "number",
                    "description": "VaR confidence level (default: 0.95)",
                    "default": 0.95,
                },
            },
        },
    ),
    Tool(
        name="detect_anomaly",
        description=(
            "Detect anomalous price movements, volume spikes, or correlation breaks "
            "in portfolio holdings. Uses z-score and rolling statistics. "
            "Returns flagged events with severity and context."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "lookback_days": {
                    "type": "integer",
                    "description": "Days to look back for anomalies (default: 7)",
                    "default": 7,
                },
                "z_threshold": {
                    "type": "number",
                    "description": "Z-score threshold for anomaly (default: 2.0)",
                    "default": 2.0,
                },
            },
        },
    ),
    Tool(
        name="search_filings",
        description=(
            "Semantic search over SEC filings (10-K, 10-Q) and earnings reports. "
            "Uses RAG with vector embeddings to find relevant sections. "
            "Provide a natural language query about any company in the portfolio."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query (e.g. 'Apple revenue growth risks')",
                },
                "ticker": {
                    "type": "string",
                    "description": "Optional: filter by company ticker",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="get_market_kpi",
        description=(
            "Retrieve macro-economic indicators: Fed Funds Rate, CPI inflation, "
            "10Y Treasury yield, unemployment rate, GDP growth, and sector ETF performance. "
            "Data sourced from FRED and market APIs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "indicators": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of indicators to fetch. Options: "
                        "'fed_rate', 'cpi', 'treasury_10y', 'unemployment', 'gdp', 'sector_performance'. "
                        "Default: all."
                    ),
                },
            },
        },
    ),
    Tool(
        name="compliance_check",
        description=(
            "Validate the portfolio against predefined compliance rules: "
            "single-stock concentration limits, sector exposure caps, "
            "and geographic diversification requirements. "
            "Returns pass/fail status with details on any violations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "max_single_stock_pct": {
                    "type": "number",
                    "description": "Max allowed % in a single stock (default: 15)",
                    "default": 15.0,
                },
                "max_sector_pct": {
                    "type": "number",
                    "description": "Max allowed % in a single sector (default: 40)",
                    "default": 40.0,
                },
            },
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return the list of available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to their implementations."""
    logger.info(f"Tool call: {name} with args: {arguments}")

    handlers = {
        "get_portfolio": get_portfolio,
        "analyze_risk": analyze_risk,
        "detect_anomaly": detect_anomaly,
        "search_filings": search_filings,
        "get_market_kpi": get_market_kpi,
        "compliance_check": compliance_check,
    }

    handler = handlers.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    try:
        result = await handler(**arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error in {name}: {str(e)}")]


async def main():
    """Run the MCP server with stdio transport."""
    logger.info("Starting finwatch-mcp server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
