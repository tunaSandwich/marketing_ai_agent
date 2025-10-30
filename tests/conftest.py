"""Shared test fixtures and configuration."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from src.models import BrandConfig, RedditPost
from src.utils.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings.create_for_testing()


@pytest.fixture
def sample_reddit_post() -> RedditPost:
    """Create a sample Reddit post for testing."""
    return RedditPost(
        id="test123",
        title="Looking for true crime podcasts",
        content="I love Serial and want something similar. Any recommendations?",
        subreddit="podcasts",
        score=15,
        created_at=datetime.now(UTC),
        url="https://reddit.com/r/podcasts/test123",
        author="test_user",
        num_comments=3,
    )


@pytest.fixture
def sample_brand_config() -> BrandConfig:
    """Create a sample brand configuration for testing."""
    return BrandConfig(
        brand_id="test_brand",
        brand_name="Test Brand",
        company_description="A test brand for unit testing",
        voice_guidelines="Be helpful and friendly",
        tone_attributes=["friendly", "helpful"],
        allowed_claims=[
            "Free service",
            "Available on mobile",
        ],
        forbidden_topics=[
            "Competitor pricing",
        ],
        primary_cta="https://example.com/test",
        tracking_params="?utm_source=test&utm_medium=test",
        subreddits_tier1=["podcasts", "test"],
        subreddits_tier2=["truecrimepodcasts"],
        subreddits_tier3=[],
    )


@pytest.fixture
def temp_brands_dir(tmp_path: Path) -> Path:
    """Create a temporary brands directory with test data."""
    brands_dir = tmp_path / "brands"
    brands_dir.mkdir()

    # Create test brand directory
    test_brand_dir = brands_dir / "test_brand"
    test_brand_dir.mkdir()

    # Create test brand config
    config_data = {
        "brand_name": "Test Brand",
        "company_description": "A test brand",
        "voice_guidelines": "Be helpful and friendly",
        "tone_attributes": ["friendly", "helpful"],
        "allowed_claims": ["Free service"],
        "forbidden_topics": ["Competitor pricing"],
        "primary_cta": "https://example.com/test",
        "tracking_params": "?utm_source=test",
        "subreddits_tier1": ["podcasts"],
        "subreddits_tier2": [],
        "subreddits_tier3": [],
    }

    config_path = test_brand_dir / "config.yaml"
    with config_path.open("w") as f:
        yaml.dump(config_data, f)

    # Create knowledge directory with sample file
    knowledge_dir = test_brand_dir / "knowledge"
    knowledge_dir.mkdir()

    sample_knowledge = knowledge_dir / "features.md"
    with sample_knowledge.open("w") as f:
        f.write("# Test Features\n\nThis is test knowledge content.")

    return brands_dir


@pytest.fixture
def mock_reddit_client():
    """Create a mock Reddit client."""
    mock = Mock()
    mock.search.return_value = []
    mock.submission.return_value.reply.return_value.id = "mock_reply_123"
    return mock


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    mock = Mock()
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = "This is a test response from Claude."
    mock.messages.create.return_value = mock_response
    return mock
