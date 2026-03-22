# 📊 finwatch-mcp

**A custom MCP Server for financial portfolio monitoring, risk analysis, and compliance — powered by LangGraph + Claude.**

> Turn natural language into actionable financial intelligence. Ask your portfolio questions like *"What's my risk exposure to tech stocks?"* or *"Flag any anomalous movements in the last 24h"* and get data-driven answers in seconds.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![MCP Protocol](https://img.shields.io/badge/MCP-Streamable_HTTP-teal.svg)](https://modelcontextprotocol.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-agent-purple.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   CLIENT LAYER                          │
│   Claude Desktop  │  Gradio UI  │  CLI  │  Telegram     │
└────────────────────────┬────────────────────────────────┘
                         │ MCP Protocol (JSON-RPC)
┌────────────────────────▼────────────────────────────────┐
│              LANGGRAPH AGENT (Orchestrator)              │
│  Multi-step reasoning · Report generation · Triage      │
│  Claude API · StateGraph · Human-in-the-loop            │
└────────────────────────┬────────────────────────────────┘
                         │ MCP Tool Calls
┌────────────────────────▼────────────────────────────────┐
│              FINWATCH MCP SERVER                        │
│                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │ get_portfolio │ │ analyze_risk │ │ detect_anomaly │  │
│  └──────────────┘ └──────────────┘ └────────────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │search_filings│ │get_market_kpi│ │compliance_check│  │
│  └──────────────┘ └──────────────┘ └────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    DATA LAYER                            │
│  SQLite (prices, KPIs)  │  ChromaDB (SEC filings, RAG)  │
│  Alpha Vantage · Finnhub · FRED · SEC EDGAR             │
└─────────────────────────────────────────────────────────┘
```

## Features

### MCP Server Tools
| Tool | Description |
|------|-------------|
| `get_portfolio` | Real-time portfolio status: holdings, P&L, sector allocation |
| `analyze_risk` | Risk metrics: VaR, Sharpe ratio, Beta, max drawdown |
| `detect_anomaly` | Flag unusual price movements, volume spikes, correlation breaks |
| `search_filings` | RAG-powered semantic search over SEC filings and earnings reports |
| `get_market_kpi` | Macro indicators: interest rates, inflation, sector performance |
| `compliance_check` | Validate portfolio against exposure limits and concentration rules |

### LangGraph Agent
- **Multi-step reasoning**: chains tool calls to answer complex questions
- **Report generation**: automated daily/weekly portfolio summaries
- **Anomaly triage**: investigates detected anomalies with root cause analysis
- **Human-in-the-loop**: asks for confirmation before high-impact actions

## Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- API keys: Alpha Vantage (free), Finnhub (free), Anthropic (for agent)

### Installation

```bash
# Clone the repo
git clone https://github.com/geraldo96/finwatch-mcp.git
cd finwatch-mcp

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Run the MCP Server

```bash
# Start the MCP server (Streamable HTTP)
uv run python -m src.mcp_server.server

# The server runs on http://localhost:8080/mcp
```

### Connect to Claude Desktop

Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "finwatch": {
      "type": "http",
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### Run the LangGraph Agent (standalone)

```bash
# Interactive CLI mode
uv run python -m src.agent.cli

# Example queries:
# > What's my current portfolio allocation?
# > Is my tech exposure within compliance limits?
# > Show me anomalies from the last week and explain them
```

### Run with Docker

```bash
docker compose up
# MCP server: http://localhost:8080/mcp
# Gradio UI:  http://localhost:7860
```

## Data Sources

| Source | Data | API Key | Rate Limit (free) |
|--------|------|---------|-------------------|
| [Alpha Vantage](https://www.alphavantage.co/) | Stock prices, fundamentals | Free | 25 req/day |
| [Finnhub](https://finnhub.io/) | Real-time quotes, news, sentiment | Free | 60 req/min |
| [FRED](https://fred.stlouisfed.org/) | Macro indicators, interest rates | Free | 120 req/min |
| [SEC EDGAR](https://www.sec.gov/edgar) | 10-K, 10-Q filings | None | 10 req/sec |
| [Yahoo Finance](https://pypi.org/project/yfinance/) | Historical prices (backup) | None | Unofficial |

## Project Structure

```
finwatch-mcp/
├── src/
│   ├── mcp_server/
│   │   ├── server.py          # MCP server entrypoint (Streamable HTTP)
│   │   ├── tools/
│   │   │   ├── portfolio.py   # get_portfolio tool
│   │   │   ├── risk.py        # analyze_risk tool
│   │   │   ├── anomaly.py     # detect_anomaly tool
│   │   │   ├── filings.py     # search_filings tool (RAG)
│   │   │   ├── market_kpi.py  # get_market_kpi tool
│   │   │   └── compliance.py  # compliance_check tool
│   │   └── config.py          # Server configuration
│   ├── agent/
│   │   ├── graph.py           # LangGraph StateGraph definition
│   │   ├── nodes.py           # Agent nodes (reason, act, report)
│   │   ├── state.py           # Agent state schema
│   │   └── cli.py             # Interactive CLI client
│   ├── data/
│   │   ├── ingester.py        # Data fetching & sync logic
│   │   ├── models.py          # SQLAlchemy / Pydantic models
│   │   └── db.py              # Database connection & queries
│   └── rag/
│       ├── embeddings.py      # BAAI embedding pipeline
│       ├── indexer.py         # SEC filing indexer
│       └── retriever.py       # ChromaDB retrieval
├── tests/
│   ├── test_tools.py          # Unit tests for MCP tools
│   ├── test_agent.py          # Agent integration tests
│   └── test_data.py           # Data layer tests
├── scripts/
│   ├── seed_data.py           # Seed DB with sample portfolio
│   ├── ingest_filings.py      # Download & index SEC filings
│   └── demo.py                # Full demo walkthrough
├── docs/
│   ├── ARCHITECTURE.md        # Detailed architecture docs
│   └── TOOLS.md               # MCP tool specifications
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

## Development Roadmap

### Week 1 — Foundation
- [x] Project scaffold & CI setup
- [ ] MCP server with `get_portfolio` and `analyze_risk` tools
- [ ] SQLite data layer + Alpha Vantage / yfinance ingestion
- [ ] Sample portfolio seeding script

### Week 2 — RAG & Anomaly Detection
- [ ] ChromaDB setup + SEC EDGAR filing indexer
- [ ] `search_filings` tool with BAAI embeddings
- [ ] `detect_anomaly` tool (z-score + rolling stats)
- [ ] `get_market_kpi` tool (FRED integration)

### Week 3 — Agent & Orchestration
- [ ] LangGraph StateGraph with Claude API
- [ ] Multi-step reasoning chains
- [ ] `compliance_check` tool
- [ ] Interactive CLI client

### Week 4 — Polish & Deploy
- [ ] Docker Compose (server + agent + Gradio UI)
- [ ] Comprehensive tests
- [ ] Demo video / GIF
- [ ] Hugging Face Space (optional)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| MCP Server | Python `mcp` SDK, Streamable HTTP |
| Agent | LangGraph, Claude API (Anthropic SDK) |
| Structured Data | SQLite + SQLAlchemy |
| Vector Store | ChromaDB + BAAI/bge-small-en-v1.5 |
| Data Sources | Alpha Vantage, Finnhub, FRED, SEC EDGAR, yfinance |
| UI | Gradio (demo), Claude Desktop (production) |
| Deploy | Docker Compose |
| Testing | pytest, pytest-asyncio |

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) first.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built by [Geraldo Margjini](https://github.com/geraldo96) as a portfolio project demonstrating MCP Server development, LangGraph agent orchestration, and financial data engineering.*
