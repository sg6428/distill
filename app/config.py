"""Environment-backed settings (LLM endpoints, output paths, agent limits)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loads configuration from environment variables and optional `.env` file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_api_base: str = ""
    llm_api_key: str = ""
    output_dir: Path = Path("outputs")
    max_react_steps: int = 8
    max_revision_rounds: int = 2


settings = Settings()
