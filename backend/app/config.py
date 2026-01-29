"""
Configuration settings using pydantic-settings.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Moralis API Key for fetching Solana token data
    moralis_api_key: Optional[str] = None

    # Database URL (SQLite by default)
    database_url: str = "sqlite+aiosqlite:///./solana_trends.db"

    # Snapshot interval in minutes
    snapshot_interval_minutes: int = 15

    # Frontend URL for CORS (Vite dev server runs on 5173 by default)
    frontend_url: str = "http://localhost:5173"

    # Application settings
    app_name: str = "Solana Meme Coin Trend Dashboard"
    debug: bool = False

    @property
    def has_moralis_key(self) -> bool:
        """Check if a valid Moralis API key is configured."""
        return self.moralis_api_key is not None and len(self.moralis_api_key) > 0


# Global settings instance
settings = Settings()
