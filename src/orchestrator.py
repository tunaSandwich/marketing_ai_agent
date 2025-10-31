"""Main orchestration for growth agent."""

import random
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger

from src.brand.loader import BrandLoader
from src.llm.client import ClaudeClient
from src.llm.prompts import PromptTemplate
from src.models import DraftResponse, RedditPost, ReviewStatus
from src.rag.retriever import KnowledgeRetriever
from src.reddit.adapter import RedditAdapter
from src.reddit.engagement import RedditEngagement
from src.reddit.poster import RedditPoster
from src.reddit.warmup import AccountWarmer
from src.review.queue import ReviewQueue
from src.utils.config import get_settings


def score_response(response: str, post_title: str) -> tuple[float, str]:
    """Score response quality 0-10.
    
    Args:
        response: Generated response text
        post_title: Original post title
        
    Returns:
        Tuple of (score, reasoning)
    """
    score = 5.0
    reasons = []
    
    # +2 if mentions specific podcast names
    podcast_indicators = ["'", '"', "podcast", "Podcast"]
    if sum(1 for indicator in podcast_indicators if indicator in response) >= 2:
        score += 2
        reasons.append("mentions specific shows")
    
    # +1 if concise
    word_count = len(response.split())
    if 30 < word_count < 200:
        score += 1
        reasons.append("concise length")
    
    # +1 if includes CTA
    if "goodpods.app" in response.lower():
        score += 1
        reasons.append("includes CTA")
    
    # +1 if conversational
    conversational = ["i ", "you", "!", "really", "tbh", "honestly"]
    if any(word in response.lower() for word in conversational):
        score += 1
        reasons.append("conversational tone")
    
    # -2 if too salesy
    salesy = ["our app", "download now", "sign up"]
    if sum(1 for word in salesy if word in response.lower()) >= 2:
        score -= 2
        reasons.append("too promotional")
    
    final_score = min(10.0, max(0.0, score))
    reason_text = " • ".join(reasons) if reasons else "baseline"
    
    return final_score, reason_text


