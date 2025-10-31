"""Reddit posting and account management."""

from datetime import datetime, timedelta
from typing import Optional

import praw
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.models import RedditPost
from src.utils.config import RedditConfig


class RedditPoster:
    """Handles posting comments and managing Reddit account health."""
    
    def __init__(self, config: RedditConfig):
        """Initialize poster with Reddit credentials.
        
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
        logger.info(f"RedditPoster initialized for u/{self.username}")
    
    def check_account_health(self) -> dict:
        """Check if account is healthy and can post.
        
        Returns:
            Dict with account health metrics
        """
        try:
            user = self.reddit.user.me()
            
            health = {
                "username": str(user.name),
                "karma": user.link_karma + user.comment_karma,
                "account_age_days": (datetime.now().timestamp() - user.created_utc) / 86400,
                "is_suspended": user.is_suspended if hasattr(user, 'is_suspended') else False,
                "can_post": True,
            }
            
            # Check minimum requirements
            if health["karma"] < 100:
                health["can_post"] = False
                health["reason"] = "Insufficient karma"
            elif health["account_age_days"] < 30:
                health["can_post"] = False
                health["reason"] = "Account too new (must be 30+ days old)"
            
            logger.info(f"Account health: {health}")
            return health
            
        except Exception as e:
            logger.error(f"Error checking account health: {e}")
            return {"can_post": False, "reason": str(e)}
    
    def check_subreddit_access(self, subreddit: str) -> bool:
        """Check if account can post to a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            
        Returns:
            True if account can post
        """
        try:
            sub = self.reddit.subreddit(subreddit)
            
            # Try to check if we're banned
            # Note: PRAW doesn't have a direct "am I banned" check
            # Best we can do is try to verify access
            _ = sub.rules  # This will raise if we don't have access
            
            logger.debug(f"Account can access r/{subreddit}")
            return True
            
        except Exception as e:
            logger.warning(f"Cannot access r/{subreddit}: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def post_reply(
        self,
        post_id: str,
        comment_text: str,
        draft_id: str,
    ) -> Optional[str]:
        """Post a reply to a Reddit post.
        
        Args:
            post_id: Reddit post ID (e.g., "1oja7qb")
            comment_text: Comment content to post
            draft_id: Internal draft ID for tracking
            
        Returns:
            Comment ID if successful, None otherwise
        """
        try:
            submission = self.reddit.submission(id=post_id)
            
            # Post the comment
            comment = submission.reply(comment_text)
            comment_id = comment.id
            
            logger.info(
                f"Posted reply {comment_id} to post {post_id} (draft {draft_id})"
            )
            
            return comment_id
            
        except praw.exceptions.RedditAPIException as e:
            logger.error(f"Reddit API error posting reply: {e}")
            
            # Check for specific errors
            for subexception in e.items:
                if subexception.error_type == "RATELIMIT":
                    logger.warning("Hit rate limit, will retry...")
                    raise  # Trigger retry
                elif subexception.error_type == "THREAD_LOCKED":
                    logger.warning("Thread is locked, cannot post")
                    return None
                    
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error posting reply: {e}")
            return None
    
    def get_recent_activity(self, limit: int = 100) -> dict:
        """Get recent account activity for monitoring.
        
        Args:
            limit: Number of recent items to fetch
            
        Returns:
            Dict with activity stats
        """
        try:
            user = self.reddit.user.me()
            
            comments = list(user.comments.new(limit=limit))
            
            # Calculate promotional vs non-promotional
            promotional_count = 0
            for comment in comments:
                if "goodpods" in comment.body.lower():
                    promotional_count += 1
            
            total_count = len(comments)
            promotional_ratio = promotional_count / total_count if total_count > 0 else 0
            
            activity = {
                "total_comments": total_count,
                "promotional_comments": promotional_count,
                "promotional_ratio": promotional_ratio,
                "safe_to_post": promotional_ratio < 0.1,  # 10% rule
            }
            
            logger.info(f"Recent activity: {activity}")
            return activity
            
        except Exception as e:
            logger.error(f"Error fetching recent activity: {e}")
            return {"safe_to_post": False, "reason": str(e)}