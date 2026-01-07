"""Unified Reddit engagement manager - handles warming and active engagement."""

import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import praw
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from ..llm.client import ClaudeClient
from ..llm.prompts import PromptTemplate
from ..rag.retriever import KnowledgeRetriever
from ..utils.config import RedditConfig, LLMConfig
from ..models import (
    AccountHealth,
    AccountState,
    ActivityBudget,
    BrandConfig,
    EngagementCycleResult,
    RedditPost,
)
from .engagement_strategy import EngagementStrategyManager
from .subreddit_selector import SubredditSelector


class RedditEngagementManager:
    """Unified engagement manager for warming and active phases."""
    
    def __init__(
        self,
        reddit_config: RedditConfig,
        llm_config: LLMConfig,
        brand_config: BrandConfig,
    ):
        """Initialize engagement manager.
        
        Args:
            reddit_config: Reddit API configuration
            llm_config: LLM configuration
            brand_config: Brand pack configuration
        """
        # Initialize Reddit
        self.reddit = praw.Reddit(
            client_id=reddit_config.client_id,
            client_secret=reddit_config.client_secret,
            user_agent=reddit_config.user_agent,
            username=reddit_config.username,
            password=reddit_config.password,
        )
        self.username = reddit_config.username
        
        # Initialize LLM
        self.llm_client = ClaudeClient(llm_config)
        
        # Initialize RAG retrievers (KEEP EXISTING SYSTEM)
        warming_index_path = Path("brands/warming/index")
        brand_index_path = Path(f"brands/{brand_config.brand_id}/index")
        
        try:
            self.warming_retriever = KnowledgeRetriever(
                index_dir=warming_index_path,
                model_name="all-MiniLM-L6-v2",
            )
            logger.info("Warming knowledge retriever initialized")
        except FileNotFoundError:
            logger.error(
                f"Warming index not found at {warming_index_path}. "
                "Run 'python scripts/index_brand_knowledge.py --brand warming'"
            )
            raise
        
        try:
            self.brand_retriever = KnowledgeRetriever(
                index_dir=brand_index_path,
                model_name="all-MiniLM-L6-v2",
            )
            logger.info(f"Brand knowledge retriever initialized for {brand_config.brand_id}")
        except FileNotFoundError:
            logger.error(
                f"Brand index not found at {brand_index_path}. "
                f"Run 'python scripts/index_brand_knowledge.py --brand {brand_config.brand_id}'"
            )
            raise
        
        # Store brand config
        self.brand_config = brand_config
        
        # Initialize strategy manager
        self.strategy_manager = EngagementStrategyManager()
        
        # Initialize subreddit selector
        # Extend Tier 1 with supplemental (subject-derived) subreddits so the agent
        # can begin exploring a broader, learning-focused set early on.
        try:
            from .supplemental_subs import load_flattened_subject_subreddits
            supplemental = load_flattened_subject_subreddits(limit=200)
        except Exception as e:
            logger.warning(f"Could not load supplemental subreddits: {e}")
            supplemental = []
        
        # Merge and de-duplicate while preserving original tier1 order preference
        tier1_merged: list[str] = []
        seen: set[str] = set()
        for sub in brand_config.subreddits_tier1 + supplemental:
            key = sub.strip()
            if key and key not in seen:
                seen.add(key)
                tier1_merged.append(key)
        
        self.subreddit_selector = SubredditSelector(
            tier1_subreddits=tier1_merged,
            tier2_subreddits=brand_config.subreddits_tier2,
            tier3_subreddits=brand_config.subreddits_tier3,
            cooldown_hours=2,
        )
        logger.info(
            f"SubredditSelector Tier1 size: brand={len(brand_config.subreddits_tier1)}, "
            f"supplemental+merged={len(tier1_merged)}"
        )
        
        # Track recent activity for quality scoring
        self.recent_comments: List[str] = []
        
        logger.info(
            f"RedditEngagementManager initialized for u/{self.username} "
            f"with brand {brand_config.brand_id}"
        )
    
    def get_account_health(self) -> AccountHealth:
        """Get current account health metrics.
        
        Returns:
            Account health with calculated health score
        """
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Reddit API call timed out")
        
        # Set a 30-second timeout for Reddit API calls
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        try:
            # Get Reddit account info with timeout protection
            logger.info("Fetching account information from Reddit API...")
            user = self.reddit.redditor(self.username)
            
            logger.info("Retrieving karma information...")
            karma = user.link_karma + user.comment_karma
            
            # Calculate account age
            logger.info("Retrieving account creation date...")
            created_utc = user.created_utc
            age_seconds = time.time() - created_utc
            age_days = age_seconds / 86400
            
            signal.alarm(0)  # Cancel timeout
            logger.info(f"Successfully retrieved account info: {karma} karma, {age_days:.1f} days old")
            
        except TimeoutError:
            signal.alarm(0)  # Cancel timeout
            logger.error(f"Reddit API call timed out after 30 seconds")
            # Return default values for timeout case
            karma = 50  # Reasonable default
            age_days = 30.0  # Reasonable default
            logger.warning(f"Using default values due to timeout: karma={karma}, age_days={age_days}")
            
        except Exception as e:
            signal.alarm(0)  # Cancel timeout  
            logger.error(f"Error retrieving account information: {type(e).__name__}: {e}")
            # Return default values for error case
            karma = 50  # Reasonable default
            age_days = 30.0  # Reasonable default
            logger.warning(f"Using default values due to error: karma={karma}, age_days={age_days}")
        
        # Calculate recent activity quality (placeholder for now)
        # TODO: Track upvote/downvote ratios on our comments
        recent_activity_quality = 0.5
        
        # Calculate health score
        health_score = self.strategy_manager.calculate_health_score(
            karma=karma,
            age_days=age_days,
            recent_activity_quality=recent_activity_quality,
        )
        
        account_state = self.strategy_manager.get_account_state(health_score)
        
        return AccountHealth(
            karma=karma,
            age_days=age_days,
            recent_activity_quality=recent_activity_quality,
            health_score=health_score,
            account_state=account_state,
        )
    
    def run_engagement_cycle(self) -> EngagementCycleResult:
        """Run one engagement cycle.
        
        Returns:
            Results of the engagement cycle
        """
        # Get account health
        health = self.get_account_health()
        
        logger.info("=" * 60)
        logger.info(f"🎯 ENGAGEMENT CYCLE - {health.account_state.value.upper()}")
        logger.info(f"Health Score: {health.health_score:.1f}/100")
        logger.info(f"Karma: {health.karma}, Age: {health.age_days:.1f} days")
        logger.info("=" * 60)
        
        # Get activity budget
        budget = self.strategy_manager.get_activity_budget(
            health_score=health.health_score,
            account_state=health.account_state,
        )
        
        logger.info(
            f"Budget: {budget.upvotes_target} upvotes, "
            f"{budget.comments_target} comments, "
            f"{budget.promotional_ratio*100:.0f}% promotional"
        )
        
        # Select target subreddit
        subreddit = self.subreddit_selector.select_subreddit(
            allowed_tiers=budget.allowed_tiers
        )
        
        logger.info(f"Target subreddit: r/{subreddit}")
        
        # Execute engagement activities
        result = EngagementCycleResult(
            cycle_type="engagement",
            health_score=health.health_score,
            account_state=health.account_state,
            subreddit=subreddit,
        )
        
        # 1. Upvote posts
        try:
            upvotes = self._upvote_posts(subreddit, budget.upvotes_target)
            result.upvotes_completed = upvotes
            logger.info(f"✅ Upvoted {upvotes} posts in r/{subreddit}")
        except Exception as e:
            logger.error(f"Error upvoting posts: {e}")
            result.errors.append(f"Upvoting failed: {str(e)}")
        
        # 2. Post comments
        for i in range(budget.comments_target):
            try:
                # Decide if this comment should be promotional
                is_promotional = random.random() < budget.promotional_ratio
                
                comment_id = self._post_comment(
                    subreddit=subreddit,
                    budget=budget,
                    is_promotional=is_promotional,
                )
                
                if comment_id:
                    if is_promotional:
                        result.promotional_comments_posted.append(comment_id)
                        logger.info(f"✅ Posted promotional comment: {comment_id}")
                    else:
                        result.helpful_comments_posted.append(comment_id)
                        logger.info(f"✅ Posted helpful comment: {comment_id}")
                else:
                    logger.info(f"⏭️  Skipped comment opportunity {i+1}")
                
                # Random delay between comments (30-90 seconds)
                if i < budget.comments_target - 1:
                    delay = random.uniform(30, 90)
                    logger.debug(f"Waiting {delay:.0f}s before next comment")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error posting comment {i+1}: {e}")
                result.errors.append(f"Comment {i+1} failed: {str(e)}")
        
        logger.info("=" * 60)
        logger.info(
            f"Cycle complete: {result.upvotes_completed} upvotes, "
            f"{len(result.helpful_comments_posted)} helpful, "
            f"{len(result.promotional_comments_posted)} promotional"
        )
        logger.info("=" * 60)
        
        return result
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _upvote_posts(self, subreddit: str, count: int) -> int:
        """Upvote posts in a subreddit.
        
        Args:
            subreddit: Subreddit name
            count: Number of posts to upvote
            
        Returns:
            Number of posts actually upvoted
        """
        upvoted = 0
        sub = self.reddit.subreddit(subreddit)
        
        # Mix of hot, rising, and new for natural behavior
        post_sources = [
            list(sub.hot(limit=20)),
            list(sub.rising(limit=15)),
            list(sub.new(limit=15)),
        ]
        
        all_posts = []
        for source in post_sources:
            all_posts.extend(source)
        
        # Remove duplicates
        seen = set()
        unique_posts = []
        for post in all_posts:
            if post.id not in seen:
                seen.add(post.id)
                unique_posts.append(post)
        
        # Randomly sample posts to upvote
        posts_to_upvote = random.sample(
            unique_posts,
            min(count, len(unique_posts))
        )
        
        for post in posts_to_upvote:
            try:
                # Skip if already upvoted
                if post.likes is True:
                    continue
                
                # Skip low-quality posts
                if post.score < 5:
                    continue
                
                post.upvote()
                upvoted += 1
                
                # Human-like delay
                time.sleep(random.uniform(0.5, 2.0))
                
            except Exception as e:
                logger.warning(f"Failed to upvote post {post.id}: {e}")
        
        return upvoted
    
    def _post_comment(
        self,
        subreddit: str,
        budget: ActivityBudget,
        is_promotional: bool,
    ) -> Optional[str]:
        """Post a comment (helpful or promotional).
        
        Args:
            subreddit: Target subreddit
            budget: Activity budget with constraints
            is_promotional: Whether to include brand mention
            
        Returns:
            Comment ID if posted, None otherwise
        """
        # Find eligible post
        post = self._find_eligible_post(subreddit, budget)
        if not post:
            return None
        
        # Log selected post context
        try:
            logger.info(
                f"Selected post for reply in r/{subreddit}: "
                f"id={getattr(post, 'id', '?')}, score={getattr(post, 'score', '?')}, "
                f"title={getattr(post, 'title', '')[:180]}{'...' if len(getattr(post, 'title', '')) > 180 else ''}"
            )
            if hasattr(post, "url"):
                logger.debug(f"Post URL: {post.url}")
        except Exception:
            pass
        
        # Generate comment (REUSE EXISTING create_response_prompt)
        comment_text = self._generate_comment(
            post=post,
            is_promotional=is_promotional,
            constraints=budget.comment_constraints,
        )
        
        if not comment_text:
            return None
        
        # Log generated comment (preview + length)
        try:
            preview = comment_text[:500]
            suffix = "..." if len(comment_text) > 500 else ""
            logger.debug(
                f"Generated {'promotional' if is_promotional else 'helpful'} comment "
                f"({len(comment_text)} chars): {preview}{suffix}"
            )
        except Exception:
            pass
        
        # Validate comment
        if is_promotional:
            is_valid, reasons = self._validate_promotional_comment_with_reasons(
                comment_text, constraints=budget.comment_constraints
            )
            if not is_valid:
                logger.warning(
                    "Generated promotional comment failed validation: " + "; ".join(reasons[:5])
                )
                return None
        else:
            is_valid, reasons = self._validate_helpful_comment_with_reasons(
                comment_text, constraints=budget.comment_constraints
            )
            if not is_valid:
                logger.warning(
                    "Generated helpful comment failed validation: " + "; ".join(reasons[:5])
                )
                return None
        
        # Post comment
        try:
            comment = post.reply(comment_text)
            logger.info(
                f"Posted {'promotional' if is_promotional else 'helpful'} "
                f"comment {comment.id} on post {post.id}"
            )
            return comment.id
        except Exception as e:
            logger.error(f"Failed to post comment on {post.id}: {e}")
            return None
    
    def _find_eligible_post(
        self,
        subreddit: str,
        budget: ActivityBudget,
    ):
        """Find an eligible post to comment on.
        
        Args:
            subreddit: Subreddit name
            budget: Activity budget with constraints
            
        Returns:
            Eligible Reddit post or None
        """
        sub = self.reddit.subreddit(subreddit)
        posts = list(sub.new(limit=50))
        
        eligible = []
        
        for post in posts:
            # Skip own posts
            if post.author and post.author.name == self.username:
                continue
            
            # Skip if already commented
            post.comments.replace_more(limit=0)
            if any(
                c.author and c.author.name == self.username 
                for c in post.comments.list()
            ):
                continue
            
            # Skip locked/archived
            if post.locked or post.archived:
                continue
            
            # Check score threshold
            if post.score < budget.comment_constraints.min_post_score:
                continue
            
            # Look for recommendation requests
            title_lower = post.title.lower()
            if any(keyword in title_lower for keyword in [
                "recommend", "suggestion", "looking for", "need", "help",
                "best", "favorite", "top"
            ]):
                eligible.append(post)
        
        if not eligible:
            return None
        
        # Prefer newer posts
        return random.choice(eligible[:10])
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _generate_comment(
        self,
        post,
        is_promotional: bool,
        constraints,
    ) -> Optional[str]:
        """Generate a comment using Claude and EXISTING prompts.
        
        CRITICAL: This reuses create_response_prompt() for BOTH helpful and promotional.
        The only difference is which RAG retriever is used.
        
        Args:
            post: Reddit post object
            is_promotional: Whether to include brand mention
            constraints: Comment constraints from budget
            
        Returns:
            Generated comment text or None
        """
        try:
            # Select knowledge retriever based on mode
            retriever = (
                self.brand_retriever if is_promotional
                else self.warming_retriever
            )
            
            # Retrieve relevant knowledge
            chunks = retriever.retrieve_for_post(
                post_title=post.title,
                post_content=post.selftext or "",
                top_k=3,
                min_similarity=0.3,
            )
            
            # Format RAG content (EXISTING FORMAT)
            rag_content = ""
            if chunks:
                rag_content = "\n\n".join([
                    f"From {chunk.filename}:\n{chunk.content}"
                    for chunk in chunks
                ])
            
            # Convert praw post to RedditPost model
            reddit_post = RedditPost(
                id=post.id,
                title=post.title,
                content=post.selftext or "",
                subreddit=post.subreddit.display_name,
                score=post.score,
                created_at=datetime.fromtimestamp(post.created_utc),
                url=f"https://reddit.com{post.permalink}",
                author=post.author.name if post.author else "[deleted]",
                num_comments=post.num_comments,
            )
            
            # Use centralized prompt system from prompts.py with different handling for modes
            if not is_promotional:
                # Create empty brand config for warming (no brand mentions)
                from ..models import BrandConfig
                warming_brand_config = BrandConfig(
                    brand_id="warming",
                    brand_name="",  # Empty to prevent any brand mentions
                    company_description="",
                    primary_cta="https://example.com",  # Valid URL required by validation
                    tracking_params="",
                    tone_attributes=[],  # Required field
                    allowed_claims=[],
                    forbidden_topics=["goodpods", "any app names", "any brand names"],  # Add explicit blocking
                    voice_guidelines="Be helpful without promoting anything",
                    subreddits_tier1=[],
                    subreddits_tier2=[],
                    subreddits_tier3=[],
                )
                context = {"skip_brand": True, "mode": "helpful"}
                
                # Generate prompt with empty brand config
                prompt = PromptTemplate.create_response_prompt(
                    post=reddit_post,
                    brand_config=warming_brand_config,
                    rag_content=rag_content,
                    context=context,
                )
                
                # CRITICAL: Append brand blocking instruction
                prompt = prompt.replace(
                    "Your response:", 
                    "CRITICAL: do not mention any apps, brands, or services - just give podcast recommendations.\n\nYour response:"
                )
            else:
                # Promotional mode - use normal brand config
                context = {"mode": "promotional"}
                
                prompt = PromptTemplate.create_response_prompt(
                    post=reddit_post,
                    brand_config=self.brand_config,
                    rag_content=rag_content,
                    context=context,
                )
            
            # DRASTICALLY REDUCED TOKEN LIMITS FOR BREVITY
            if is_promotional:
                # Promotional can be slightly longer but still brief
                max_tokens = 35  # This generates ~150-180 chars
            else:
                # Helpful must be very brief
                max_tokens = 30  # This generates ~120-150 chars
            
            # Single attempt with strict limits and lower temperature
            message = self.llm_client._client.messages.create(
                model=self.llm_client._config.model,
                max_tokens=max_tokens,
                temperature=0.7,  # Lower temperature for more predictable length
                messages=[{"role": "user", "content": prompt}],
            )
            
            # Extract content
            comment = ""
            if message.content and len(message.content) > 0:
                comment = (
                    message.content[0].text
                    if hasattr(message.content[0], "text")
                    else str(message.content[0])
                ).strip()
            
            logger.debug(f"Generated {'promotional' if is_promotional else 'helpful'} comment: {comment[:100]}...")
            
            # HARD TRUNCATION SAFETY NET - Step 3 of brevity enforcement
            if len(comment) > 180:
                logger.warning(f"Comment too long ({len(comment)} chars), truncating...")
                
                # Try to truncate at sentence boundary first
                sentences = comment.split('.')
                if len(sentences) > 1:
                    # Find the longest combination of sentences that fits
                    truncated = ""
                    for sentence in sentences[:-1]:  # Skip empty last element after last period
                        candidate = truncated + sentence + "."
                        if len(candidate.strip()) <= 180:
                            truncated = candidate
                        else:
                            break
                    
                    if len(truncated.strip()) > 20:  # Make sure we have meaningful content
                        comment = truncated.strip()
                    else:
                        # Fallback to word boundary
                        comment = self._truncate_at_word_boundary(comment, 180)
                else:
                    # No sentences, truncate at word boundary
                    comment = self._truncate_at_word_boundary(comment, 180)
                
                logger.info(f"Truncated to {len(comment)} chars: {comment}")
            
            return comment
            
        except Exception as e:
            logger.error(f"Error generating comment: {e}")
            return None
    
    def _truncate_at_word_boundary(self, text: str, max_length: int) -> str:
        """Truncate text at word boundary without breaking words.
        
        Args:
            text: Text to truncate
            max_length: Maximum allowed length
            
        Returns:
            Truncated text that fits within max_length
        """
        if len(text) <= max_length:
            return text
        
        # Find last space before max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            # Truncate at last word boundary
            return text[:last_space].strip()
        else:
            # No spaces found, hard truncate (shouldn't happen with short comments)
            return text[:max_length].strip()
    
    def _validate_naturalness(self, comment: str) -> tuple[bool, list[str]]:
        """Validate comment naturalness to detect AI language patterns.
        
        Args:
            comment: Comment text to validate
            
        Returns:
            Tuple of (is_natural, list_of_ai_patterns_found)
        """
        if not comment or not isinstance(comment, str):
            return False, ["Comment is empty or not a string"]
        
        comment_lower = comment.lower()
        
        # Detect AI language patterns
        ai_tells = [
            # Formal/corporate language
            "i'd be happy to", "i would recommend", "i would suggest",
            "here are some", "here's a list", "based on your",
            "you might want to", "you may want to", "you should consider",
            "thank you for", "i hope this helps", "feel free to",
            
            # Overly structured language
            "to answer your question", "in response to", "regarding your",
            "with that said", "that being said", "in conclusion",
            "to summarize", "in summary", "overall,",
            
            # AI hedging language
            "it seems like", "it appears that", "it looks like",
            "from what i understand", "if i understand correctly",
            "based on what you've described",
            
            # Unnatural enthusiasm  
            "absolutely love", "definitely check out",
            "you'll absolutely", "you'll definitely", "perfect choice",
            
            # Corporate speak
            "great question", "excellent point", "wonderful suggestion",
            "amazing podcast", "incredible show", "fantastic resource",
        ]
        
        # Check for AI patterns
        found_patterns = []
        for pattern in ai_tells:
            if pattern in comment_lower:
                found_patterns.append(pattern)
        
        # Check for overly perfect grammar (AI tell) - disabled for now as it's too strict
        # sentences = comment.split('.')
        # if len(sentences) > 2 and len(comment) > 200:  # More lenient - only flag longer comments
        #     # Every sentence starts with capital and ends with punctuation = AI-like
        #     perfect_grammar = all(
        #         s.strip() and s.strip()[0].isupper() 
        #         for s in sentences[:-1] if s.strip()
        #     )
        #     if perfect_grammar:
        #         found_patterns.append("overly perfect grammar")
        
        # Check for unnatural word choices
        unnatural_words = [
            "utilize", "ascertain", "subsequently", "furthermore", 
            "nevertheless", "therefore", "consequently", "moreover"
        ]
        
        for word in unnatural_words:
            if word in comment_lower:
                found_patterns.append(f"unnatural word: {word}")
        
        # Check for lack of contractions (AI tell)
        formal_phrases = [
            "do not", "will not", "have not", "did not", "can not", 
            "should not", "would not", "could not"
        ]
        
        formal_found = []
        for phrase in formal_phrases:
            if phrase in comment_lower:
                formal_found.append(phrase)
        
        if len(formal_found) > 1:  # Multiple formal phrases = AI-like
            found_patterns.append(f"too formal: {', '.join(formal_found)}")
        
        is_natural = len(found_patterns) == 0
        return is_natural, found_patterns
    
    def _validate_helpful_comment(self, comment: str, constraints=None) -> bool:
        """Validate helpful comment for warming mode (no brand mentions allowed)."""
        result, _ = self._validate_helpful_comment_with_reasons(comment, constraints)
        return result
    
    def _validate_helpful_comment_with_reasons(self, comment: str, constraints=None) -> tuple[bool, list[str]]:
        """Validate helpful comment and return detailed failure reasons.
        
        Args:
            comment: Generated comment to validate
            
        Returns:
            Tuple of (is_valid, list_of_failure_reasons)
        """
        if not comment or not isinstance(comment, str):
            return False, ["Comment is empty or not a string"]
        
        reasons = []
        comment_lower = comment.lower()
        
        # Block brand mentions (strict for warming mode)
        blocklist = [
            "goodpods",
            "our app",
            "my app", 
            "this app",
            "the app",
            "download",
            "podcast player",
            "podcast app",
        ]
        
        blocked_terms = []
        for term in blocklist:
            if term in comment_lower:
                blocked_terms.append(term)
        
        if blocked_terms:
            reasons.append(f"Contains blocked terms: {', '.join(blocked_terms)}")
        
        # Length check - realistic for 40-180 char brevity enforcement 
        if constraints and constraints.max_length:
            # Allow small buffer for strict brevity (180 becomes 200 max)
            actual_max = min(200, constraints.max_length + 20)
        else:
            actual_max = 200  # Default max for helpful comments
            
        if len(comment) < 40:  # Minimum for meaningful content
            reasons.append(f"Too short: {len(comment)} chars (min 40)")
        elif len(comment) > actual_max:
            reasons.append(f"Too long: {len(comment)} chars (max {actual_max})")
        
        # Check for incomplete sentences (truncation detection)
        if not (comment.endswith('.') or comment.endswith('!') or 
                comment.endswith('?') or comment.endswith(')')):
            # Check if it looks truncated
            last_words = comment.split()[-3:] if len(comment.split()) >= 3 else comment.split()
            if any(word in ["the", "and", "or", "but", "with", "for", "is", "are", "to", "a", "an"] 
                   for word in last_words):
                reasons.append("Comment appears truncated (incomplete sentence)")
        
        # Just ensure it's a meaningful response (not too short)
        if len(comment.split()) < 5:
            reasons.append("Too brief to be helpful (less than 5 words)")
        
        # Check for recommendation language (but be flexible)
        rec_words = ["try", "check out", "recommend", "love", "loving", "great", 
                     "perfect", "listen", "good", "using", "been", "really", "honestly"]
        if not any(word in comment_lower for word in rec_words):
            # Only flag if it also doesn't mention any podcast-like words
            podcast_indicators = ["podcast", "episode", "show", "series", "listen"]
            if not any(ind in comment_lower for ind in podcast_indicators):
                reasons.append("May not contain helpful recommendation language")
        
        # Use centralised naturalness validator
        is_natural, ai_patterns_found = self._validate_naturalness(comment)
        if not is_natural:
            reasons.append(f"AI language detected: {', '.join(ai_patterns_found[:3])}")  # Limit to first 3
        
        is_valid = len(reasons) == 0
        if not is_valid:
            logger.warning(f"Helpful comment validation failed: {'; '.join(reasons)}")
        
        return is_valid, reasons
    
    def _validate_promotional_comment(self, comment: str, constraints=None) -> bool:
        """Validate promotional comment for subtlety and helpfulness."""
        result, _ = self._validate_promotional_comment_with_reasons(comment, constraints)
        return result
    
    def _validate_promotional_comment_with_reasons(self, comment: str, constraints=None) -> tuple[bool, list[str]]:
        """Validate promotional comment and return detailed failure reasons.
        
        CRITICAL: Promotional comments must be helpful FIRST, promotional SECOND.
        
        Args:
            comment: Comment text to validate
            constraints: Optional comment constraints for length validation
            
        Returns:
            Tuple of (is_valid, list_of_failure_reasons)
        """
        if not comment or not isinstance(comment, str):
            return False, ["Comment is empty or not a string"]
        
        reasons = []
        comment_lower = comment.lower()
        
        # Length check - realistic for 40-180 char brevity enforcement
        if constraints and constraints.max_length:
            # Allow small buffer for strict brevity (240 becomes 260 max)
            actual_max = min(280, constraints.max_length + 20)
        else:
            actual_max = 280  # Default max for promotional comments
            
        if len(comment) < 50:  # Promotional needs more substance
            reasons.append(f"Too short: {len(comment)} chars (min 50)")
        elif len(comment) > actual_max:
            reasons.append(f"Too long: {len(comment)} chars (max {actual_max})")
        
        # Check for incomplete sentences (truncation detection)
        if not (comment.endswith('.') or comment.endswith('!') or 
                comment.endswith('?') or comment.endswith(')')):
            # Check if it looks truncated
            last_words = comment.split()[-3:] if len(comment.split()) >= 3 else comment.split()
            if any(word in ["the", "and", "or", "but", "with", "for", "is", "are", "to", "a", "an"] 
                   for word in last_words):
                reasons.append("Comment appears truncated (incomplete sentence)")
        
        # Must have recommendation OR helpfulness language
        helpful_signals = [
            "try", "check out", "recommend", "love", "great", "perfect", 
            "honestly", "tbh", "organize", "helps", "use", "easier", "better"
        ]
        
        found_helpful = [s for s in helpful_signals if s in comment_lower]
        if not found_helpful:
            reasons.append(f"Missing helpful language (need one of: {', '.join(helpful_signals[:6])}...)")
        
        # Brand mention validation
        goodpods_mentions = comment_lower.count("goodpods")
        
        if goodpods_mentions == 0:
            reasons.append("No brand mention in promotional comment")
        elif goodpods_mentions > 1:
            reasons.append(f"Too many brand mentions: {goodpods_mentions} (max 1)")
        
        # Should sound like personal experience
        personal_indicators = [
            "i use", "i personally", "i organize", "i've been", "helps me", "i can", 
            "honestly i", "i keep", "makes", "way easier", "i found",
            "i switched", "been using", "my experience", "i love"
        ]
        
        found_personal = [p for p in personal_indicators if p in comment_lower]
        if not found_personal:
            reasons.append("Doesn't sound personal (need 'I use', 'I've been', 'helps me', etc.)")
        
        # Block overly corporate language
        corporate_patterns = [
            "you should try goodpods",
            "check out goodpods",
            "download goodpods",
            "goodpods is a great",
            "goodpods has",
        ]
        
        found_corporate = []
        for pattern in corporate_patterns:
            if pattern in comment_lower:
                found_corporate.append(pattern)
        
        if found_corporate:
            reasons.append(f"Too corporate: '{', '.join(found_corporate)}'")
        
        # Use centralised naturalness validator
        is_natural, ai_patterns_found = self._validate_naturalness(comment)
        if not is_natural:
            reasons.append(f"AI language detected: {', '.join(ai_patterns_found[:3])}")  # Limit to first 3
        
        is_valid = len(reasons) == 0
        if not is_valid:
            logger.warning(f"Promotional comment validation failed: {'; '.join(reasons)}")
        
        return is_valid, reasons
    
    def run_discovery_cycle(self) -> EngagementCycleResult:
        """Run discovery cycle (only in ACTIVE state).
        
        Discovery cycles are more selective and target high-value opportunities
        across multiple subreddits.
        
        Returns:
            Results of the discovery cycle
        """
        health = self.get_account_health()
        
        # Only run discovery in ACTIVE state
        if not self.strategy_manager.should_run_discovery_cycle(health.account_state):
            logger.info(
                f"⏭️  Skipping discovery cycle - account state: {health.account_state.value}"
            )
            return EngagementCycleResult(
                cycle_type="discovery_skipped",
                health_score=health.health_score,
                account_state=health.account_state,
            )
        
        logger.info("=" * 60)
        logger.info("🔍 DISCOVERY CYCLE - ACTIVE MODE")
        logger.info(f"Health Score: {health.health_score:.1f}/100")
        logger.info("=" * 60)
        
        # Use ACTIVE budget
        budget = self.strategy_manager.get_activity_budget(
            health_score=health.health_score,
            account_state=health.account_state,
        )
        
        result = EngagementCycleResult(
            cycle_type="discovery",
            health_score=health.health_score,
            account_state=health.account_state,
        )
        
        # Search across all tier 1 subreddits for opportunities
        all_opportunities = []
        
        for subreddit in self.brand_config.subreddits_tier1:
            try:
                post = self._find_eligible_post(subreddit, budget)
                if post:
                    all_opportunities.append((subreddit, post))
            except Exception as e:
                logger.warning(f"Error finding posts in r/{subreddit}: {e}")
        
        if not all_opportunities:
            logger.info("No discovery opportunities found")
            return result
        
        # Select best opportunity (random for now, could score by relevance)
        subreddit, post = random.choice(all_opportunities)
        result.subreddit = subreddit
        
        # Decide promotional or helpful
        is_promotional = random.random() < budget.promotional_ratio
        
        try:
            comment_id = self._post_comment(
                subreddit=subreddit,
                budget=budget,
                is_promotional=is_promotional,
            )
            
            if comment_id:
                if is_promotional:
                    result.promotional_comments_posted.append(comment_id)
                    logger.info(f"✅ Discovery: Posted promotional comment {comment_id}")
                else:
                    result.helpful_comments_posted.append(comment_id)
                    logger.info(f"✅ Discovery: Posted helpful comment {comment_id}")
            
        except Exception as e:
            logger.error(f"Error in discovery cycle: {e}")
            result.errors.append(str(e))
        
        logger.info("=" * 60)
        return result
