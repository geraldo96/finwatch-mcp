# Dev Log

## 2026-03-23 — Project setup

### uv instead of pip
First time using uv as package manager. Setup was faster than expected —
`uv sync` replaces the usual `python -m venv` + `pip install` dance.
One gotcha: hatchling couldn't find the package automatically, had to add
`[tool.hatch.build.targets.wheel] packages = ["src"]` to pyproject.toml.

### Python 3.12 deprecation
`datetime.utcnow()` is deprecated in 3.12. Replaced with `datetime.now(UTC)`
across all modules. Minor but good to know for future projects.

### First test run
15 pytest tests passing for get_portfolio and analyze_risk.
yfinance pulls real market data — no API key needed, good for quick prototyping.