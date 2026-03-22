"""Server configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # API Keys
    anthropic_api_key: str = ""
    alpha_vantage_api_key: str = ""
    finnhub_api_key: str = ""
    sec_edgar_user_agent: str = "finwatch-mcp contact@example.com"

    # Server
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8080

    # Database
    database_url: str = "sqlite:///data/finwatch.db"
    chroma_persist_dir: str = "data/chroma"

    # Agent
    claude_model: str = "claude-sonnet-4-20250514"
    max_agent_steps: int = 10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
