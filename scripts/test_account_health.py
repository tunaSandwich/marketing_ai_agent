#!/usr/bin/env python3
"""Test account health retrieval specifically."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.reddit.engagement import RedditEngagementManager
from src.utils.config import RedditConfig, LLMConfig
from src.brand.loader import BrandLoader

load_dotenv()

def test_account_health():
    """Test account health retrieval."""
    print("="*60)
    print("ACCOUNT HEALTH TEST")
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
    
    print("\n💊 Testing account health retrieval...")
    health = manager.get_account_health()
    
    print(f"\n[ACCOUNT HEALTH RESULTS]")
    print(f"Karma: {health.karma}")
    print(f"Age: {health.age_days:.1f} days")
    print(f"Recent Activity Quality: {health.recent_activity_quality}")
    print(f"Health Score: {health.health_score:.1f}/100")
    print(f"Account State: {health.account_state.value.upper()}")
    
    print("\n✅ Account health test completed successfully!")

if __name__ == "__main__":
    test_account_health()