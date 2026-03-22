"""compliance_check: Validate portfolio against exposure limits."""

import json
from datetime import datetime, UTC

import yfinance as yf

from src.data.models import Holding, get_session


async def compliance_check(
    max_single_stock_pct: float = 15.0,
    max_sector_pct: float = 40.0,
) -> str:
    """Check portfolio compliance against concentration and exposure rules.

    Validates:
    - Single-stock concentration
    - Sector exposure caps
    - Geographic diversification
    """
    session = get_session()
    try:
        holdings = session.query(Holding).all()
        if not holdings:
            return json.dumps({"status": "error", "message": "No holdings found."})

        # Fetch current prices for accurate weights
        tickers = [h.ticker for h in holdings]
        prices = _get_prices(tickers)

        # Calculate market values
        total_value = 0.0
        stock_values: dict[str, float] = {}
        sector_values: dict[str, float] = {}
        country_values: dict[str, float] = {}

        for h in holdings:
            price = prices.get(h.ticker, h.avg_cost)
            mv = h.shares * price
            total_value += mv
            stock_values[h.ticker] = mv
            sector_values[h.sector] = sector_values.get(h.sector, 0) + mv
            country_values[h.country] = country_values.get(h.country, 0) + mv

        if total_value == 0:
            return json.dumps({"status": "error", "message": "Portfolio value is zero."})

        violations = []
        warnings = []

        # Check single-stock concentration
        for ticker, value in stock_values.items():
            pct = value / total_value * 100
            if pct > max_single_stock_pct:
                violations.append({
                    "rule": "single_stock_concentration",
                    "ticker": ticker,
                    "actual_pct": round(pct, 2),
                    "limit_pct": max_single_stock_pct,
                    "excess_pct": round(pct - max_single_stock_pct, 2),
                })
            elif pct > max_single_stock_pct * 0.8:
                warnings.append({
                    "rule": "single_stock_approaching_limit",
                    "ticker": ticker,
                    "actual_pct": round(pct, 2),
                    "limit_pct": max_single_stock_pct,
                })

        # Check sector concentration
        for sector, value in sector_values.items():
            pct = value / total_value * 100
            if pct > max_sector_pct:
                violations.append({
                    "rule": "sector_concentration",
                    "sector": sector,
                    "actual_pct": round(pct, 2),
                    "limit_pct": max_sector_pct,
                    "excess_pct": round(pct - max_sector_pct, 2),
                })
            elif pct > max_sector_pct * 0.8:
                warnings.append({
                    "rule": "sector_approaching_limit",
                    "sector": sector,
                    "actual_pct": round(pct, 2),
                    "limit_pct": max_sector_pct,
                })

        # Geographic diversification check (>80% in one country = warning)
        for country, value in country_values.items():
            pct = value / total_value * 100
            if pct > 80:
                warnings.append({
                    "rule": "geographic_concentration",
                    "country": country,
                    "actual_pct": round(pct, 2),
                    "note": "Consider international diversification",
                })

        is_compliant = len(violations) == 0

        result = {
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "compliant": is_compliant,
            "parameters": {
                "max_single_stock_pct": max_single_stock_pct,
                "max_sector_pct": max_sector_pct,
            },
            "summary": {
                "total_value": round(total_value, 2),
                "num_holdings": len(holdings),
                "num_violations": len(violations),
                "num_warnings": len(warnings),
            },
            "violations": violations,
            "warnings": warnings,
        }

        return json.dumps(result, indent=2)

    finally:
        session.close()


def _get_prices(tickers: list[str]) -> dict[str, float]:
    """Quick price fetch for compliance calculation."""
    prices = {}
    try:
        data = yf.download(tickers, period="1d", progress=False)
        if "Close" in data.columns:
            for t in tickers:
                try:
                    if len(tickers) > 1:
                        val = data["Close"][t].iloc[-1]
                    else:
                        val = data["Close"].iloc[-1]
                    prices[t] = float(val)
                except (KeyError, IndexError):
                    continue
    except Exception:
        pass
    return prices
