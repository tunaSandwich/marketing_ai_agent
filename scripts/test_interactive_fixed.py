#!/usr/bin/env python3
"""Test the fixed interactive preview for promotional comments."""

import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.reddit.engagement import RedditEngagementManager
from src.utils.config import RedditConfig, LLMConfig
from src.brand.loader import BrandLoader
from src.models import ActivityBudget, CommentConstraints, ComplexityLevel, RiskTolerance, get_default_model

load_dotenv()

def create_mock_post(title: str, content: str = ""):
    """Create mock Reddit post."""
    post = Mock()
    post.id = "test_post"
    post.title = title
    post.selftext = content
    post.subreddit = Mock()
    post.subreddit.display_name = "podcasts"
    post.score = 10
    post.created_utc = 1234567890.0
    post.permalink = "/r/podcasts/test"
    post.author = Mock()
    post.author.name = "test_user"
    post.num_comments = 5
    return post

def show_promotional_examples(manager: RedditEngagementManager):
    """Generate promotional comment examples - same as the failing function."""
    print("\n" + "="*60)
    print("PROMOTIONAL COMMENTS (Subtle Brand Mention - Active Mode)")
    print("="*60)
    
    test_posts = [
        ("How do you organize your podcasts?", "Using Apple Podcasts but it's getting messy"),
    ]
    
    budget = ActivityBudget(
        upvotes_target=5,
        comments_target=1,
        promotional_ratio=1.0,  # Force promotional for testing
        risk_tolerance=RiskTolerance.HIGH,
        allowed_tiers=[1, 2, 3],
        max_posts_per_subreddit_per_day=3,
        comment_constraints=CommentConstraints(
            max_length=300,
            min_post_score=0,
            allow_follow_up_questions=True,
            allow_thread_replies=True,
            complexity_level=ComplexityLevel.COMPLEX,
        ),
    )
    
    for i, (title, content) in enumerate(test_posts, 1):
        print(f"\n[Example {i}/1]")
        print(f"Post Title: {title}")
        if content:
            print(f"Post Content: {content}")
        print("-"*60)
        
        post = create_mock_post(title, content)
        comment = manager._generate_comment(post, is_promotional=True, constraints=budget.comment_constraints)
        
        if comment:
            print(f"Generated Comment:\n{comment}\n")
            
            # This is the line that was causing the error - now fixed
            is_valid = manager._validate_promotional_comment(comment)
            brand_count = comment.lower().count("goodpods")
            has_link = str(manager.brand_config.primary_cta) in comment  # FIXED: Added str()
            
            print(f"Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
            print(f"Brand mentions: {brand_count}")
            print(f"Includes link: {'✅' if has_link else '❌'}")
            print(f"Length: {len(comment)} chars")
        else:
            print("❌ Failed to generate comment")
        
        print()

def main():
    """Test the fixed promotional comment generation."""
    print("Testing Fixed Promotional Comment Generation")
    
    # Load configs
    reddit_config = RedditConfig(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
    )
    
    llm_config = LLMConfig(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model=get_default_model(),
        max_tokens=300,
        temperature=0.9,
    )
    
    brands_dir = Path(__file__).parent.parent / "brands"
    brand_loader = BrandLoader(brands_dir)
    brand_config = brand_loader.load_brand_config("goodpods")
    
    print("\n🔧 Initializing engagement manager...")
    manager = RedditEngagementManager(
        reddit_config=reddit_config,
        llm_config=llm_config,
        brand_config=brand_config,
    )
    
    # Test the fixed promotional examples function
    show_promotional_examples(manager)
    
    print("✅ Test completed without crashes!")

if __name__ == "__main__":
    main()