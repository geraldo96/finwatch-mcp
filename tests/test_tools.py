"""Tests for finwatch MCP tools: get_portfolio and analyze_risk.

Run: python -m pytest tests/test_tools.py -v
"""

import asyncio
import json

import pytest

from src.data.models import Holding, init_db, get_session


# --- Fixtures ---

@pytest.fixture(autouse=True)
def setup_db():
    """Ensure DB exists and has test holdings before each test."""
    init_db()
    session = get_session()

    # Clear and re-seed with minimal test portfolio
    session.query(Holding).delete()
    session.commit()

    test_holdings = [
        Holding(ticker="AAPL", name="Apple Inc.", shares=50, avg_cost=178.50, sector="Technology", country="US"),
        Holding(ticker="MSFT", name="Microsoft Corp.", shares=30, avg_cost=380.25, sector="Technology", country="US"),
        Holding(ticker="JNJ", name="Johnson & Johnson", shares=40, avg_cost=155.80, sector="Healthcare", country="US"),
        Holding(ticker="JPM", name="JPMorgan Chase", shares=35, avg_cost=195.40, sector="Financials", country="US"),
        Holding(ticker="XOM", name="Exxon Mobil", shares=45, avg_cost=105.20, sector="Energy", country="US"),
    ]

    for h in test_holdings:
        session.add(h)
    session.commit()
    session.close()

    yield

    # Cleanup
    session = get_session()
    session.query(Holding).delete()
    session.commit()
    session.close()


# --- get_portfolio tests ---

class TestGetPortfolio:
    """Tests for the get_portfolio tool."""

    @pytest.mark.asyncio
    async def test_returns_valid_json(self):
        """Tool should return valid JSON."""
        from src.mcp_server.tools.portfolio import get_portfolio

        result = await get_portfolio()
        data = json.loads(result)
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_summary_fields(self):
        """Summary should contain all required fields."""
        from src.mcp_server.tools.portfolio import get_portfolio

        result = await get_portfolio()
        data = json.loads(result)
        summary = data["summary"]

        assert "total_value" in summary
        assert "total_cost" in summary
        assert "total_pnl" in summary
        assert "total_pnl_pct" in summary
        assert "num_holdings" in summary
        assert summary["num_holdings"] == 5

    @pytest.mark.asyncio
    async def test_total_value_positive(self):
        """Portfolio total value should be positive."""
        from src.mcp_server.tools.portfolio import get_portfolio

        result = await get_portfolio()
        data = json.loads(result)
        assert data["summary"]["total_value"] > 0

    @pytest.mark.asyncio
    async def test_sector_allocation_sums_to_100(self):
        """Sector allocation percentages should sum to ~100%."""
        from src.mcp_server.tools.portfolio import get_portfolio

        result = await get_portfolio()
        data = json.loads(result)
        total_pct = sum(data["sector_allocation"].values())
        assert 99.0 <= total_pct <= 101.0

    @pytest.mark.asyncio
    async def test_filter_by_ticker(self):
        """Filtering by ticker should return only that holding."""
        from src.mcp_server.tools.portfolio import get_portfolio

        result = await get_portfolio(ticker="AAPL")
        data = json.loads(result)
        assert data["summary"]["num_holdings"] == 1
        assert data["holdings"][0]["ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_filter_nonexistent_ticker(self):
        """Filtering by unknown ticker should return empty."""
        from src.mcp_server.tools.portfolio import get_portfolio

        result = await get_portfolio(ticker="ZZZZZ")
        data = json.loads(result)
        assert data["status"] == "empty"

    @pytest.mark.asyncio
    async def test_holdings_have_required_fields(self):
        """Each holding should have all expected fields."""
        from src.mcp_server.tools.portfolio import get_portfolio

        result = await get_portfolio()
        data = json.loads(result)

        required_fields = [
            "ticker", "name", "shares", "avg_cost",
            "current_price", "market_value", "pnl", "pnl_pct",
            "sector", "country",
        ]

        for holding in data["holdings"]:
            for field in required_fields:
                assert field in holding, f"Missing field: {field} in {holding['ticker']}"


# --- analyze_risk tests ---

class TestAnalyzeRisk:
    """Tests for the analyze_risk tool."""

    @pytest.mark.asyncio
    async def test_returns_valid_json(self):
        """Tool should return valid JSON."""
        from src.mcp_server.tools.risk import analyze_risk

        result = await analyze_risk(window_days=30)
        data = json.loads(result)
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_metrics_present(self):
        """All risk metrics should be present in the response."""
        from src.mcp_server.tools.risk import analyze_risk

        result = await analyze_risk(window_days=30)
        data = json.loads(result)
        metrics = data["portfolio_metrics"]

        assert "var_1d" in metrics
        assert "volatility_annual" in metrics
        assert "sharpe_ratio" in metrics
        assert "beta_vs_spy" in metrics
        assert "max_drawdown" in metrics

    @pytest.mark.asyncio
    async def test_var_is_negative(self):
        """Value at Risk should be negative (it's a loss measure)."""
        from src.mcp_server.tools.risk import analyze_risk

        result = await analyze_risk(window_days=30, confidence_level=0.95)
        data = json.loads(result)
        assert data["portfolio_metrics"]["var_1d"] < 0

    @pytest.mark.asyncio
    async def test_volatility_is_positive(self):
        """Annualized volatility should be positive."""
        from src.mcp_server.tools.risk import analyze_risk

        result = await analyze_risk(window_days=30)
        data = json.loads(result)
        assert data["portfolio_metrics"]["volatility_annual"] > 0

    @pytest.mark.asyncio
    async def test_max_drawdown_is_negative(self):
        """Max drawdown should be negative or zero."""
        from src.mcp_server.tools.risk import analyze_risk

        result = await analyze_risk(window_days=30)
        data = json.loads(result)
        assert data["portfolio_metrics"]["max_drawdown"] <= 0

    @pytest.mark.asyncio
    async def test_interpretation_present(self):
        """Response should include human-readable interpretation."""
        from src.mcp_server.tools.risk import analyze_risk

        result = await analyze_risk(window_days=30)
        data = json.loads(result)
        assert "interpretation" in data
        assert "sharpe" in data["interpretation"]
        assert "volatility" in data["interpretation"]

    @pytest.mark.asyncio
    async def test_asset_volatility_per_ticker(self):
        """Per-asset volatility should be reported for each holding."""
        from src.mcp_server.tools.risk import analyze_risk

        result = await analyze_risk(window_days=30)
        data = json.loads(result)
        assert "asset_volatility" in data
        assert "AAPL" in data["asset_volatility"]

    @pytest.mark.asyncio
    async def test_custom_window(self):
        """Tool should respect custom window parameter."""
        from src.mcp_server.tools.risk import analyze_risk

        result = await analyze_risk(window_days=7)
        data = json.loads(result)
        assert data["parameters"]["window_days"] == 7
