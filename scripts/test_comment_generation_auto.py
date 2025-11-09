#!/usr/bin/env python3
"""Auto-test comment generation without requiring user input."""

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

def test_helpful_comments():
    """Test helpful comment generation automatically."""
    print("="*60)
    print("AUTOMATED COMMENT GENERATION TEST")
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
    
    print(f"Using model: {llm_config.model}")
    
    brands_dir = Path(__file__).parent.parent / "brands"
    brand_loader = BrandLoader(brands_dir)
    brand_config = brand_loader.load_brand_config("goodpods")
    
    print("\n🔧 Initializing engagement manager...")
    manager = RedditEngagementManager(
        reddit_config=reddit_config,
        llm_config=llm_config,
        brand_config=brand_config,
    )
    
    print("\n📝 Testing helpful comment generation...")
    
    test_posts = [
        ("Looking for true crime podcast recommendations", "I loved Serial, what else should I try?"),
        ("Need podcasts for my commute", "30 minute episodes would be ideal"),
    ]
    
    budget = ActivityBudget(
        upvotes_target=10,
        comments_target=1,
        promotional_ratio=0.0,
        risk_tolerance=RiskTolerance.LOW,
        allowed_tiers=[1],
        max_posts_per_subreddit_per_day=3,
        comment_constraints=CommentConstraints(
            max_length=180,  # Reduced to give model more buffer
            min_post_score=5,
            allow_follow_up_questions=False,
            allow_thread_replies=False,
            complexity_level=ComplexityLevel.SIMPLE,
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
        comment = manager._generate_comment(post, is_promotional=False, constraints=budget.comment_constraints)
        
        if comment:
            print(f"✅ Generated Comment:")
            print(f"{comment[:100]}..." if len(comment) > 100 else comment)
            
            # Detailed validation
            is_valid, failure_reasons = manager._validate_helpful_comment_with_reasons(comment, budget.comment_constraints)
            print(f"\nValidation: {'✅ PASS' if is_valid else '❌ FAIL'}")
            if not is_valid and failure_reasons:
                for reason in failure_reasons:
                    print(f"  - {reason}")
            print(f"Length: {len(comment)}/{budget.comment_constraints.max_length} chars")
            if is_valid:
                success_count += 1
        else:
            print("❌ Failed to generate comment")
    
    print("\n" + "="*60)
    print(f"RESULTS: {success_count}/{len(test_posts)} comments generated successfully")
    print("="*60)
    
    if success_count == len(test_posts):
        print("✅ All tests passed! Comment generation is working correctly.")
    else:
        print("⚠️  Some tests failed. Check model configuration or prompts.")

if __name__ == "__main__":
    test_helpful_comments()