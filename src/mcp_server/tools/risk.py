"""analyze_risk: Calculate portfolio risk metrics."""

import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

from src.data.models import Holding, get_session


async def analyze_risk(
    window_days: int = 30,
    confidence_level: float = 0.95,
) -> str:
    """Calculate risk metrics for the portfolio.

    Returns: VaR, Sharpe ratio, Beta, max drawdown, volatility.
    """
    session = get_session()
    try:
        holdings = session.query(Holding).all()
        if not holdings:
            return json.dumps({"status": "error", "message": "No holdings found."})

        tickers = [h.ticker for h in holdings]
        weights = _compute_weights(holdings)

        # Fetch historical prices
        end_date = datetime.now()
        start_date = end_date - timedelta(days=window_days + 30)  # extra buffer
        prices = yf.download(tickers, start=start_date, end=end_date, progress=False)["Close"]

        if prices.empty:
            return json.dumps({"status": "error", "message": "Could not fetch price data."})

        # Ensure DataFrame even for single ticker
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name=tickers[0])

        returns = prices.pct_change().dropna().tail(window_days)

        if returns.empty:
            return json.dumps({"status": "error", "message": "Insufficient price history."})

        # Portfolio returns (weighted)
        weight_array = np.array([weights.get(t, 0) for t in returns.columns])
        portfolio_returns = returns.values @ weight_array

        # --- Metrics ---
        # 1. Value at Risk (Historical VaR)
        var = float(np.percentile(portfolio_returns, (1 - confidence_level) * 100))

        # 2. Volatility (annualized)
        volatility = float(np.std(portfolio_returns) * np.sqrt(252))

        # 3. Sharpe Ratio (assuming risk-free rate ~4.5%)
        risk_free_daily = 0.045 / 252
        mean_excess = np.mean(portfolio_returns) - risk_free_daily
        sharpe = float(mean_excess / np.std(portfolio_returns) * np.sqrt(252)) if np.std(portfolio_returns) > 0 else 0.0

        # 4. Beta vs SPY
        beta = _compute_beta(portfolio_returns, start_date, end_date, window_days)

        # 5. Max Drawdown
        cumulative = np.cumprod(1 + portfolio_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = float(np.min(drawdowns))

        # Per-asset volatility
        asset_vols = {}
        for col in returns.columns:
            asset_vols[col] = round(float(returns[col].std() * np.sqrt(252)), 4)

        result = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "parameters": {
                "window_days": window_days,
                "confidence_level": confidence_level,
            },
            "portfolio_metrics": {
                "var_1d": round(var, 6),
                "var_1d_pct": f"{var * 100:.2f}%",
                "volatility_annual": round(volatility, 4),
                "sharpe_ratio": round(sharpe, 4),
                "beta_vs_spy": round(beta, 4),
                "max_drawdown": round(max_drawdown, 4),
                "max_drawdown_pct": f"{max_drawdown * 100:.2f}%",
            },
            "asset_volatility": asset_vols,
            "interpretation": _interpret_metrics(sharpe, volatility, max_drawdown, var),
        }

        return json.dumps(result, indent=2)

    finally:
        session.close()


def _compute_weights(holdings: list[Holding]) -> dict[str, float]:
    """Compute portfolio weights based on cost basis."""
    total = sum(h.shares * h.avg_cost for h in holdings)
    if total == 0:
        return {}
    return {h.ticker: (h.shares * h.avg_cost) / total for h in holdings}


def _compute_beta(
    portfolio_returns: np.ndarray,
    start_date: datetime,
    end_date: datetime,
    window_days: int,
) -> float:
    """Compute portfolio beta against S&P 500 (SPY)."""
    try:
        spy = yf.download("SPY", start=start_date, end=end_date, progress=False)["Close"]
        spy_returns = spy.pct_change().dropna().tail(window_days).values

        min_len = min(len(portfolio_returns), len(spy_returns))
        if min_len < 5:
            return 1.0

        p = portfolio_returns[:min_len]
        s = spy_returns[:min_len]

        covariance = np.cov(p, s)[0][1]
        spy_variance = np.var(s)
        return float(covariance / spy_variance) if spy_variance > 0 else 1.0
    except Exception:
        return 1.0


def _interpret_metrics(
    sharpe: float, volatility: float, max_drawdown: float, var: float
) -> dict[str, str]:
    """Provide human-readable interpretation of risk metrics."""
    interpretations = {}

    if sharpe > 1.5:
        interpretations["sharpe"] = "Excellent risk-adjusted returns"
    elif sharpe > 0.5:
        interpretations["sharpe"] = "Acceptable risk-adjusted returns"
    else:
        interpretations["sharpe"] = "Poor risk-adjusted returns — consider rebalancing"

    if volatility > 0.3:
        interpretations["volatility"] = "High volatility — portfolio is aggressive"
    elif volatility > 0.15:
        interpretations["volatility"] = "Moderate volatility — balanced risk profile"
    else:
        interpretations["volatility"] = "Low volatility — conservative portfolio"

    if max_drawdown < -0.2:
        interpretations["drawdown"] = "Significant drawdown risk — review concentration"
    elif max_drawdown < -0.1:
        interpretations["drawdown"] = "Moderate drawdown — within normal range"
    else:
        interpretations["drawdown"] = "Contained drawdown — good downside protection"

    return interpretations
