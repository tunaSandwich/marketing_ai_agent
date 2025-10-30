"""Tests for core data models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.models import (
    BrandConfig,
    EvaluationResult,
    GeneratedResponse,
    RedditPost,
    RoutingDecision,
)


class TestRedditPost:
    """Tests for RedditPost model."""

    def test_reddit_post_creation(self):
        """Test creating a valid Reddit post."""
        post = RedditPost(
            id="abc123",
            title="Test title",
            content="Test content",
            subreddit="test",
            score=10,
            created_at=datetime.now(UTC),
            url="https://reddit.com/test",
            author="test_user",
        )

        assert post.id == "abc123"
        assert post.title == "Test title"
        assert post.subreddit == "test"

    def test_reddit_post_validation_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError):
            RedditPost()  # Missing required fields

    def test_reddit_post_defaults(self):
        """Test default values."""
        post = RedditPost(
            id="test",
            title="test",
            content="test",
            subreddit="test",
            score=1,
            created_at=datetime.now(UTC),
            url="https://test.com",
            author="test",
        )

        assert post.num_comments == 0  # Default value


class TestGeneratedResponse:
    """Tests for GeneratedResponse model."""

    def test_generated_response_creation(self):
        """Test creating a valid generated response."""
        response = GeneratedResponse(
            id="resp123",
            content="Test response content",
            post_id="post123",
            brand_id="test_brand",
            model_used="claude-sonnet-4-20250514-sonnet",
            prompt_template="v1.0",
            generation_time_ms=1500,
        )

        assert response.id == "resp123"
        assert response.content == "Test response content"
        assert response.model_used == "claude-sonnet-4-20250514-sonnet"

    def test_generated_response_defaults(self):
        """Test default values."""
        response = GeneratedResponse(
            id="test",
            content="test",
            post_id="test",
            brand_id="test",
            model_used="test",
            prompt_template="test",
            generation_time_ms=100,
        )

        assert response.rag_chunks_used == 0  # Default value
        assert isinstance(response.created_at, datetime)


class TestEvaluationResult:
    """Tests for EvaluationResult model."""

    def test_evaluation_result_creation(self):
        """Test creating a valid evaluation result."""
        evaluation = EvaluationResult(
            response_id="resp123",
            relevance_score=8,
            helpfulness_score=9,
            naturalness_score=7,
            brand_safety_score=10,
            cta_subtlety_score=6,
        )

        assert evaluation.relevance_score == 8
        assert evaluation.total_score == 40  # 8+9+7+10+6

    def test_evaluation_score_validation(self):
        """Test score validation (0-10 range)."""
        with pytest.raises(ValidationError):
            EvaluationResult(
                response_id="test",
                relevance_score=15,  # Invalid: > 10
                helpfulness_score=5,
                naturalness_score=5,
                brand_safety_score=5,
                cta_subtlety_score=5,
            )

        with pytest.raises(ValidationError):
            EvaluationResult(
                response_id="test",
                relevance_score=-1,  # Invalid: < 0
                helpfulness_score=5,
                naturalness_score=5,
                brand_safety_score=5,
                cta_subtlety_score=5,
            )

    def test_total_score_calculation(self):
        """Test total score calculation."""
        evaluation = EvaluationResult(
            response_id="test",
            relevance_score=10,
            helpfulness_score=10,
            naturalness_score=10,
            brand_safety_score=10,
            cta_subtlety_score=10,
        )

        assert evaluation.total_score == 50


class TestBrandConfig:
    """Tests for BrandConfig model."""

    def test_brand_config_creation(self, sample_brand_config):
        """Test creating a valid brand config."""
        config = sample_brand_config

        assert config.brand_id == "test_brand"
        assert config.brand_name == "Test Brand"
        assert len(config.allowed_claims) == 2
        assert "podcasts" in config.subreddits_tier1

    def test_brand_config_validation_url(self):
        """Test URL validation for primary_cta."""
        with pytest.raises(ValidationError):
            BrandConfig(
                brand_id="test",
                brand_name="Test",
                company_description="Test",
                voice_guidelines="Test",
                tone_attributes=["test"],
                allowed_claims=["test"],
                forbidden_topics=["test"],
                primary_cta="not-a-valid-url",  # Invalid URL
                tracking_params="?test=test",
                subreddits_tier1=["test"],
            )


class TestRoutingDecision:
    """Tests for RoutingDecision enum."""

    def test_routing_decision_values(self):
        """Test routing decision enum values."""
        assert RoutingDecision.AUTO_POST == "auto_post"
        assert RoutingDecision.HUMAN_REVIEW == "human_review"
        assert RoutingDecision.REJECT == "reject"
