"""Configuration management for the marketing agent."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedditConfig(BaseSettings):
    """Reddit API configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="REDDIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    client_id: str = Field(..., description="Reddit client ID")
    client_secret: str = Field(..., description="Reddit client secret")
    user_agent: str = Field(default="GrowthAgent/1.0", description="Reddit user agent")
    username: str = Field(..., description="Reddit username")
    password: str = Field(..., description="Reddit password")
    rate_limit_per_minute: int = Field(default=30, description="Rate limit per minute")
    min_karma_required: int = Field(default=100, description="Minimum karma required")
    account_age_days: int = Field(default=30, description="Minimum account age in days")


class LLMConfig(BaseSettings):
    """LLM configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="ANTHROPIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(..., description="Anthropic API key")
    model: str = Field(default="claude-sonnet-4-20250514", description="Claude model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=200, description="Maximum tokens in response")
    timeout_seconds: int = Field(default=30, description="API timeout in seconds")


class SystemConfig(BaseSettings):
    """System-level configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="SYSTEM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_replies_per_day: int = Field(default=50, description="Max replies per day")
    discovery_interval_minutes: int = Field(default=60, description="Minutes between discovery cycles")
    auto_post_threshold: float = Field(default=8.0, description="Quality score threshold for auto-posting")
    review_threshold: float = Field(default=6.0, description="Quality score threshold for review queue")


class AppConfig(BaseSettings):
    """Application configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    default_brand_id: str = Field(default="goodpods", description="Default brand to use")
    environment: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Logging level")




class Settings(BaseSettings):
    """Main settings class."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    reddit: RedditConfig = Field(default_factory=RedditConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    app: AppConfig = Field(default_factory=AppConfig)

    @classmethod
    def create_for_testing(cls) -> "Settings":
        """Create settings instance for testing with minimal config."""
        return cls(
            reddit=RedditConfig(
                client_id="test_client_id",
                client_secret="test_client_secret",
                user_agent="test_agent",
                username="test_user",
                password="test_password",
            ),
            llm=LLMConfig(api_key="test_api_key"),
            system=SystemConfig(),
            app=AppConfig(),
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
