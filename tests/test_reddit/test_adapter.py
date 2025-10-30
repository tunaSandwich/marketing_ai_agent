"""Tests for Reddit adapter."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.reddit.adapter import RedditAdapter
from src.utils.config import RedditConfig


class TestRedditAdapter:
    """Tests for RedditAdapter class."""

    @pytest.fixture
    def reddit_config(self):
        """Create a Reddit config for testing."""
        return RedditConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            user_agent="test_agent",
            username="test_user",
            password="test_password",
            rate_limit_per_minute=60,
        )

    @pytest.fixture
    def reddit_adapter(self, reddit_config):
        """Create a Reddit adapter for testing."""
        with patch("src.reddit.adapter.praw.Reddit"):
            adapter = RedditAdapter(reddit_config)
            adapter._reddit = Mock()
            return adapter

    def test_reddit_adapter_initialization(self, reddit_config):
        """Test Reddit adapter initialization."""
        with patch("src.reddit.adapter.praw.Reddit") as mock_praw:
            RedditAdapter(reddit_config)

            mock_praw.assert_called_once_with(
                client_id="test_client_id",
                client_secret="test_client_secret",
                user_agent="test_agent",
                username="test_user",
                password="test_password",
            )

    def test_validate_post_eligibility_recent_post(self, reddit_adapter, sample_reddit_post):
        """Test post eligibility validation for recent post."""
        # Recent post should be eligible
        sample_reddit_post.created_at = datetime.now(UTC) - timedelta(hours=1)
        sample_reddit_post.score = 5
        sample_reddit_post.author = "valid_user"

        is_eligible = reddit_adapter.validate_post_eligibility(sample_reddit_post)
        assert is_eligible is True

    def test_validate_post_eligibility_old_post(self, reddit_adapter, sample_reddit_post):
        """Test post eligibility validation for old post."""
        # Old post should not be eligible
        sample_reddit_post.created_at = datetime.now(UTC) - timedelta(hours=25)

        is_eligible = reddit_adapter.validate_post_eligibility(sample_reddit_post)
        assert is_eligible is False

    def test_validate_post_eligibility_low_score(self, reddit_adapter, sample_reddit_post):
        """Test post eligibility validation for low score post."""
        # Low score post should not be eligible
        sample_reddit_post.score = 0

        is_eligible = reddit_adapter.validate_post_eligibility(sample_reddit_post)
        assert is_eligible is False

    def test_validate_post_eligibility_deleted_author(self, reddit_adapter, sample_reddit_post):
        """Test post eligibility validation for deleted author."""
        # Deleted author post should not be eligible
        sample_reddit_post.author = "[deleted]"

        is_eligible = reddit_adapter.validate_post_eligibility(sample_reddit_post)
        assert is_eligible is False

    def test_rate_limiting_enforcement(self, reddit_adapter):
        """Test that rate limiting is enforced."""
        # This is a basic test - full implementation would require more complex mocking
        reddit_adapter._enforce_rate_limit()

        # Should not raise an exception
        assert reddit_adapter._last_request_time is not None

    @patch("time.sleep")
    def test_rate_limiting_with_sleep(self, mock_sleep, reddit_adapter):
        """Test rate limiting when sleep is required."""
        # Set a recent request time to trigger sleep
        reddit_adapter._last_request_time = datetime.now(UTC) - timedelta(seconds=0.5)

        reddit_adapter._enforce_rate_limit()

        # Should have called sleep
        mock_sleep.assert_called_once()

    def test_check_karma_requirements_mock(self, reddit_adapter):
        """Test karma requirements check with mocked Reddit."""
        # Mock user with sufficient karma
        mock_user = Mock()
        mock_user.comment_karma = 150
        mock_user.link_karma = 50
        mock_user.created_utc = (datetime.now(UTC) - timedelta(days=100)).timestamp()

        reddit_adapter._reddit.user.me.return_value = mock_user

        result = reddit_adapter.check_karma_requirements("test")
        assert result is True

    def test_check_karma_requirements_insufficient(self, reddit_adapter):
        """Test karma requirements check with insufficient karma."""
        # Mock user with insufficient karma
        mock_user = Mock()
        mock_user.comment_karma = 10
        mock_user.link_karma = 5
        mock_user.created_utc = (datetime.now(UTC) - timedelta(days=100)).timestamp()

        reddit_adapter._reddit.user.me.return_value = mock_user

        result = reddit_adapter.check_karma_requirements("test")
        assert result is False
