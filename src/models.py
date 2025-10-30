"""Core data models for the marketing agent."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


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
