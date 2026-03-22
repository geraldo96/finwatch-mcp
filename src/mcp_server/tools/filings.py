"""search_filings: RAG-powered semantic search over SEC filings."""

import json
from datetime import datetime


async def search_filings(
    query: str,
    ticker: str | None = None,
    top_k: int = 5,
) -> str:
    """Search SEC filings using semantic similarity.

    Uses ChromaDB + BAAI embeddings for retrieval-augmented generation.
    """
    # TODO: Implement in Week 2
    # 1. Embed the query using BAAI/bge-small-en-v1.5
    # 2. Query ChromaDB collection filtered by ticker (if provided)
    # 3. Return top_k most relevant chunks with metadata

    try:
        from src.rag.retriever import retrieve_filings

        results = await retrieve_filings(query=query, ticker=ticker, top_k=top_k)
        return json.dumps(results, indent=2)

    except ImportError:
        # RAG not yet set up — return helpful placeholder
        return json.dumps({
            "status": "not_configured",
            "message": (
                "RAG pipeline not yet initialized. "
                "Run `python scripts/ingest_filings.py` to index SEC filings first."
            ),
            "query": query,
            "ticker": ticker,
            "timestamp": datetime.utcnow().isoformat(),
        }, indent=2)
