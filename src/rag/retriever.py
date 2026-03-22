"""RAG retriever for SEC filings using ChromaDB.

TODO (Week 2):
- Initialize ChromaDB with BAAI/bge-small-en-v1.5 embeddings
- Index SEC EDGAR filings (10-K, 10-Q)
- Implement semantic search with metadata filtering
"""

from datetime import datetime


async def retrieve_filings(
    query: str,
    ticker: str | None = None,
    top_k: int = 5,
) -> dict:
    """Retrieve relevant filing chunks via semantic search.

    This is a stub — run `scripts/ingest_filings.py` to set up the full pipeline.
    """
    # Placeholder until ChromaDB is configured
    return {
        "status": "not_configured",
        "message": "RAG pipeline not yet initialized. Run scripts/ingest_filings.py first.",
        "query": query,
        "ticker": ticker,
        "timestamp": datetime.utcnow().isoformat(),
    }
