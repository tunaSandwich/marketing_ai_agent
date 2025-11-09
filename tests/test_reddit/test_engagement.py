"""Tests for unified engagement system."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.reddit.engagement import RedditEngagementManager
from src.reddit.engagement_strategy import EngagementStrategyManager
from src.reddit.subreddit_selector import SubredditSelector
from src.models import (
    AccountState,
    AccountHealth,
    ActivityBudget,
    CommentConstraints,
    ComplexityLevel,
    RiskTolerance,
    BrandConfig,
)
from src.utils.config import RedditConfig, LLMConfig


@pytest.fixture
def reddit_config():
    """Mock Reddit configuration."""
    return RedditConfig(
        client_id="test_id",
        client_secret="test_secret",
        user_agent="test_agent",
        username="test_user",
        password="test_pass",
    )


@pytest.fixture
def llm_config():
    """Mock LLM configuration."""
    return LLMConfig(
        api_key="test_key",
        model="claude-3-haiku-20240307",
        max_tokens=150,
        temperature=0.9,
    )


@pytest.fixture
def brand_config():
    """Mock brand configuration."""
    return BrandConfig(
        brand_id="goodpods",
        brand_name="Goodpods",
        company_description="Social podcast player",
        voice_guidelines="Helpful and friendly",
        tone_attributes=["friendly"],
        allowed_claims=["Free podcast player"],
        forbidden_topics=["Competitor comparisons"],
        primary_cta="https://apps.apple.com/us/app/goodpods-podcast-player/id1483407582",
        tracking_params="",
        subreddits_tier1=["podcasts", "podcast"],
        subreddits_tier2=["TrueCrimePodcasts"],
        subreddits_tier3=["AudioDrama"],
    )


class TestEngagementStrategyManager:
    """Test engagement strategy manager."""
    
    def test_health_score_calculation(self):
        """Test health score calculation."""
        manager = EngagementStrategyManager()
        
        # New account
        score = manager.calculate_health_score(karma=0, age_days=0)
        assert score == 5.0
        
        # Building account
        score = manager.calculate_health_score(karma=50, age_days=15)
        assert 45 < score < 55
        
        # Ready account
        score = manager.calculate_health_score(karma=100, age_days=30)
        assert score >= 95.0
    
    def test_account_state_mapping(self):
        """Test account state determination."""
        manager = EngagementStrategyManager()
        
        assert manager.get_account_state(10) == AccountState.NEW
        assert manager.get_account_state(40) == AccountState.BUILDING
        assert manager.get_account_state(60) == AccountState.MATURING
        assert manager.get_account_state(85) == AccountState.READY
        assert manager.get_account_state(95) == AccountState.ACTIVE
    
    def test_activity_budget_new_account(self):
        """Test activity budget for new account."""
        manager = EngagementStrategyManager()
        budget = manager.get_activity_budget(10, AccountState.NEW)
        
        assert 15 <= budget.upvotes_target <= 20
        assert 2 <= budget.comments_target <= 3
        assert budget.promotional_ratio == 0.0
        assert budget.risk_tolerance == RiskTolerance.LOW
        assert budget.allowed_tiers == [1]
    
    def test_activity_budget_active_account(self):
        """Test activity budget for active account."""
        manager = EngagementStrategyManager()
        budget = manager.get_activity_budget(95, AccountState.ACTIVE)
        
        assert 5 <= budget.upvotes_target <= 10
        assert 1 <= budget.comments_target <= 2
        assert budget.promotional_ratio == 0.10
        assert budget.risk_tolerance == RiskTolerance.HIGH


class TestSubredditSelector:
    """Test subreddit selector."""
    
    def test_select_subreddit_tier1_only(self):
        """Test selecting from tier 1 only."""
        selector = SubredditSelector(
            tier1_subreddits=["podcasts", "podcast"],
            tier2_subreddits=["TrueCrimePodcasts"],
            tier3_subreddits=[],
        )
        
        selected = selector.select_subreddit(allowed_tiers=[1])
        assert selected in ["podcasts", "podcast"]
    
    def test_cooldown_tracking(self):
        """Test cooldown prevents immediate reuse."""
        selector = SubredditSelector(
            tier1_subreddits=["podcasts", "podcast"],
            tier2_subreddits=[],
            tier3_subreddits=[],
        )
        
        first = selector.select_subreddit(allowed_tiers=[1])
        assert not selector._is_available(first)


class TestRedditEngagementManager:
    """Test main engagement manager."""
    
    @patch('src.reddit.engagement.praw.Reddit')
    @patch('src.reddit.engagement.ClaudeClient')
    @patch('src.reddit.engagement.KnowledgeRetriever')
    def test_validate_helpful_comment_success(
        self,
        mock_retriever,
        mock_client,
        mock_reddit,
        reddit_config,
        llm_config,
        brand_config,
    ):
        """Test helpful comment validation."""
        mock_retriever_instance = Mock()
        mock_retriever.return_value = mock_retriever_instance
        
        manager = RedditEngagementManager(
            reddit_config=reddit_config,
            llm_config=llm_config,
            brand_config=brand_config,
        )
        
        valid_comments = [
            "try Criminal for true crime podcasts",
            "honestly Serial is still great for this",
            "check out Morbid - perfect for true crime fans",
        ]
        
        for comment in valid_comments:
            assert manager._validate_helpful_comment(comment)
    
    @patch('src.reddit.engagement.praw.Reddit')
    @patch('src.reddit.engagement.ClaudeClient')
    @patch('src.reddit.engagement.KnowledgeRetriever')
    def test_validate_helpful_comment_blocks_brand(
        self,
        mock_retriever,
        mock_client,
        mock_reddit,
        reddit_config,
        llm_config,
        brand_config,
    ):
        """Test helpful comment blocks brand mentions."""
        mock_retriever_instance = Mock()
        mock_retriever.return_value = mock_retriever_instance
        
        manager = RedditEngagementManager(
            reddit_config=reddit_config,
            llm_config=llm_config,
            brand_config=brand_config,
        )
        
        blocked_comments = [
            "try Goodpods app for organizing podcasts",
            "check out this podcast player",
        ]
        
        for comment in blocked_comments:
            assert not manager._validate_helpful_comment(comment)
    
    @patch('src.reddit.engagement.praw.Reddit')
    @patch('src.reddit.engagement.ClaudeClient')
    @patch('src.reddit.engagement.KnowledgeRetriever')
    def test_validate_promotional_comment(
        self,
        mock_retriever,
        mock_client,
        mock_reddit,
        reddit_config,
        llm_config,
        brand_config,
    ):
        """Test promotional comment validation."""
        mock_retriever_instance = Mock()
        mock_retriever.return_value = mock_retriever_instance
        
        manager = RedditEngagementManager(
            reddit_config=reddit_config,
            llm_config=llm_config,
            brand_config=brand_config,
        )
        
        # Valid: organization/feature comment (no podcast names needed)
        valid_organization = "honestly i organize all my podcasts in goodpods now. makes commuting way easier. you can import from spotify too"
        assert manager._validate_promotional_comment(valid_organization)
        
        # Valid: with podcast recommendations (should also work)
        valid_podcasts = "honestly try Criminal for true crime. i organize everything in goodpods now - makes finding episodes way easier"
        assert manager._validate_promotional_comment(valid_podcasts)
        
        # Invalid: no brand mention
        invalid_no_brand = "try Serial for true crime. Criminal is also great."
        assert not manager._validate_promotional_comment(invalid_no_brand)
        
        # Invalid: too many brand mentions
        invalid_too_many = "goodpods is great. i use goodpods every day. download goodpods now."
        assert not manager._validate_promotional_comment(invalid_too_many)
        
        # Invalid: not personal enough
        invalid_no_personal = "Goodpods is a great app for podcasts. It has many features."
        assert not manager._validate_promotional_comment(invalid_no_personal)
    
    @patch('src.reddit.engagement.praw.Reddit')
    @patch('src.reddit.engagement.ClaudeClient')
    @patch('src.reddit.engagement.KnowledgeRetriever')
    def test_get_account_health(
        self,
        mock_retriever,
        mock_client,
        mock_reddit,
        reddit_config,
        llm_config,
        brand_config,
    ):
        """Test account health calculation."""
        # Mock Reddit user
        mock_user = Mock()
        mock_user.link_karma = 50
        mock_user.comment_karma = 50
        mock_user.created_utc = 1234567890.0  # Some timestamp
        
        mock_reddit_instance = Mock()
        mock_reddit_instance.redditor.return_value = mock_user
        mock_reddit.return_value = mock_reddit_instance
        
        mock_retriever_instance = Mock()
        mock_retriever.return_value = mock_retriever_instance
        
        manager = RedditEngagementManager(
            reddit_config=reddit_config,
            llm_config=llm_config,
            brand_config=brand_config,
        )
        
        health = manager.get_account_health()
        
        assert health.karma == 100  # 50 + 50
        assert health.age_days > 0
        assert 0 <= health.health_score <= 100
        assert health.account_state in AccountState
    
    @patch('src.reddit.engagement.praw.Reddit')
    @patch('src.reddit.engagement.ClaudeClient')
    @patch('src.reddit.engagement.KnowledgeRetriever')
    def test_find_eligible_post(
        self,
        mock_retriever,
        mock_client,
        mock_reddit,
        reddit_config,
        llm_config,
        brand_config,
    ):
        """Test finding eligible posts."""
        # Mock posts
        mock_post1 = Mock()
        mock_post1.author.name = "other_user"
        mock_post1.locked = False
        mock_post1.archived = False
        mock_post1.score = 10
        mock_post1.title = "Looking for podcast recommendations"
        mock_post1.comments.replace_more = Mock()
        mock_post1.comments.list.return_value = []
        
        mock_post2 = Mock()
        mock_post2.author.name = "test_user"  # Own post
        mock_post2.title = "My recommendation"
        
        # Mock subreddit
        mock_subreddit = Mock()
        mock_subreddit.new.return_value = [mock_post1, mock_post2]
        
        mock_reddit_instance = Mock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance
        
        mock_retriever_instance = Mock()
        mock_retriever.return_value = mock_retriever_instance
        
        manager = RedditEngagementManager(
            reddit_config=reddit_config,
            llm_config=llm_config,
            brand_config=brand_config,
        )
        
        budget = ActivityBudget(
            upvotes_target=5,
            comments_target=1,
            promotional_ratio=0.0,
            risk_tolerance=RiskTolerance.LOW,
            allowed_tiers=[1],
            max_posts_per_subreddit_per_day=3,
            comment_constraints=CommentConstraints(
                max_length=150,
                min_post_score=5,
                allow_follow_up_questions=False,
                allow_thread_replies=False,
                complexity_level=ComplexityLevel.SIMPLE,
            ),
        )
        
        eligible_post = manager._find_eligible_post("podcasts", budget)
        
        # Should find the first post (not own post)
        assert eligible_post == mock_post1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])