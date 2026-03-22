"""detect_anomaly: Flag unusual price movements and volume spikes."""

import json
from datetime import datetime, UTC

import numpy as np
import pandas as pd
import yfinance as yf

from src.data.models import Holding, get_session


async def detect_anomaly(
    lookback_days: int = 7,
    z_threshold: float = 2.0,
) -> str:
    """Detect anomalous movements in portfolio holdings.

    Uses z-score on daily returns and volume to flag unusual activity.
    """
    session = get_session()
    try:
        holdings = session.query(Holding).all()
        if not holdings:
            return json.dumps({"status": "error", "message": "No holdings found."})

        tickers = [h.ticker for h in holdings]
        ticker_names = {h.ticker: h.name for h in holdings}

        # Fetch 90 days to compute baseline stats, analyze last `lookback_days`
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        data = yf.download(tickers, start=start_date, end=end_date, progress=False)

        if data.empty:
            return json.dumps({"status": "error", "message": "Could not fetch market data."})

        anomalies = []

        for ticker in tickers:
            try:
                if len(tickers) > 1:
                    close = data["Close"][ticker].dropna()
                    volume = data["Volume"][ticker].dropna()
                else:
                    close = data["Close"].dropna()
                    volume = data["Volume"].dropna()

                if len(close) < 30:
                    continue

                returns = close.pct_change().dropna()

                # Baseline: everything before the lookback window
                baseline_returns = returns.iloc[:-lookback_days]
                recent_returns = returns.iloc[-lookback_days:]
                baseline_volume = volume.iloc[:-lookback_days]
                recent_volume = volume.iloc[-lookback_days:]

                # Z-scores for returns
                mu_r = baseline_returns.mean()
                sigma_r = baseline_returns.std()

                # Z-scores for volume
                mu_v = baseline_volume.mean()
                sigma_v = baseline_volume.std()

                for date, ret in recent_returns.items():
                    z_return = (ret - mu_r) / sigma_r if sigma_r > 0 else 0

                    vol = recent_volume.get(date, 0)
                    z_volume = (vol - mu_v) / sigma_v if sigma_v > 0 else 0

                    if abs(z_return) >= z_threshold or abs(z_volume) >= z_threshold:
                        severity = _classify_severity(z_return, z_volume)
                        anomaly_type = []
                        if abs(z_return) >= z_threshold:
                            direction = "spike" if z_return > 0 else "drop"
                            anomaly_type.append(f"price_{direction}")
                        if abs(z_volume) >= z_threshold:
                            anomaly_type.append("volume_spike")

                        anomalies.append({
                            "ticker": ticker,
                            "name": ticker_names.get(ticker, ticker),
                            "date": date.strftime("%Y-%m-%d"),
                            "type": ", ".join(anomaly_type),
                            "severity": severity,
                            "daily_return": f"{ret * 100:.2f}%",
                            "z_score_return": round(float(z_return), 2),
                            "volume": int(vol),
                            "z_score_volume": round(float(z_volume), 2),
                        })

            except Exception:
                continue

        # Sort by severity then date
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        anomalies.sort(key=lambda a: (severity_order.get(a["severity"], 4), a["date"]))

        result = {
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "parameters": {
                "lookback_days": lookback_days,
                "z_threshold": z_threshold,
            },
            "total_anomalies": len(anomalies),
            "anomalies": anomalies,
        }

        return json.dumps(result, indent=2)

    finally:
        session.close()


def _classify_severity(z_return: float, z_volume: float) -> str:
    """Classify anomaly severity based on z-scores."""
    max_z = max(abs(z_return), abs(z_volume))
    if max_z >= 4.0:
        return "critical"
    elif max_z >= 3.0:
        return "high"
    elif max_z >= 2.5:
        return "medium"
    else:
        return "low"
