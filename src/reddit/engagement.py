"""Non-promotional engagement to maintain 10% ratio."""

import random
from typing import List

import praw
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import RedditConfig


class RedditEngagement:
    """Handles non-promotional engagement (upvotes, casual comments)."""
    
    def __init__(self, config: RedditConfig):
        """Initialize engagement handler.
        
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
        logger.info("RedditEngagement initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def upvote_posts(
        self,
        subreddits: List[str],
        count: int = 10,
    ) -> int:
        """Upvote relevant posts to show authentic engagement.
        
        Args:
            subreddits: List of subreddit names
            count: Number of posts to upvote
            
        Returns:
            Number of posts upvoted
        """
        upvoted = 0
        
        try:
            for subreddit_name in subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get hot posts (most likely to be quality content)
                posts = list(subreddit.hot(limit=50))
                
                # Sample randomly to appear natural
                sample_posts = random.sample(posts, min(count // len(subreddits), len(posts)))
                
                for post in sample_posts:
                    try:
                        # Skip if we already upvoted
                        if post.likes is True:
                            continue
                        
                        post.upvote()
                        upvoted += 1
                        logger.debug(f"Upvoted post {post.id} in r/{subreddit_name}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to upvote {post.id}: {e}")
            
            logger.info(f"Upvoted {upvoted} posts across {len(subreddits)} subreddits")
            return upvoted
            
        except Exception as e:
            logger.error(f"Error upvoting posts: {e}")
            return upvoted
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def post_casual_comment(
        self,
        subreddit: str = "podcasts",
    ) -> bool:
        """Post a helpful, non-promotional comment.
        
        Args:
            subreddit: Subreddit to comment in
            
        Returns:
            True if posted successfully
        """
        try:
            sub = self.reddit.subreddit(subreddit)
            
            # Get recent posts
            posts = list(sub.new(limit=20))
            
            # Find a post we can genuinely help with (no Goodpods mention)
            for post in posts:
                # Skip if it's our own post or already commented
                if post.author == self.reddit.user.me():
                    continue
                
                # Skip if we already commented
                post.comments.replace_more(limit=0)
                if any(c.author == self.reddit.user.me() for c in post.comments):
                    continue
                
                # Generate casual, helpful comment (no promotion)
                comment = self._generate_casual_comment(post)
                
                if comment:
                    post.reply(comment)
                    logger.info(f"Posted casual comment on {post.id}")
                    return True
            
            logger.info("No suitable posts found for casual commenting")
            return False
            
        except Exception as e:
            logger.error(f"Error posting casual comment: {e}")
            return False
    
    def _generate_casual_comment(self, post) -> str:
        """Generate a helpful, non-promotional comment.
        
        This is intentionally simple and genuine - no AI generation needed.
        
        Args:
            post: Reddit post object
            
        Returns:
            Comment text or empty string if not suitable
        """
        title_lower = post.title.lower()
        
        # Pattern matching for genuine helpfulness
        if "thank you" in title_lower or "thanks" in title_lower:
            return random.choice([
                "glad you found something useful!",
                "happy to help!",
                "enjoy!",
                "awesome, hope you enjoy it!",
            ])
        
        if "first time" in title_lower and "podcast" in title_lower:
            return random.choice([
                "welcome to the podcast world! it's addictive :)",
                "enjoy the journey! podcasts are amazing",
                "you're gonna love it. great choice to start!",
            ])
        
        if "finished" in title_lower or "done with" in title_lower:
            return random.choice([
                "that post-podcast void is real!",
                "know that feeling. time to find the next obsession!",
                "the search for the next great one begins...",
            ])
        
        # Default: Skip if we can't add genuine value
        return ""
    
    def upvote_comments(
        self,
        subreddits: List[str],
        count: int = 5,
    ) -> int:
        """Upvote helpful comments to show community engagement.
        
        Args:
            subreddits: List of subreddit names
            count: Number of comments to upvote
            
        Returns:
            Number of comments upvoted
        """
        upvoted = 0
        
        try:
            for subreddit_name in subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get recent posts
                posts = list(subreddit.hot(limit=10))
                
                for post in posts[:3]:  # Check top 3 posts
                    post.comments.replace_more(limit=0)
                    
                    # Get top-level comments
                    comments = post.comments[:10]
                    
                    for comment in comments:
                        try:
                            # Skip if already voted or is our own
                            if comment.likes is not None or comment.author == self.reddit.user.me():
                                continue
                            
                            # Upvote if it seems helpful (has positive score)
                            if comment.score > 0:
                                comment.upvote()
                                upvoted += 1
                                logger.debug(f"Upvoted comment {comment.id}")
                                
                                if upvoted >= count:
                                    break
                                    
                        except Exception as e:
                            logger.warning(f"Failed to upvote comment: {e}")
                    
                    if upvoted >= count:
                        break
            
            logger.info(f"Upvoted {upvoted} comments")
            return upvoted
            
        except Exception as e:
            logger.error(f"Error upvoting comments: {e}")
            return upvoted