class GrowthOrchestrator:
    """Orchestrates discovery, generation, and posting."""
    
    def __init__(self, brand_id: str = "goodpods"):
        """Initialize orchestrator.
        
        Args:
            brand_id: Brand to run agent for
        """
        self.brand_id = brand_id
        self.settings = get_settings()
        
        # Initialize components
        self.reddit = RedditAdapter(self.settings.reddit)
        self.poster = RedditPoster(self.settings.reddit)
        self.engagement = RedditEngagement(self.settings.reddit)
        self.warmer = AccountWarmer(self.settings.reddit)
        self.claude = ClaudeClient(self.settings.llm)
        
        # Load brand config
        brands_dir = Path(__file__).parent.parent / "brands"
        brand_loader = BrandLoader(brands_dir)
        self.brand_config = brand_loader.load_brand_config(brand_id)
        
        # Initialize RAG
        index_dir = brands_dir / brand_id / "index"
        if index_dir.exists():
            self.retriever = KnowledgeRetriever(index_dir)
            logger.info("RAG retriever initialized")
        else:
            self.retriever = None
            logger.warning("No RAG index found")
        
        # Initialize review queue
        queue_dir = Path(__file__).parent.parent / "data" / "review_queue"
        self.queue = ReviewQueue(queue_dir)
        
        self.prompt_template = PromptTemplate()
        
        logger.info(f"Orchestrator initialized for brand: {brand_id}")
    
    def discover_opportunities(self, limit: int = 10) -> List[RedditPost]:
        """Discover podcast recommendation opportunities.
        
        Args:
            limit: Maximum opportunities to return
            
        Returns:
            List of Reddit posts
        """
        logger.info("Starting discovery...")
        
        query = '(title:"looking for" OR title:"recommend" OR title:"suggestions") AND podcast'
        
        posts = self.reddit.search_posts(
            query=query,
            subreddits=["podcasts"],
            limit=limit * 2,
            time_filter="day",
        )
        
        # Filter and rank by engagement
        eligible = []
        for post in posts:
            engagement = post.score + (post.num_comments * 2)
            eligible.append((engagement, post))
        
        eligible.sort(reverse=True, key=lambda x: x[0])
        top_posts = [post for _, post in eligible[:limit]]
        
        logger.info(f"Found {len(top_posts)} opportunities")
        return top_posts
    
    def generate_response(self, post: RedditPost) -> DraftResponse:
        """Generate response for a post.
        
        Args:
            post: Reddit post to respond to
            
        Returns:
            Draft response
        """
        draft_id = f"draft_{uuid.uuid4().hex[:12]}"
        
        # Retrieve relevant knowledge
        rag_content = ""
        rag_chunks = []
        
        if self.retriever:
            chunks = self.retriever.retrieve_for_post(
                post.title,
                post.content,
                top_k=3,
                min_similarity=0.3,
            )
            
            if chunks:
                rag_content = "\n\n".join([
                    f"[{chunk.filename}]\n{chunk.content}"
                    for chunk in chunks
                ])
                rag_chunks = [chunk.filename for chunk in chunks]
        
        # Generate response
        prompt = self.prompt_template.create_response_prompt(
            post=post,
            brand_config=self.brand_config,
            rag_content=rag_content,
            context={"intent": "recommendation_request"},
        )
        
        response = self.claude.generate_response(
            prompt=prompt,
            post_id=post.id,
            brand_id=self.brand_id,
            response_id=draft_id,
            prompt_template="production_v1",
        )
        
        # Score response
        quality_score, reasoning = score_response(response.content, post.title)
        
        # Create draft
        draft = DraftResponse(
            draft_id=draft_id,
            post=post,
            response_content=response.content,
            quality_score=quality_score,
            quality_reasoning=reasoning,
            rag_chunks_used=rag_chunks,
            created_at=datetime.now(UTC),
        )
        
        logger.info(
            f"Generated draft {draft_id} with quality score {quality_score:.1f}/10"
        )
        
        return draft
    
    def run_discovery_cycle(self) -> dict:
        """Run discovery and generation, or warming if account not ready."""
        logger.info("=" * 60)
        logger.info("Starting cycle")
        
        # Check account health
        health = self.poster.check_account_health()
        
        # If account doesn't meet requirements, enter warming mode
        if not health.get("can_post"):
            reason = health.get("reason", "Unknown")
            logger.warning(f"Account cannot post: {reason}")
            logger.info("🌱 Entering ACCOUNT WARMING MODE")
            
            # Run warming cycle
            warming_result = self.warmer.run_warming_cycle(
                current_karma=health.get("karma", 0),
                current_age_days=health.get("account_age_days", 0),
            )
            
            return {
                "mode": "warming",
                "reason": reason,
                "warming_result": warming_result,
            }
        
        # Otherwise, proceed with normal discovery + posting
        logger.info("🚀 Account ready - running discovery + posting cycle")
        
        # Check 10% rule
        activity = self.poster.get_recent_activity()
        if not activity.get("safe_to_post"):
            logger.warning("Promotional ratio too high, skipping cycle")
            return {"skipped": "10% rule violation"}
        
        # Discover opportunities
        opportunities = self.discover_opportunities(limit=5)
        
        if not opportunities:
            logger.info("No opportunities found")
            return {"opportunities": 0, "drafted": 0, "auto_posted": 0}
        
        # Generate responses and auto-post high-quality ones
        drafted = 0
        auto_posted = 0
        queued_for_review = 0
        auto_rejected = 0
        
        for opp in opportunities:
            try:
                draft = self.generate_response(opp)
                drafted += 1
                
                # Enhanced safety logging before decision
                logger.info("=" * 60)
                logger.info(f"SAFETY CHECK for draft {draft.draft_id}")
                logger.info(f"  Quality Score: {draft.quality_score:.1f}/10")
                logger.info(f"  Quality Reasoning: {draft.quality_reasoning}")
                logger.info(f"  RAG Chunks Used: {draft.rag_chunks_used}")
                logger.info(f"  Account Karma: {health.get('karma', 0)}")
                logger.info(f"  Promotional Ratio: {activity.get('promotional_ratio', 0):.1%}")
                logger.info(f"  Post: r/{draft.post.subreddit} - {draft.post.title[:50]}...")
                logger.info("=" * 60)
                
                # Decision logic based on quality score
                if draft.quality_score >= 8.0:
                    # AUTO-POST: High quality, all safety checks passed
                    logger.info(
                        f"✅ Draft {draft.draft_id} scored {draft.quality_score:.1f}/10 - AUTO-POSTING"
                    )
                    
                    # Attempt to post
                    comment_id = self.poster.post_reply(
                        post_id=draft.post.id,
                        comment_text=draft.response_content,
                        draft_id=draft.draft_id,
                    )
                    
                    if comment_id:
                        draft.status = ReviewStatus.POSTED
                        draft.posted_comment_id = comment_id
                        draft.posted_at = datetime.now(UTC)
                        # Save to posted directory
                        file_path = self.queue.posted_dir / f"{draft.draft_id}.json"
                        with file_path.open('w') as f:
                            import json
                            json.dump(draft.model_dump(mode='json'), f, indent=2, default=str)
                        auto_posted += 1
                        logger.info(f"🎉 Successfully posted comment {comment_id}")
                    else:
                        logger.warning(f"Failed to post draft {draft.draft_id}")
                        draft.status = ReviewStatus.FAILED
                        self.queue.add_draft(draft)
                        
                elif draft.quality_score >= 6.0:
                    # QUEUE FOR REVIEW: Medium quality
                    logger.info(
                        f"📝 Draft {draft.draft_id} scored {draft.quality_score:.1f}/10 - queuing for review"
                    )
                    self.queue.add_draft(draft)
                    queued_for_review += 1
                    
                else:
                    # AUTO-REJECT: Low quality
                    logger.info(
                        f"❌ Draft {draft.draft_id} scored {draft.quality_score:.1f}/10 - auto-rejected"
                    )
                    draft.status = ReviewStatus.REJECTED
                    draft.reviewer_notes = "Auto-rejected: quality score too low"
                    # Save to rejected directory
                    file_path = self.queue.rejected_dir / f"{draft.draft_id}.json"
                    with file_path.open('w') as f:
                        import json
                        json.dump(draft.model_dump(mode='json'), f, indent=2, default=str)
                    auto_rejected += 1
                    
            except Exception as e:
                logger.error(f"Error processing opportunity {opp.id}: {e}")
        
        stats = {
            "opportunities": len(opportunities),
            "drafted": drafted,
            "auto_posted": auto_posted,
            "queued_for_review": queued_for_review,
            "auto_rejected": auto_rejected,
            "queue_stats": self.queue.get_stats(),
        }
        
        logger.info(f"✅ Cycle complete: {stats}")
        return stats
    
    def post_approved_drafts(self, limit: int = 3) -> dict:
        """Post approved drafts to Reddit.
        
        Args:
            limit: Maximum number to post
            
        Returns:
            Dict with posting stats
        """
        logger.info("Posting approved drafts...")
        
        approved = self.queue.get_approved(limit=limit)
        
        if not approved:
            logger.info("No approved drafts to post")
            return {"posted": 0, "failed": 0}
        
        posted = 0
        failed = 0
        
        for draft in approved:
            try:
                comment_id = self.poster.post_reply(
                    post_id=draft.post.id,
                    comment_text=draft.response_content,
                    draft_id=draft.draft_id,
                )
                
                if comment_id:
                    self.queue.mark_posted(draft.draft_id, comment_id)
                    posted += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Error posting draft {draft.draft_id}: {e}")
                failed += 1
        
        result = {"posted": posted, "failed": failed}
        logger.info(f"Posting complete: {result}")
        return result
    
    def maintain_engagement_ratio(self) -> dict:
        """Maintain healthy engagement ratio with non-promotional activity.
        
        Returns:
            Dict with engagement stats
        """
        logger.info("🎯 Running engagement maintenance...")
        
        # Upvote 10-15 posts across relevant subreddits
        upvoted_posts = self.engagement.upvote_posts(
            subreddits=["podcasts", "TrueCrimePodcasts", "truecrime"],
            count=random.randint(10, 15),
        )
        
        # Upvote 5-8 helpful comments
        upvoted_comments = self.engagement.upvote_comments(
            subreddits=["podcasts", "TrueCrimePodcasts"],
            count=random.randint(5, 8),
        )
        
        # Occasionally post a casual, helpful comment (10% chance)
        casual_commented = False
        if random.random() < 0.1:  # 10% chance
            casual_commented = self.engagement.post_casual_comment()
        
        result = {
            "upvoted_posts": upvoted_posts,
            "upvoted_comments": upvoted_comments,
            "casual_commented": casual_commented,
        }
        
        logger.info(f"✅ Engagement maintenance complete: {result}")
        return result