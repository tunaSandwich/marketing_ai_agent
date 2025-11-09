#!/usr/bin/env python3
"""Step-by-step initialization test to find where it hangs."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

def test_step_by_step():
    """Test each component individually."""
    print("="*60)
    print("STEP-BY-STEP INITIALIZATION TEST")
    print("="*60)
    
    # Load environment
    load_dotenv()
    
    # Step 1: Test imports
    print("\n1️⃣ Testing imports...")
    try:
        import praw
        from src.utils.config import RedditConfig, LLMConfig
        from src.brand.loader import BrandLoader
        from src.llm.client import ClaudeClient
        from src.rag.retriever import KnowledgeRetriever
        print("   ✅ All imports successful")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return
    
    # Step 2: Create configs
    print("\n2️⃣ Creating configurations...")
    try:
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
        print("   ✅ Configurations created")
    except Exception as e:
        print(f"   ❌ Config creation failed: {e}")
        return
    
    # Step 3: Load brand config
    print("\n3️⃣ Loading brand configuration...")
    try:
        brands_dir = Path(__file__).parent.parent / "brands"
        brand_loader = BrandLoader(brands_dir)
        brand_config = brand_loader.load_brand_config("goodpods")
        print(f"   ✅ Brand config loaded: {brand_config.brand_name}")
    except Exception as e:
        print(f"   ❌ Brand loading failed: {e}")
        return
    
    # Step 4: Create Reddit client
    print("\n4️⃣ Creating Reddit client...")
    try:
        reddit = praw.Reddit(
            client_id=reddit_config.client_id,
            client_secret=reddit_config.client_secret,
            user_agent=reddit_config.user_agent,
            username=reddit_config.username,
            password=reddit_config.password,
        )
        print("   ✅ Reddit client created")
    except Exception as e:
        print(f"   ❌ Reddit client failed: {e}")
        return
    
    # Step 5: Create Claude client
    print("\n5️⃣ Creating Claude client...")
    try:
        claude_client = ClaudeClient(llm_config)
        print("   ✅ Claude client created")
    except Exception as e:
        print(f"   ❌ Claude client failed: {e}")
        return
    
    # Step 6: Load warming RAG
    print("\n6️⃣ Loading warming RAG retriever...")
    try:
        warming_index_path = Path("brands/warming/index")
        warming_retriever = KnowledgeRetriever(
            index_dir=warming_index_path,
            model_name="all-MiniLM-L6-v2",
        )
        print("   ✅ Warming retriever loaded")
    except Exception as e:
        print(f"   ❌ Warming retriever failed: {e}")
        return
    
    # Step 7: Load brand RAG
    print("\n7️⃣ Loading brand RAG retriever...")
    try:
        brand_index_path = Path(f"brands/{brand_config.brand_id}/index")
        brand_retriever = KnowledgeRetriever(
            index_dir=brand_index_path,
            model_name="all-MiniLM-L6-v2",
        )
        print("   ✅ Brand retriever loaded")
    except Exception as e:
        print(f"   ❌ Brand retriever failed: {e}")
        return
    
    # Step 8: Test Reddit connection
    print("\n8️⃣ Testing Reddit connection...")
    try:
        user = reddit.user.me()
        print(f"   ✅ Connected as u/{user.name}")
    except Exception as e:
        print(f"   ❌ Reddit connection failed: {e}")
        return
    
    # Step 9: Create strategy manager
    print("\n9️⃣ Creating strategy manager...")
    try:
        from src.reddit.engagement_strategy import EngagementStrategyManager
        strategy_manager = EngagementStrategyManager()
        print("   ✅ Strategy manager created")
    except Exception as e:
        print(f"   ❌ Strategy manager failed: {e}")
        return
    
    # Step 10: Create subreddit selector
    print("\n🔟 Creating subreddit selector...")
    try:
        from src.reddit.subreddit_selector import SubredditSelector
        subreddit_selector = SubredditSelector(
            tier1_subreddits=brand_config.subreddits_tier1,
            tier2_subreddits=brand_config.subreddits_tier2,
            tier3_subreddits=brand_config.subreddits_tier3,
            cooldown_hours=2,
        )
        print("   ✅ Subreddit selector created")
    except Exception as e:
        print(f"   ❌ Subreddit selector failed: {e}")
        return
    
    print("\n" + "="*60)
    print("✅ ALL COMPONENTS INITIALIZED SUCCESSFULLY!")
    print("="*60)
    print("\n🎯 Individual components work fine.")
    print("The issue might be in the full RedditEngagementManager initialization.")
    print("\nTry the working validation test:")
    print("  python scripts/test_validation_only.py")


if __name__ == "__main__":
    test_step_by_step()