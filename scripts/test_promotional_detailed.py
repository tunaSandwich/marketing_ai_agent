#!/usr/bin/env python3
"""Test promotional comment generation with detailed validation feedback."""

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

def test_promotional():
    """Test promotional comments with detailed validation."""
    print("="*60)
    print("PROMOTIONAL COMMENT VALIDATION TEST")
    print("="*60)
    
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
    
    test_posts = [
        ("How do you organize your podcasts?", "Using Apple Podcasts but it's getting messy"),
        ("Looking for podcast app recommendations", "Spotify is okay but want something better"),
    ]
    
    budget = ActivityBudget(
        upvotes_target=5,
        comments_target=1,
        promotional_ratio=1.0,
        risk_tolerance=RiskTolerance.HIGH,
        allowed_tiers=[1, 2, 3],
        max_posts_per_subreddit_per_day=3,
        comment_constraints=CommentConstraints(
            max_length=240,  # Target 240 with 320 buffer
            min_post_score=0,
            allow_follow_up_questions=True,
            allow_thread_replies=True,
            complexity_level=ComplexityLevel.COMPLEX,
        ),
    )
    
    success_count = 0
    for i, (title, content) in enumerate(test_posts, 1):
        print(f"\n[Test {i}/{len(test_posts)}]")
        print(f"Post: {title}")
        if content:
            print(f"Content: {content}")
        print("-" * 40)
        
        post = create_mock_post(title, content)
        comment = manager._generate_comment(post, is_promotional=True, constraints=budget.comment_constraints)
        
        if comment:
            print(f"✅ Generated Comment:")
            # Show first 150 chars, then truncate
            if len(comment) > 150:
                print(f"{comment[:150]}...")
            else:
                print(comment)
            
            # Detailed validation
            is_valid, failure_reasons = manager._validate_promotional_comment_with_reasons(comment, budget.comment_constraints)
            brand_count = comment.lower().count("goodpods")
            has_link = str(manager.brand_config.primary_cta) in comment
            
            print(f"\nValidation: {'✅ PASS' if is_valid else '❌ FAIL'}")
            if not is_valid and failure_reasons:
                print("Failure reasons:")
                for reason in failure_reasons:
                    print(f"  - {reason}")
            
            print(f"\nMetrics:")
            print(f"  Brand mentions: {brand_count}")
            print(f"  Includes link: {'✅' if has_link else '❌'}")
            print(f"  Length: {len(comment)}/{budget.comment_constraints.max_length} chars")
            
            if is_valid:
                success_count += 1
        else:
            print("❌ Failed to generate comment")
    
    print("\n" + "="*60)
    print(f"RESULTS: {success_count}/{len(test_posts)} comments passed validation")
    print("="*60)
    
    if success_count == len(test_posts):
        print("✅ All promotional comments passed validation!")
    else:
        print("⚠️  Some promotional comments need improvement.")
        print("\nCommon issues:")
        print("- Too long (> 300 chars)")
        print("- Missing personal indicators ('I use', 'I've been')")
        print("- Too corporate sounding")

if __name__ == "__main__":
    test_promotional()