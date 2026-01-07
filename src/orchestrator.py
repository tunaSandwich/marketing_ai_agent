"""Main orchestration for growth agent."""

import random
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import List, Optional

from loguru import logger

from src.brand.loader import BrandLoader
from src.llm.client import ClaudeClient
from src.llm.prompts import PromptTemplate
from src.models import DraftResponse, EngagementCycleResult, RedditPost
from src.rag.retriever import KnowledgeRetriever
from src.reddit.adapter import RedditAdapter
from src.reddit.engagement import RedditEngagementManager
from src.reddit.poster import RedditPoster
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
        self.claude = ClaudeClient(self.settings.llm)
        
        # Load brand config
        brands_dir = Path(__file__).parent.parent / "brands"
        brand_loader = BrandLoader(brands_dir)
        self.brand_config = brand_loader.load_brand_config(brand_id)
        
        # Initialize unified engagement manager
        self.engagement_manager = RedditEngagementManager(
            reddit_config=self.settings.reddit,
            llm_config=self.settings.llm,
            brand_config=self.brand_config,
        )
        
        # Track last discovery cycle time
        self.last_discovery_cycle = None
        
        # Initialize RAG
        index_dir = brands_dir / brand_id / "index"
        if index_dir.exists():
            self.retriever = KnowledgeRetriever(index_dir)
            logger.info("RAG retriever initialized")
        else:
            self.retriever = None
            logger.warning("No RAG index found")
        
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
    
    def run(self):
        """Main orchestration loop using unified engagement system."""
        logger.info("Starting unified engagement orchestrator...")
        
        while True:
            try:
                current_time = datetime.now()
                
                # Run engagement cycle (every 1 hour)
                logger.info("Starting engagement cycle...")
                engagement_result = self.engagement_manager.run_engagement_cycle()
                self._log_cycle_result(engagement_result)
                
                # Run discovery cycle (every 2 hours, only if active)
                if self._should_run_discovery(current_time):
                    logger.info("Starting discovery cycle...")
                    discovery_result = self.engagement_manager.run_discovery_cycle()
                    self._log_cycle_result(discovery_result)
                    self.last_discovery_cycle = current_time
                
                # Wait for next cycle (1 hour)
                self._wait_for_next_cycle()
                
            except KeyboardInterrupt:
                logger.info("Orchestrator stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in orchestrator loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error

    def _should_run_discovery(self, current_time: datetime) -> bool:
        """Determine if discovery cycle should run (every 2 hours)."""
        if self.last_discovery_cycle is None:
            return True
        
        time_since_last = (current_time - self.last_discovery_cycle).total_seconds()
        return time_since_last >= 7200  # 2 hours in seconds

    def _log_cycle_result(self, result: EngagementCycleResult):
        """Log cycle results."""
        logger.info(
            f"Cycle complete: {result.cycle_type}, "
            f"health={result.health_score:.1f}, "
            f"helpful={len(result.helpful_comments_posted)}, "
            f"promo={len(result.promotional_comments_posted)}, "
            f"errors={len(result.errors)}"
        )

    def _wait_for_next_cycle(self):
        """Wait for next engagement cycle (1 hour)."""
        wait_seconds = 3600  # 1 hour
        logger.info(f"Waiting {wait_seconds/60:.0f} minutes until next cycle...")
        time.sleep(wait_seconds)
    
    def run_discovery_cycle(self) -> dict:
        """Run a single unified cycle (scheduler-friendly).
        
        This performs:
          1) One engagement cycle
          2) One discovery cycle if due and allowed by account state
        
        Returns:
            Dict with aggregated stats for this invocation
        """
        # Engagement cycle (always)
        engagement_result = self.engagement_manager.run_engagement_cycle()
        self._log_cycle_result(engagement_result)
        
        aggregated = {
            "cycle_type": engagement_result.cycle_type,
            "health_score": engagement_result.health_score,
            "helpful_comments": len(engagement_result.helpful_comments_posted),
            "promotional_comments": len(engagement_result.promotional_comments_posted),
            "errors": len(engagement_result.errors),
            "discovery_ran": False,
        }
        
        # Discovery (every ~2 hours, ACTIVE-only)
        current_time = datetime.now()
        if self._should_run_discovery(current_time):
            discovery_result = self.engagement_manager.run_discovery_cycle()
            self._log_cycle_result(discovery_result)
            self.last_discovery_cycle = current_time
            
            # Aggregate counts
            aggregated["discovery_ran"] = discovery_result.cycle_type.startswith("discovery")
            aggregated["helpful_comments"] += len(discovery_result.helpful_comments_posted)
            aggregated["promotional_comments"] += len(discovery_result.promotional_comments_posted)
            aggregated["errors"] += len(discovery_result.errors)
            # health_score remains the same-scale metric; keep last computed
        
        return aggregated
    
    def maintain_engagement_ratio(self) -> dict:
        """Legacy method - engagement now handled by unified system.
        
        Returns:
            Dict with engagement stats
        """
        logger.warning("maintain_engagement_ratio is deprecated - engagement handled by unified system")
        
        # Run engagement cycle instead
        result = self.engagement_manager.run_engagement_cycle()
        
        return {
            "upvoted_posts": result.upvotes_completed,
            "helpful_comments": len(result.helpful_comments_posted),
            "promotional_comments": len(result.promotional_comments_posted),
        }
