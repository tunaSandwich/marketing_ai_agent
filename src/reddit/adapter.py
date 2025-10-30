"""Reddit API adapter with rate limiting and compliance features."""

from datetime import UTC, datetime, timedelta

import praw
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import RedditMetrics, RedditPost, ReplyResult
from ..utils.config import RedditConfig


class RedditAdapter:
    """Reddit API wrapper with rate limiting and compliance."""

    def __init__(self, config: RedditConfig) -> None:
        """Initialize Reddit adapter with configuration."""
        self._config = config
        self._reddit = praw.Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            user_agent=config.user_agent,
            username=config.username,
            password=config.password,
        )
        self._last_request_time: datetime | None = None

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting to comply with Reddit API limits."""
        if self._last_request_time is not None:
            time_since_last = datetime.now(UTC) - self._last_request_time
            min_interval = timedelta(seconds=60 / self._config.rate_limit_per_minute)

            if time_since_last < min_interval:
                sleep_time = (min_interval - time_since_last).total_seconds()
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                import time

                time.sleep(sleep_time)

        self._last_request_time = datetime.now(UTC)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search_posts(
        self,
        query: str,
        subreddits: list[str],
        limit: int = 20,
        time_filter: str = "day",
    ) -> list[RedditPost]:
        """Search for posts matching query in specified subreddits.

        Args:
            query: Search query string
            subreddits: List of subreddit names (without r/ prefix)
            limit: Maximum number of posts to return
            time_filter: Time filter for search (hour, day, week, month, year, all)

        Returns:
            List of matching Reddit posts
        """
        self._enforce_rate_limit()

        posts: list[RedditPost] = []

        try:
            for subreddit_name in subreddits:
                subreddit = self._reddit.subreddit(subreddit_name)

                # Search within subreddit
                search_results = subreddit.search(
                    query,
                    sort="new",
                    time_filter=time_filter,
                    limit=limit // len(subreddits),
                )

                for submission in search_results:
                    post = RedditPost(
                        id=submission.id,
                        title=submission.title,
                        content=submission.selftext or "",
                        subreddit=submission.subreddit.display_name,
                        score=submission.score,
                        created_at=datetime.fromtimestamp(submission.created_utc, tz=UTC),
                        url=f"https://reddit.com{submission.permalink}",
                        author=str(submission.author) if submission.author else "[deleted]",
                        num_comments=submission.num_comments,
                    )
                    posts.append(post)

                    if len(posts) >= limit:
                        break

                if len(posts) >= limit:
                    break

        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            raise

        logger.info(f"Found {len(posts)} posts for query: '{query}'")
        return posts

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def post_reply(self, post_id: str, content: str) -> ReplyResult:
        """Post a reply to a Reddit post.

        Args:
            post_id: Reddit post ID
            content: Reply content

        Returns:
            Reply result with metadata
        """
        self._enforce_rate_limit()

        try:
            submission = self._reddit.submission(id=post_id)
            comment = submission.reply(content)

            result = ReplyResult(
                reply_id=comment.id,
                reply_url=f"https://reddit.com{comment.permalink}",
                response_id="",  # This will be set by the caller
            )

            logger.info(f"Posted reply {result.reply_id} to post {post_id}")
            return result

        except Exception as e:
            logger.error(f"Error posting reply to {post_id}: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_metrics(self, reply_id: str) -> RedditMetrics:
        """Get metrics for a posted reply.

        Args:
            reply_id: Reddit comment ID

        Returns:
            Metrics for the reply
        """
        self._enforce_rate_limit()

        try:
            comment = self._reddit.comment(id=reply_id)
            comment.refresh()  # Ensure we have latest data

            metrics = RedditMetrics(
                reply_id=reply_id,
                upvotes=max(0, comment.score),  # Reddit score can be negative
                downvotes=max(0, -comment.score) if comment.score < 0 else 0,
                replies_received=len(comment.replies) if hasattr(comment, "replies") else 0,
                clicks_tracked=0,  # This would need separate tracking
            )

            return metrics

        except Exception as e:
            logger.error(f"Error getting metrics for reply {reply_id}: {e}")
            raise

    def check_karma_requirements(self, subreddit: str) -> bool:
        """Check if account meets karma requirements for subreddit.

        Args:
            subreddit: Subreddit name

        Returns:
            True if requirements are met
        """
        try:
            user = self._reddit.user.me()

            # Check overall karma
            total_karma = user.comment_karma + user.link_karma
            if total_karma < self._config.min_karma_required:
                logger.warning(
                    f"Insufficient karma: {total_karma} < {self._config.min_karma_required}"
                )
                return False

            # Check account age
            account_age = datetime.now(UTC) - datetime.fromtimestamp(
                user.created_utc, tz=UTC
            )
            required_age = timedelta(days=self._config.account_age_days)

            if account_age < required_age:
                logger.warning(
                    f"Account too new: {account_age.days} days < {self._config.account_age_days}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking karma requirements: {e}")
            return False

    def validate_post_eligibility(self, post: RedditPost) -> bool:
        """Validate if a post is eligible for reply.

        Args:
            post: Reddit post to validate

        Returns:
            True if post is eligible for reply
        """
        # Check post age (don't reply to very old posts)
        max_age = timedelta(hours=24)
        if datetime.now(UTC) - post.created_at > max_age:
            return False

        # Check minimum score
        if post.score < 1:
            return False

        # Check if post has been deleted
        return post.author != "[deleted]"
