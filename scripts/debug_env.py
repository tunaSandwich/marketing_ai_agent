#!/usr/bin/env python3
"""Debug environment variables and config loading."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

def debug_environment():
    """Check all environment variables."""
    print("="*60)
    print("ENVIRONMENT VARIABLE DIAGNOSIS")
    print("="*60)
    
    # Load .env file
    env_file = Path(__file__).parent.parent / ".env"
    print(f"\n📁 Loading .env from: {env_file}")
    print(f"   File exists: {env_file.exists()}")
    
    if env_file.exists():
        print(f"   File size: {env_file.stat().st_size} bytes")
        load_dotenv(env_file)
        print("   ✅ .env file loaded")
    else:
        print("   ❌ .env file not found")
        return
    
    # Check required variables
    required_vars = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET", 
        "REDDIT_USER_AGENT",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
        "ANTHROPIC_API_KEY"
    ]
    
    print("\n🔍 Checking environment variables:")
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            print(f"   ❌ {var}: Not set")
            all_good = False
        elif value.strip() == "":
            print(f"   ❌ {var}: Empty string")
            all_good = False
        elif len(value) < 5:
            print(f"   ⚠️  {var}: Very short ({len(value)} chars) - '{value}'")
        else:
            # Mask sensitive values
            if "SECRET" in var or "PASSWORD" in var or "API_KEY" in var:
                masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
                print(f"   ✅ {var}: {len(value)} chars - {masked}")
            else:
                print(f"   ✅ {var}: {len(value)} chars - {value}")
    
    return all_good


def test_config_creation():
    """Test creating Reddit and LLM configs."""
    print("\n" + "="*60)
    print("CONFIG OBJECT CREATION TEST")
    print("="*60)
    
    try:
        from src.utils.config import RedditConfig
        print("\n🔧 Testing RedditConfig creation...")
        
        reddit_config = RedditConfig(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
        )
        print("   ✅ RedditConfig created successfully")
        print(f"   Username: {reddit_config.username}")
        print(f"   User Agent: {reddit_config.user_agent}")
        
    except Exception as e:
        print(f"   ❌ RedditConfig failed: {type(e).__name__}: {e}")
        return False
    
    try:
        from src.utils.config import LLMConfig
        print("\n🤖 Testing LLMConfig creation...")
        
        llm_config = LLMConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.9,
        )
        print("   ✅ LLMConfig created successfully")
        print(f"   Model: {llm_config.model}")
        
    except Exception as e:
        print(f"   ❌ LLMConfig failed: {type(e).__name__}: {e}")
        return False
        
    return True


def test_reddit_connection():
    """Test actual Reddit connection."""
    print("\n" + "="*60)
    print("REDDIT CONNECTION TEST")
    print("="*60)
    
    try:
        import praw
        print("\n🔗 Testing Reddit connection...")
        
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
        )
        
        # Test connection
        user = reddit.user.me()
        print(f"   ✅ Connected as: u/{user.name}")
        print(f"   Karma: {user.link_karma + user.comment_karma}")
        
    except Exception as e:
        print(f"   ❌ Reddit connection failed: {type(e).__name__}: {e}")
        return False
        
    return True


def test_brand_loading():
    """Test brand configuration loading."""
    print("\n" + "="*60)
    print("BRAND LOADING TEST")
    print("="*60)
    
    try:
        from src.brand.loader import BrandLoader
        print("\n📦 Testing brand loading...")
        
        brands_dir = Path(__file__).parent.parent / "brands"
        brand_loader = BrandLoader(brands_dir)
        brand_config = brand_loader.load_brand_config("goodpods")
        
        print(f"   ✅ Brand loaded: {brand_config.brand_name}")
        print(f"   Primary CTA: {brand_config.primary_cta}")
        
    except Exception as e:
        print(f"   ❌ Brand loading failed: {type(e).__name__}: {e}")
        return False
        
    return True


def test_rag_indexes():
    """Test RAG index loading."""
    print("\n" + "="*60)
    print("RAG INDEXES TEST")
    print("="*60)
    
    try:
        from src.rag.retriever import KnowledgeRetriever
        print("\n📚 Testing RAG indexes...")
        
        # Test warming index
        warming_path = Path("brands/warming/index")
        if warming_path.exists():
            warming_retriever = KnowledgeRetriever(
                index_dir=warming_path,
                model_name="all-MiniLM-L6-v2",
            )
            print(f"   ✅ Warming index loaded")
        else:
            print(f"   ❌ Warming index missing: {warming_path}")
            return False
        
        # Test goodpods index
        goodpods_path = Path("brands/goodpods/index")
        if goodpods_path.exists():
            goodpods_retriever = KnowledgeRetriever(
                index_dir=goodpods_path,
                model_name="all-MiniLM-L6-v2",
            )
            print(f"   ✅ Goodpods index loaded")
        else:
            print(f"   ❌ Goodpods index missing: {goodpods_path}")
            return False
            
    except Exception as e:
        print(f"   ❌ RAG indexes failed: {type(e).__name__}: {e}")
        return False
        
    return True


def main():
    """Run all diagnostics."""
    print("🔍 DIAGNOSING ENGAGEMENT SYSTEM SETUP")
    
    # Step 1: Check environment variables
    env_ok = debug_environment()
    
    if not env_ok:
        print("\n❌ Environment variables missing - fix .env file first")
        return
    
    # Step 2: Test config creation
    config_ok = test_config_creation()
    
    if not config_ok:
        print("\n❌ Config creation failed - check environment variable values")
        return
    
    # Step 3: Test brand loading
    brand_ok = test_brand_loading()
    
    if not brand_ok:
        print("\n❌ Brand loading failed")
        return
    
    # Step 4: Test RAG indexes
    rag_ok = test_rag_indexes()
    
    if not rag_ok:
        print("\n❌ RAG indexes missing - run indexing scripts")
        return
    
    # Step 5: Test Reddit connection
    reddit_ok = test_reddit_connection()
    
    if not reddit_ok:
        print("\n❌ Reddit connection failed - check credentials")
        return
    
    print("\n" + "="*60)
    print("✅ ALL DIAGNOSTICS PASSED!")
    print("="*60)
    print("\n🎯 Your system should work with:")
    print("   python scripts/test_engagement_preview.py")


if __name__ == "__main__":
    main()