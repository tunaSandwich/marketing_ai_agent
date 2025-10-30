"""Tests for configuration management."""

import pytest
from pydantic import ValidationError

from src.utils.config import (
    ApplicationConfig,
    EvaluationConfig,
    LLMConfig,
    RedditConfig,
    Settings,
)


class TestRedditConfig:
    """Tests for Reddit configuration."""

    def test_reddit_config_creation(self):
        """Test creating a valid Reddit config."""
        config = RedditConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            user_agent="test_agent",
            username="test_user",
            password="test_password",
        )

        assert config.client_id == "test_client_id"
        assert config.rate_limit_per_minute == 30  # Default value
        assert config.min_karma_required == 100  # Default value

    def test_reddit_config_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError):
            RedditConfig()  # Missing required fields


class TestLLMConfig:
    """Tests for LLM configuration."""

    def test_llm_config_creation(self):
        """Test creating a valid LLM config."""
        config = LLMConfig(anthropic_api_key="test_api_key")

        assert config.anthropic_api_key == "test_api_key"
        assert config.model == "claude-sonnet-4-20250514-sonnet-20241022"  # Default value
        assert config.temperature == 0.7  # Default value
        assert config.max_tokens == 200  # Default value

    def test_llm_config_custom_values(self):
        """Test LLM config with custom values."""
        config = LLMConfig(
            anthropic_api_key="test_key",
            model="claude-3-haiku",
            temperature=0.5,
            max_tokens=500,
        )

        assert config.model == "claude-3-haiku"
        assert config.temperature == 0.5
        assert config.max_tokens == 500


class TestEvaluationConfig:
    """Tests for evaluation configuration."""

    def test_evaluation_config_defaults(self):
        """Test evaluation config default values."""
        config = EvaluationConfig()

        assert config.auto_post_threshold == 40
        assert config.human_review_threshold == 30
        assert config.reject_threshold == 25

    def test_evaluation_config_custom_values(self):
        """Test evaluation config with custom values."""
        config = EvaluationConfig(
            auto_post_threshold=45,
            human_review_threshold=35,
            reject_threshold=20,
        )

        assert config.auto_post_threshold == 45
        assert config.human_review_threshold == 35
        assert config.reject_threshold == 20


class TestApplicationConfig:
    """Tests for application configuration."""

    def test_application_config_defaults(self):
        """Test application config default values."""
        config = ApplicationConfig()

        assert config.environment == "development"
        assert config.log_level == "INFO"
        assert config.max_replies_per_day == 10
        assert config.default_brand_id == "goodpods"

    def test_application_config_custom_values(self):
        """Test application config with custom values."""
        config = ApplicationConfig(
            environment="production",
            log_level="DEBUG",
            max_replies_per_day=50,
            default_brand_id="custom_brand",
        )

        assert config.environment == "production"
        assert config.log_level == "DEBUG"
        assert config.max_replies_per_day == 50
        assert config.default_brand_id == "custom_brand"


class TestSettings:
    """Tests for main settings configuration."""

    def test_settings_for_testing(self):
        """Test creating settings for testing."""
        settings = Settings.create_for_testing()

        assert settings.reddit.client_id == "test_client_id"
        assert settings.llm.anthropic_api_key == "test_api_key"
        assert settings.evaluation.auto_post_threshold == 40
        assert settings.app.environment == "development"

    def test_settings_nested_access(self):
        """Test accessing nested configuration values."""
        settings = Settings.create_for_testing()

        # Test nested access
        assert settings.reddit.rate_limit_per_minute == 30
        assert settings.llm.temperature == 0.7
        assert settings.evaluation.human_review_threshold == 30
        assert settings.app.max_replies_per_day == 10
