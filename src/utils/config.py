"""Configuration management for the marketing agent."""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedditConfig(BaseModel):
    """Reddit API configuration."""

    client_id: str = Field(..., description="Reddit client ID")
    client_secret: str = Field(..., description="Reddit client secret")
    user_agent: str = Field(..., description="Reddit user agent")
    username: str = Field(..., description="Reddit username")
    password: str = Field(..., description="Reddit password")
    rate_limit_per_minute: int = Field(default=30, description="Rate limit per minute")
    min_karma_required: int = Field(default=100, description="Minimum karma required")
    account_age_days: int = Field(default=90, description="Minimum account age in days")


class LLMConfig(BaseModel):
    """LLM configuration."""

    anthropic_api_key: str = Field(..., description="Anthropic API key")
    model: str = Field(default="claude-sonnet-4-20250514", description="Claude model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=200, description="Maximum tokens in response")
    timeout_seconds: int = Field(default=30, description="API timeout in seconds")


class EvaluationConfig(BaseModel):
    """Evaluation thresholds configuration."""

    auto_post_threshold: int = Field(default=40, description="Auto-post threshold (0-50)")
    human_review_threshold: int = Field(default=30, description="Human review threshold (0-50)")
    reject_threshold: int = Field(default=25, description="Reject threshold (0-50)")


class ApplicationConfig(BaseModel):
    """Application-level configuration."""

    environment: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Path | None = Field(default=None, description="Log file path")
    max_replies_per_day: int = Field(default=10, description="Maximum replies per day")
    discovery_interval_minutes: int = Field(default=30, description="Discovery interval")
    default_brand_id: str = Field(default="goodpods", description="Default brand ID")
    brands_dir: Path = Field(default=Path("brands"), description="Brands directory")


class ReviewUIConfig(BaseModel):
    """Review UI configuration."""

    port: int = Field(default=8080, description="Review UI port")
    host: str = Field(default="localhost", description="Review UI host")


class Settings(BaseSettings):
    """Main application settings."""

    reddit: RedditConfig
    llm: LLMConfig
    evaluation: EvaluationConfig
    app: ApplicationConfig
    review_ui: ReviewUIConfig

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="_",
        case_sensitive=False,
        extra="ignore",
    )

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
            llm=LLMConfig(anthropic_api_key="test_api_key"),
            evaluation=EvaluationConfig(),
            app=ApplicationConfig(),
            review_ui=ReviewUIConfig(),
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
