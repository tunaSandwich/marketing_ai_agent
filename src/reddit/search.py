"""Reddit discovery logic for finding relevant posts."""

import re

from loguru import logger

from ..models import DiscoveryQuery, RedditPost
from .adapter import RedditAdapter


class RedditDiscovery:
    """Discovers relevant posts on Reddit based on intent patterns."""

    def __init__(self, reddit_adapter: RedditAdapter) -> None:
        """Initialize Reddit discovery with adapter."""
        self._reddit = reddit_adapter

    def create_podcast_discovery_query(self, subreddits: list[str]) -> DiscoveryQuery:
        """Create a discovery query for podcast recommendation requests.

        Args:
            subreddits: List of target subreddits

        Returns:
            Configured discovery query for podcast requests
        """
        return DiscoveryQuery(
            base_query=(
                '(title:"looking for" OR title:"recommend" OR title:"suggestions" '
                'OR title:"need") AND (selftext:"podcast" OR title:"podcast")'
            ),
            intent_patterns=[
                r"looking for .* podcast",
                r"recommend .* podcast",
                r"any .* podcast suggestions",
                r"need a podcast about",
                r"best podcast for",
                r"podcast recommendations for",
                r"what podcast.*should.*listen",
                r"suggest.*podcast",
            ],
            exclude_patterns=[
                r"how to start a podcast",
                r"podcast equipment",
                r"podcast hosting",
                r"promote my podcast",
                r"my podcast",
                r"advertising.*podcast",
                r"monetize.*podcast",
            ],
            subreddits=subreddits,
            max_results=20,
            min_score=1,
            max_age_hours=24,
        )

    def discover_opportunities(self, query: DiscoveryQuery) -> list[RedditPost]:
        """Discover posting opportunities based on query.

        Args:
            query: Discovery query configuration

        Returns:
            List of eligible posts for response
        """
        # Search for posts using the base query
        posts = self._reddit.search_posts(
            query=query.base_query,
            subreddits=query.subreddits,
            limit=query.max_results,
        )

        # Filter posts by intent patterns and exclusions
        eligible_posts: list[RedditPost] = []

        for post in posts:
            if self._matches_intent(post, query) and self._reddit.validate_post_eligibility(post):
                eligible_posts.append(post)

        logger.info(f"Found {len(eligible_posts)} eligible opportunities from {len(posts)} posts")
        return eligible_posts

    def _matches_intent(self, post: RedditPost, query: DiscoveryQuery) -> bool:
        """Check if post matches intent patterns and doesn't match exclusions.

        Args:
            post: Reddit post to check
            query: Discovery query with patterns

        Returns:
            True if post matches intent and doesn't match exclusions
        """
        # Combine title and content for pattern matching
        full_text = f"{post.title} {post.content}".lower()

        # Check if any intent pattern matches
        intent_match = False
        for pattern in query.intent_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                intent_match = True
                logger.debug(f"Post {post.id} matches intent pattern: {pattern}")
                break

        if not intent_match:
            return False

        # Check if any exclusion pattern matches
        for pattern in query.exclude_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                logger.debug(f"Post {post.id} excluded by pattern: {pattern}")
                return False

        return True

    def analyze_post_context(self, post: RedditPost) -> dict[str, str]:
        """Analyze post context for response generation.

        Args:
            post: Reddit post to analyze

        Returns:
            Dictionary with context information
        """
        context = {
            "subreddit": post.subreddit,
            "title": post.title,
            "content": post.content,
            "author": post.author,
            "intent": self._extract_intent(post),
            "topic": self._extract_topic(post),
            "genre": self._extract_genre(post),
        }

        return context

    def _extract_intent(self, post: RedditPost) -> str:
        """Extract the primary intent from a post.

        Args:
            post: Reddit post to analyze

        Returns:
            Primary intent (recommendation_request, comparison, etc.)
        """
        full_text = f"{post.title} {post.content}".lower()

        # Intent classification patterns
        if re.search(r"(recommend|suggestion|suggest)", full_text):
            return "recommendation_request"
        if re.search(r"(compare|vs|versus|better than)", full_text):
            return "comparison_request"
        if re.search(r"(best|top|favorite)", full_text):
            return "best_of_request"
        return "general_inquiry"

    def _extract_topic(self, post: RedditPost) -> str:
        """Extract the main topic/subject from a post.

        Args:
            post: Reddit post to analyze

        Returns:
            Main topic mentioned in the post
        """
        full_text = f"{post.title} {post.content}".lower()

        # Common topic patterns
        topic_patterns = {
            "true crime": r"true crime|murder|serial killer|investigation",
            "history": r"history|historical|past|ancient|medieval",
            "science": r"science|research|physics|chemistry|biology",
            "technology": r"tech|technology|programming|computer",
            "business": r"business|entrepreneur|startup|finance",
            "comedy": r"comedy|funny|humor|laugh",
            "news": r"news|current events|politics",
            "health": r"health|wellness|fitness|medical",
            "education": r"learning|education|academic|study",
            "entertainment": r"entertainment|tv|movie|celebrity",
        }

        for topic, pattern in topic_patterns.items():
            if re.search(pattern, full_text):
                return topic

        return "general"

    def _extract_genre(self, post: RedditPost) -> str | None:
        """Extract specific podcast genre mentioned in post.

        Args:
            post: Reddit post to analyze

        Returns:
            Specific genre if mentioned, None otherwise
        """
        full_text = f"{post.title} {post.content}".lower()

        # Podcast genre patterns
        genre_patterns = {
            "true_crime": r"true crime|murder mystery|investigation|detective",
            "comedy": r"comedy|funny|humor|comedic",
            "news": r"news|current events|daily news",
            "interview": r"interview|conversation|talk show",
            "storytelling": r"story|narrative|tales|storytelling",
            "educational": r"educational|learn|informative|academic",
            "business": r"business|entrepreneur|startup|finance",
            "health": r"health|wellness|fitness|mental health",
            "technology": r"tech|technology|programming|software",
            "sports": r"sports|football|basketball|baseball|soccer",
        }

        for genre, pattern in genre_patterns.items():
            if re.search(pattern, full_text):
                return genre

        return None
