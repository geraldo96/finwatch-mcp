"""Seed the database with a realistic sample portfolio.

Run: python -m scripts.seed_data
"""

from src.data.models import Holding, init_db, get_session

SAMPLE_PORTFOLIO = [
    # Tech (overweight to trigger compliance alerts)
    {"ticker": "AAPL", "name": "Apple Inc.", "shares": 50, "avg_cost": 178.50, "sector": "Technology", "country": "US"},
    {"ticker": "MSFT", "name": "Microsoft Corp.", "shares": 30, "avg_cost": 380.25, "sector": "Technology", "country": "US"},
    {"ticker": "NVDA", "name": "NVIDIA Corp.", "shares": 20, "avg_cost": 485.00, "sector": "Technology", "country": "US"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "shares": 25, "avg_cost": 141.30, "sector": "Technology", "country": "US"},

    # Healthcare
    {"ticker": "JNJ", "name": "Johnson & Johnson", "shares": 40, "avg_cost": 155.80, "sector": "Healthcare", "country": "US"},
    {"ticker": "UNH", "name": "UnitedHealth Group", "shares": 10, "avg_cost": 520.00, "sector": "Healthcare", "country": "US"},

    # Financials
    {"ticker": "JPM", "name": "JPMorgan Chase", "shares": 35, "avg_cost": 195.40, "sector": "Financials", "country": "US"},
    {"ticker": "V", "name": "Visa Inc.", "shares": 20, "avg_cost": 275.60, "sector": "Financials", "country": "US"},

    # Energy
    {"ticker": "XOM", "name": "Exxon Mobil", "shares": 45, "avg_cost": 105.20, "sector": "Energy", "country": "US"},

    # International
    {"ticker": "ASML", "name": "ASML Holding", "shares": 8, "avg_cost": 680.00, "sector": "Technology", "country": "NL"},
    {"ticker": "NVO", "name": "Novo Nordisk", "shares": 25, "avg_cost": 125.00, "sector": "Healthcare", "country": "DK"},

    # Consumer
    {"ticker": "AMZN", "name": "Amazon.com", "shares": 30, "avg_cost": 178.90, "sector": "Consumer Discretionary", "country": "US"},
]


def seed():
    """Initialize DB and insert sample portfolio."""
    init_db()
    session = get_session()

    # Clear existing holdings
    session.query(Holding).delete()

    for item in SAMPLE_PORTFOLIO:
        session.add(Holding(**item))

    session.commit()
    session.close()

    print(f"✅ Seeded {len(SAMPLE_PORTFOLIO)} holdings into the database.")
    print("\nPortfolio summary:")
    total = sum(h["shares"] * h["avg_cost"] for h in SAMPLE_PORTFOLIO)
    print(f"  Total cost basis: ${total:,.2f}")
    print(f"  Holdings: {len(SAMPLE_PORTFOLIO)}")

    sectors = {}
    for h in SAMPLE_PORTFOLIO:
        cost = h["shares"] * h["avg_cost"]
        sectors[h["sector"]] = sectors.get(h["sector"], 0) + cost
    print("  Sector allocation (by cost):")
    for sector, val in sorted(sectors.items(), key=lambda x: -x[1]):
        print(f"    {sector}: ${val:,.2f} ({val/total*100:.1f}%)")


if __name__ == "__main__":
    seed()
