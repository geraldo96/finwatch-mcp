"""get_market_kpi: Retrieve macro-economic indicators."""

import json
from datetime import datetime

import yfinance as yf


async def get_market_kpi(
    indicators: list[str] | None = None,
) -> str:
    """Get macro-economic indicators and market KPIs.

    Fetches data from Yahoo Finance (FRED integration in Week 2).
    """
    if indicators is None:
        indicators = ["fed_rate", "treasury_10y", "sector_performance"]

    result: dict = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "indicators": {},
    }

    for ind in indicators:
        try:
            if ind == "sector_performance":
                result["indicators"]["sector_performance"] = _get_sector_performance()
            elif ind == "treasury_10y":
                result["indicators"]["treasury_10y"] = _get_ticker_value("^TNX", "10Y Treasury Yield")
            elif ind == "fed_rate":
                # Approximation via 3-month T-bill
                result["indicators"]["fed_rate"] = _get_ticker_value("^IRX", "Fed Funds Rate (approx)")
            else:
                result["indicators"][ind] = {"status": "not_available", "note": "FRED integration pending"}
        except Exception as e:
            result["indicators"][ind] = {"status": "error", "message": str(e)}

    return json.dumps(result, indent=2)


def _get_sector_performance() -> dict:
    """Get sector ETF performance."""
    sector_etfs = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Energy": "XLE",
        "Consumer Discretionary": "XLY",
        "Industrials": "XLI",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
    }
    results = {}
    for sector, etf in sector_etfs.items():
        try:
            ticker = yf.Ticker(etf)
            hist = ticker.history(period="1mo")
            if not hist.empty:
                first = hist["Close"].iloc[0]
                last = hist["Close"].iloc[-1]
                change = (last - first) / first * 100
                results[sector] = {
                    "etf": etf,
                    "1m_return": f"{change:.2f}%",
                    "current": round(float(last), 2),
                }
        except Exception:
            continue
    return results


def _get_ticker_value(symbol: str, label: str) -> dict:
    """Get latest value for a market ticker."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        if not hist.empty:
            value = float(hist["Close"].iloc[-1])
            return {"label": label, "value": round(value, 4)}
    except Exception:
        pass
    return {"label": label, "status": "unavailable"}
