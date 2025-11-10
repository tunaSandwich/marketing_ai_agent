"""Core data models for the marketing agent."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


# =============================================================================
# LLM Model Configuration
# =============================================================================

class ClaudeModel(str, Enum):
    """Available Claude models with their API identifiers."""
    
    # Working models (verified as of November 2024)
    HAIKU = "claude-3-haiku-20240307"  # Fast, economical
    OPUS = "claude-3-opus-20240229"    # Most capable, expensive
    
    # Legacy models (no longer available)
    # SONNET_LEGACY = "claude-3-sonnet-20240229"  # DEPRECATED
    # SONNET_35 = "claude-3-5-sonnet-20240620"    # DEPRECATED


# Default model for the application
DEFAULT_MODEL = ClaudeModel.HAIKU

# Model configurations with performance characteristics
MODEL_CONFIGS = {
    ClaudeModel.HAIKU: {
        "name": "Claude 3 Haiku",
        "description": "Fast and economical model for general tasks",
        "cost_tier": "low",
        "speed": "fast",
        "max_tokens_recommended": 300,
        "temperature_recommended": 0.7,
    },
    ClaudeModel.OPUS: {
        "name": "Claude 3 Opus", 
        "description": "Most capable model for complex reasoning",
        "cost_tier": "high",
        "speed": "slow",
        "max_tokens_recommended": 500,
        "temperature_recommended": 0.7,
    },
}


def get_default_model() -> str:
    """Get the default model identifier."""
    return DEFAULT_MODEL.value


def get_model_config(model: ClaudeModel) -> dict:
    """Get configuration for a specific model."""
    return MODEL_CONFIGS.get(model, MODEL_CONFIGS[DEFAULT_MODEL])


def is_model_available(model_name: str) -> bool:
    """Check if a model name is in our available models list."""
    return model_name in [model.value for model in ClaudeModel]


# =============================================================================
# Core Data Models
# =============================================================================


class RedditPost(BaseModel):
    """Reddit post data model."""

    id: str = Field(..., description="Reddit post ID")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post body content")
    subreddit: str = Field(..., description="Subreddit name without r/ prefix")
    score: int = Field(..., description="Post score (upvotes - downvotes)")
    created_at: datetime = Field(..., description="Post creation timestamp")
    url: str = Field(..., description="Full URL to the post")
    author: str = Field(..., description="Post author username")
    num_comments: int = Field(default=0, description="Number of comments")


class GeneratedResponse(BaseModel):
    """Generated response data model."""

    id: str = Field(..., description="Unique response ID")
    content: str = Field(..., description="Response content")
    post_id: str = Field(..., description="Target Reddit post ID")
    brand_id: str = Field(..., description="Brand pack ID used")
    created_at: datetime = Field(default_factory=datetime.now)

    # Generation metadata
    model_used: str = Field(..., description="LLM model used")
    prompt_template: str = Field(..., description="Prompt template version")
    rag_chunks_used: int = Field(default=0, description="Number of RAG chunks used")
    generation_time_ms: int = Field(..., description="Generation time in milliseconds")


class EvaluationResult(BaseModel):
    """Response evaluation result."""

    response_id: str = Field(..., description="Response being evaluated")
    relevance_score: int = Field(..., ge=0, le=10, description="Relevance to original request")
    helpfulness_score: int = Field(..., ge=0, le=10, description="Genuine value provided")
    naturalness_score: int = Field(..., ge=0, le=10, description="Sounds human, not robotic")
    brand_safety_score: int = Field(..., ge=0, le=10, description="Follows brand guidelines")
    cta_subtlety_score: int = Field(..., ge=0, le=10, description="CTA is natural, not pushy")

    feedback: str | None = Field(None, description="Detailed feedback")
    evaluated_at: datetime = Field(default_factory=datetime.now)

    @property
    def total_score(self) -> int:
        """Calculate total evaluation score."""
        return (
            self.relevance_score
            + self.helpfulness_score
            + self.naturalness_score
            + self.brand_safety_score
            + self.cta_subtlety_score
        )


class RoutingDecision(str, Enum):
    """Response routing decision."""

    AUTO_POST = "auto_post"
    HUMAN_REVIEW = "human_review"
    REJECT = "reject"


class ProcessingResult(BaseModel):
    """Result of processing a Reddit post."""

    post_id: str = Field(..., description="Reddit post ID")
    response: GeneratedResponse | None = Field(None, description="Generated response")
    evaluation: EvaluationResult | None = Field(None, description="Evaluation result")
    routing_decision: RoutingDecision = Field(..., description="Routing decision")
    error: str | None = Field(None, description="Error message if processing failed")
    processed_at: datetime = Field(default_factory=datetime.now)


class ReplyResult(BaseModel):
    """Result of posting a reply to Reddit."""

    reply_id: str = Field(..., description="Reddit comment ID")
    reply_url: str = Field(..., description="URL to the posted comment")
    posted_at: datetime = Field(default_factory=datetime.now)
    response_id: str = Field(..., description="Original response ID")


class RedditMetrics(BaseModel):
    """Metrics for a Reddit reply."""

    reply_id: str = Field(..., description="Reddit comment ID")
    upvotes: int = Field(default=0, description="Number of upvotes")
    downvotes: int = Field(default=0, description="Number of downvotes")
    replies_received: int = Field(default=0, description="Number of replies received")
    clicks_tracked: int = Field(default=0, description="Number of tracked link clicks")
    last_updated: datetime = Field(default_factory=datetime.now)


class BrandConfig(BaseModel):
    """Brand pack configuration model."""

    brand_id: str = Field(..., description="Unique brand identifier")
    brand_name: str = Field(..., description="Display name")
    company_description: str = Field(..., description="Company description")
    voice_guidelines: str = Field(..., description="Voice and tone guidelines")
    tone_attributes: list[str] = Field(..., description="Tone attributes")
    allowed_claims: list[str] = Field(..., description="Allowed marketing claims")
    forbidden_topics: list[str] = Field(..., description="Topics to avoid")
    primary_cta: HttpUrl = Field(..., description="Primary call-to-action URL")
    tracking_params: str = Field(..., description="UTM tracking parameters")
    subreddits_tier1: list[str] = Field(..., description="Primary target subreddits")
    subreddits_tier2: list[str] = Field(default_factory=list, description="Secondary subreddits")
    subreddits_tier3: list[str] = Field(default_factory=list, description="Tertiary subreddits")


class DiscoveryQuery(BaseModel):
    """Reddit discovery query configuration."""

    base_query: str = Field(..., description="Base search query")
    intent_patterns: list[str] = Field(..., description="Intent patterns to match")
    exclude_patterns: list[str] = Field(..., description="Patterns to exclude")
    subreddits: list[str] = Field(..., description="Target subreddits")
    max_results: int = Field(default=20, description="Maximum results to return")
    min_score: int = Field(default=1, description="Minimum post score")
    max_age_hours: int = Field(default=24, description="Maximum post age in hours")


class DraftResponse(BaseModel):
    """A generated response awaiting review."""
    
    draft_id: str
    post: RedditPost
    response_content: str
    quality_score: float
    quality_reasoning: str
    rag_chunks_used: list[str] = []
    created_at: datetime


class AccountState(str, Enum):
    """Account state for engagement strategy."""
    NEW = "new"  # 0-25 health
    BUILDING = "building"  # 25-50 health
    MATURING = "maturing"  # 50-75 health
    READY = "ready"  # 75-90 health
    ACTIVE = "active"  # 90+ health


class RiskTolerance(str, Enum):
    """Risk tolerance for engagement activities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComplexityLevel(str, Enum):
    """Comment complexity level."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class CommentConstraints(BaseModel):
    """Constraints for comment generation based on account state."""
    
    max_length: int = Field(..., description="Maximum comment length in characters")
    min_post_score: int = Field(..., description="Minimum post score to reply to")
    allow_follow_up_questions: bool = Field(
        ..., 
        description="Whether to allow asking follow-up questions"
    )
    allow_thread_replies: bool = Field(
        ..., 
        description="Whether to allow replying to comments (vs top-level only)"
    )
    complexity_level: ComplexityLevel = Field(
        ..., 
        description="Comment complexity level"
    )


class ActivityBudget(BaseModel):
    """Activity budget for one engagement cycle."""
    
    upvotes_target: int = Field(..., description="Number of posts to upvote")
    comments_target: int = Field(..., description="Number of comments to post")
    promotional_ratio: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Ratio of promotional to helpful content"
    )
    risk_tolerance: RiskTolerance = Field(
        ..., 
        description="Risk tolerance for this cycle"
    )
    allowed_tiers: List[int] = Field(
        ..., 
        description="Allowed subreddit tiers (1, 2, 3)"
    )
    max_posts_per_subreddit_per_day: int = Field(
        ..., 
        description="Maximum posts per subreddit per day"
    )
    comment_constraints: CommentConstraints = Field(
        ..., 
        description="Comment generation constraints"
    )


class EngagementCycleResult(BaseModel):
    """Result of an engagement cycle."""
    
    cycle_type: str = Field(..., description="Type of cycle (engagement or discovery)")
    health_score: float = Field(..., description="Account health score at cycle start")
    account_state: AccountState = Field(..., description="Account state")
    subreddit: Optional[str] = Field(None, description="Target subreddit")
    upvotes_completed: int = Field(default=0, description="Number of upvotes completed")
    helpful_comments_posted: List[str] = Field(
        default_factory=list, 
        description="IDs of helpful comments posted"
    )
    promotional_comments_posted: List[str] = Field(
        default_factory=list, 
        description="IDs of promotional comments posted"
    )
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    completed_at: datetime = Field(default_factory=datetime.now)


class AccountHealth(BaseModel):
    """Account health metrics."""
    
    karma: int = Field(..., description="Current karma")
    age_days: float = Field(..., description="Account age in days")
    recent_activity_quality: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0, 
        description="Quality score of recent activity"
    )
    health_score: float = Field(
        ..., 
        ge=0.0, 
        le=100.0, 
        description="Overall health score"
    )
    account_state: AccountState = Field(..., description="Current account state")
