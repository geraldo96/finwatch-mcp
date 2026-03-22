FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY scripts/ scripts/

# Install dependencies
RUN uv pip install --system -e "."

# Create data directory
RUN mkdir -p data

EXPOSE 8080

CMD ["python", "-m", "src.mcp_server.server"]
