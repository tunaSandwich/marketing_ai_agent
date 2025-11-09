"""Account warming system for building karma and account credibility."""

import random
import time
from datetime import datetime, timedelta
from typing import List, Optional

import praw
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import RedditConfig


class AccountWarmer:
    """Handles account warming activities to build karma and credibility."""
    
    def __init__(self, config: RedditConfig):
        """Initialize account warmer.
        
        Args:
            config: Reddit API configuration
        """
        self.reddit = praw.Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            user_agent=config.user_agent,
            username=config.username,
            password=config.password,
        )
        self.username = config.username
        logger.info(f"AccountWarmer initialized for u/{self.username}")
    
    def get_karma_goal(self, current_karma: int) -> int:
        """Calculate karma goal based on current karma.
        
        Args:
            current_karma: Current total karma
            
        Returns:
            Target karma to reach
        """
        if current_karma < 10:
            return 10
        elif current_karma < 25:
            return 25
        elif current_karma < 50:
            return 50
        elif current_karma < 100:
            return 100
        else:
            return current_karma  # Goal reached
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def upvote_quality_posts(
        self,
        subreddits: List[str],
        count: int = 20,
    ) -> dict:
        """Upvote quality posts to build engagement history.
        
        Args:
            subreddits: List of subreddit names
            count: Number of posts to upvote
            
        Returns:
            Dict with upvote stats
        """
        upvoted = 0
        already_voted = 0
        
        try:
            for subreddit_name in subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Mix of hot, rising, and new for natural behavior
                post_sources = [
                    list(subreddit.hot(limit=30)),
                    list(subreddit.rising(limit=20)),
                    list(subreddit.new(limit=20)),
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
                
                # Sample randomly
                posts_to_vote = random.sample(
                    unique_posts,
                    min(count // len(subreddits), len(unique_posts))
                )
                
                for post in posts_to_vote:
                    try:
                        # Skip if already upvoted
                        if post.likes is True:
                            already_voted += 1
                            continue
                        
                        # Skip if downvoted (don't change)
                        if post.likes is False:
                            continue
                        
                        # Skip low-quality posts
                        if post.score < 5:
                            continue
                        
                        post.upvote()
                        upvoted += 1
                        logger.debug(f"Upvoted post {post.id} in r/{subreddit_name}")
                        
                        # Random delay to appear human (0.5-2 seconds)
                        time.sleep(random.uniform(0.5, 2.0))
                        
                    except Exception as e:
                        logger.warning(f"Failed to upvote {post.id}: {e}")
            
            result = {
                "upvoted": upvoted,
                "already_voted": already_voted,
                "total_processed": upvoted + already_voted,
            }
            
            logger.info(f"Upvoting complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in upvote_quality_posts: {e}")
            return {"upvoted": upvoted, "already_voted": already_voted, "error": str(e)}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def post_helpful_comment(
        self,
        subreddits: List[str] = ["podcasts", "TrueCrimePodcasts"],
    ) -> Optional[str]:
        """Post a helpful, non-promotional comment to build karma.
        
        Args:
            subreddits: List of subreddits to comment in
            
        Returns:
            Comment ID if posted, None otherwise
        """
        try:
            # Randomly select a subreddit
            subreddit_name = random.choice(subreddits)
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get recent posts
            posts = list(subreddit.new(limit=50))
            
            # Filter for posts we can genuinely help with
            eligible_posts = []
            
            for post in posts:
                # Skip if it's our own post
                if post.author and post.author.name == self.username:
                    continue
                
                # Skip if we already commented
                post.comments.replace_more(limit=0)
                if any(c.author and c.author.name == self.username for c in post.comments.list()):
                    continue
                
                # Skip if locked or archived
                if post.locked or post.archived:
                    continue
                
                # Look for posts asking for recommendations
                title_lower = post.title.lower()
                if any(keyword in title_lower for keyword in [
                    "recommend", "suggestion", "looking for", "need", "help",
                    "best", "favorite", "top"
                ]):
                    eligible_posts.append(post)
            
            if not eligible_posts:
                logger.info("No eligible posts found for helpful commenting")
                return None
            
            # Select a random post
            post = random.choice(eligible_posts[:10])  # Top 10 to focus on newer posts
            
            # Generate genuinely helpful comment (no Goodpods mention!)
            comment_text = self._generate_helpful_comment(post)
            
            if not comment_text:
                logger.info("Could not generate appropriate comment")
                return None
            
            # Post the comment
            comment = post.reply(comment_text)
            comment_id = comment.id
            
            logger.info(
                f"Posted helpful comment {comment_id} on r/{subreddit_name} "
                f"(post: {post.id})"
            )
            
            return comment_id
            
        except Exception as e:
            logger.error(f"Error posting helpful comment: {e}")
            return None
    
    def _generate_helpful_comment(self, post) -> Optional[str]:
        """Generate a genuinely helpful comment based on post content.
        
        This focuses on being helpful WITHOUT mentioning Goodpods.
        
        Args:
            post: Reddit post object
            
        Returns:
            Comment text or None if not suitable
        """
        title_lower = post.title.lower()
        content_lower = (post.selftext or "").lower()
        combined = f"{title_lower} {content_lower}"
        
        # Pattern matching for genuine helpfulness
        
        # True crime recommendations
        if "true crime" in combined:
            return random.choice([
                "For true crime, I'd recommend Criminal - great short-form stories. Bear Brook is also fantastic if you want a deep investigative series.",
                "Have you tried Someone Knows Something? It's a Canadian investigative series that's really well done. Also check out The Murder Squad if you like detective perspectives.",
                "Serial is the classic, but if you've already heard it, try S-Town or In the Dark season 2. Both are incredibly well-produced.",
            ])
        
        # Comedy podcast recommendations
        if "comedy" in combined and "podcast" in combined:
            return random.choice([
                "Comedy Bang Bang is hilarious if you like improv. My Brother My Brother and Me is great for absurdist humor.",
                "The Daily Zeitgeist mixes comedy with news pretty well. Conan O'Brien Needs a Friend is also worth checking out.",
                "If you want pure comedy, try The Dollop - they cover weird history with a comedic twist.",
            ])
        
        # History recommendations
        if "history" in combined:
            return random.choice([
                "Dan Carlin's Hardcore History is the gold standard, but episodes are long. Revolutions by Mike Duncan is also excellent and more digestible.",
                "Our Fake History is great if you like myth-busting approach to historical events. The History of Rome is foundational listening.",
                "Backstory is good for American history specifically. The episodes are well-researched and engaging.",
            ])
        
        # Science recommendations
        if "science" in combined:
            return random.choice([
                "Radiolab is amazing for science storytelling. Science Vs is great for myth-busting scientific claims.",
                "Ologies by Alie Ward is fantastic - she interviews experts in different scientific fields. Very accessible and fun.",
                "99% Invisible is technically about design, but it's incredibly well-produced and fascinating.",
            ])
        
        # Generic "looking for podcasts"
        if "looking for" in combined and "podcast" in combined:
            return random.choice([
                "What genres are you interested in? That'll help narrow it down - there are great shows in pretty much every category.",
                "Are you looking for narrative storytelling, interview-style, or educational content? That makes a big difference in recommendations.",
            ])
        
        # Thank you posts
        if "thank you" in combined or "thanks" in combined:
            return random.choice([
                "Glad you found something useful!",
                "Happy to help!",
                "Enjoy!",
            ])
        
        # Default: Skip if we can't add genuine value
        return None
    
    def run_warming_cycle(
        self,
        current_karma: int,
        current_age_days: float,
    ) -> dict:
        """Run one account warming cycle.
        
        Args:
            current_karma: Current account karma
            current_age_days: Current account age in days
            
        Returns:
            Dict with cycle results
        """
        logger.info("=" * 60)
        logger.info("🌱 ACCOUNT WARMING MODE")
        logger.info(f"Current karma: {current_karma} / 100")
        logger.info(f"Current age: {current_age_days:.1f} / 30 days")
        logger.info("=" * 60)
        
        results = {
            "mode": "warming",
            "current_karma": current_karma,
            "karma_goal": 100,
            "current_age_days": current_age_days,
            "age_goal_days": 30,
        }
        
        # Phase 1: Aggressive karma building (karma < 50)
        if current_karma < 50:
            logger.info("📈 Phase 1: Aggressive karma building")
            
            # Upvote more posts
            upvote_result = self.upvote_quality_posts(
                subreddits=["podcasts", "TrueCrimePodcasts", "HistoryPodcasting"],
                count=30,
            )
            results["upvotes"] = upvote_result
            
            # Try to post 1-2 helpful comments
            comment_posted = False
            for attempt in range(2):
                comment_id = self.post_helpful_comment()
                if comment_id:
                    comment_posted = True
                    results["comment_posted"] = comment_id
                    logger.info(f"💬 Posted helpful comment: {comment_id}")
                    break
                time.sleep(random.uniform(30, 60))  # Wait between attempts
            
            if not comment_posted:
                results["comment_posted"] = None
                logger.info("💬 No suitable comment opportunities found")
        
        # Phase 2: Moderate activity (karma 50-99)
        elif current_karma < 100:
            logger.info("📊 Phase 2: Moderate karma building")
            
            # Upvote fewer posts
            upvote_result = self.upvote_quality_posts(
                subreddits=["podcasts", "TrueCrimePodcasts"],
                count=20,
            )
            results["upvotes"] = upvote_result
            
            # Try to post 1 helpful comment
            comment_id = self.post_helpful_comment()
            results["comment_posted"] = comment_id
            if comment_id:
                logger.info(f"💬 Posted helpful comment: {comment_id}")
        
        # Phase 3: Maintenance (karma >= 100, but age < 30)
        else:
            logger.info("⏳ Phase 3: Maintenance mode (waiting for account age)")
            
            # Just upvote to stay active
            upvote_result = self.upvote_quality_posts(
                subreddits=["podcasts"],
                count=15,
            )
            results["upvotes"] = upvote_result
            results["comment_posted"] = None
        
        # Calculate progress
        karma_progress = min(100, (current_karma / 100) * 100)
        age_progress = min(100, (current_age_days / 30) * 100)
        overall_progress = (karma_progress + age_progress) / 2
        
        results["karma_progress_percent"] = karma_progress
        results["age_progress_percent"] = age_progress
        results["overall_progress_percent"] = overall_progress
        
        logger.info(f"🎯 Progress: Karma {karma_progress:.1f}%, Age {age_progress:.1f}%, Overall {overall_progress:.1f}%")
        logger.info(f"✅ Warming cycle complete: {results}")
        return results