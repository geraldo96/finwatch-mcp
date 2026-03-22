"""get_portfolio: Retrieve current portfolio holdings and P&L."""

import json
from datetime import datetime

import yfinance as yf

from src.data.models import Holding, PriceHistory, get_session


async def get_portfolio(ticker: str | None = None) -> str:
    """Get current portfolio status with real-time prices.

    Returns holdings, current value, P&L, and sector allocation.
    """
    session = get_session()
    try:
        query = session.query(Holding)
        if ticker:
            query = query.filter(Holding.ticker == ticker.upper())
        holdings = query.all()

        if not holdings:
            return json.dumps({"status": "empty", "message": "No holdings found."})

        # Fetch current prices
        tickers = [h.ticker for h in holdings]
        current_prices = _get_current_prices(tickers)

        # Build response
        portfolio_items = []
        total_value = 0.0
        total_cost = 0.0
        sector_allocation: dict[str, float] = {}

        for h in holdings:
            price = current_prices.get(h.ticker, h.avg_cost)
            market_value = h.shares * price
            cost_basis = h.shares * h.avg_cost
            pnl = market_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0

            portfolio_items.append({
                "ticker": h.ticker,
                "name": h.name,
                "shares": h.shares,
                "avg_cost": round(h.avg_cost, 2),
                "current_price": round(price, 2),
                "market_value": round(market_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "sector": h.sector,
                "country": h.country,
            })

            total_value += market_value
            total_cost += cost_basis
            sector_allocation[h.sector] = sector_allocation.get(h.sector, 0) + market_value

        # Calculate sector percentages
        sector_pct = {
            sector: round(value / total_value * 100, 2)
            for sector, value in sector_allocation.items()
        }

        result = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_value": round(total_value, 2),
                "total_cost": round(total_cost, 2),
                "total_pnl": round(total_value - total_cost, 2),
                "total_pnl_pct": round((total_value - total_cost) / total_cost * 100, 2),
                "num_holdings": len(holdings),
            },
            "sector_allocation": sector_pct,
            "holdings": portfolio_items,
        }

        return json.dumps(result, indent=2)

    finally:
        session.close()


def _get_current_prices(tickers: list[str]) -> dict[str, float]:
    """Fetch current prices from yfinance."""
    prices = {}
    try:
        data = yf.download(tickers, period="1d", progress=False)
        if "Close" in data.columns:
            for t in tickers:
                col = t if len(tickers) > 1 else "Close"
                if len(tickers) > 1:
                    val = data["Close"][t].iloc[-1] if t in data["Close"].columns else None
                else:
                    val = data["Close"].iloc[-1]
                if val is not None:
                    prices[t] = float(val)
    except Exception:
        pass  # Fall back to avg_cost in caller
    return prices
