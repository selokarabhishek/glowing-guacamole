"""Configuration management with pydantic-settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # VLM Provider Settings
    default_vlm_provider: str = "claude"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # Model Settings
    claude_model: str = "claude-sonnet-4-20250514"
    openai_model: str = "gpt-4o"
    ollama_model: str = "qwen2.5vl:7b"

    # Server Settings
    host: str = "127.0.0.1"
    port: int = 8000

    # Memory Settings
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Security Settings
    api_token: str = ""  # Optional auth token - generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    require_auth: bool = False  # Set to True to require authentication

    # Analysis Settings
    max_tokens: int = 4096
    system_prompt: str = """You are a visual UI analysis expert. Analyze the provided screenshot and:

1. Describe what you see on the page (layout, elements, purpose)
2. If there are forms, identify all input fields with their labels
3. Provide structured data for any detected form fields including:
   - Field type (text, email, password, select, checkbox, etc.)
   - Field label
   - CSS selector to locate the field
   - Whether it's required
   - Suggested values if applicable

Be precise and actionable in your analysis."""


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
