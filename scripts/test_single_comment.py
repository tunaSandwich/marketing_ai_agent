#!/usr/bin/env python3
"""Test single comment generation to verify model fix."""

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
from src.models import ActivityBudget, CommentConstraints, ComplexityLevel, RiskTolerance

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

def test_single_comment():
    """Test generating a single helpful comment."""
    print("="*60)
    print("SINGLE COMMENT GENERATION TEST")
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
        model="claude-3-haiku-20240307",
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
    
    print("\n💬 Testing comment generation...")
    
    # Create test post
    post = create_mock_post(
        title="Looking for true crime podcast recommendations",
        content="I loved Serial, what else should I try?"
    )
    
    # Create constraints for helpful comment
    constraints = CommentConstraints(
        max_length=150,
        min_post_score=5,
        allow_follow_up_questions=False,
        allow_thread_replies=False,
        complexity_level=ComplexityLevel.SIMPLE,
    )
    
    print(f"Post: {post.title}")
    if post.selftext:
        print(f"Content: {post.selftext}")
    print("-" * 40)
    
    # Generate comment
    comment = manager._generate_comment(post, is_promotional=False, constraints=constraints)
    
    if comment:
        print(f"✅ Generated Comment:\n{comment}\n")
        
        # Validate comment
        is_valid = manager._validate_helpful_comment(comment)
        print(f"Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
        print(f"Length: {len(comment)} chars")
        print(f"Model Used: {llm_config.model}")
    else:
        print("❌ Failed to generate comment")
        
    print("\n" + "="*60)

if __name__ == "__main__":
    test_single_comment()