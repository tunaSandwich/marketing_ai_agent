"""Interactive preview of engagement system responses.

Allows generating and regenerating comments to review quality before deployment.
"""

import os
import random
from unittest.mock import Mock
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


def show_helpful_examples(manager: RedditEngagementManager):
    """Generate 4 helpful comment examples."""
    print("\n" + "="*60)
    print("HELPFUL COMMENTS (No Brand Mention - Warming Mode)")
    print("="*60)
    
    test_posts = [
        ("Looking for true crime podcast recommendations", "I loved Serial, what else should I try?"),
        ("Need podcasts for my commute", "30 minute episodes would be ideal"),
        ("Best history podcasts?", "I like Dan Carlin's Hardcore History"),
        ("Science podcasts that aren't boring?", ""),
    ]
    
    budget = ActivityBudget(
        upvotes_target=10,
        comments_target=1,
        promotional_ratio=0.0,
        risk_tolerance=RiskTolerance.LOW,
        allowed_tiers=[1],
        max_posts_per_subreddit_per_day=3,
        comment_constraints=CommentConstraints(
            max_length=180,  # Target 180 with 240 buffer
            min_post_score=5,
            allow_follow_up_questions=False,
            allow_thread_replies=False,
            complexity_level=ComplexityLevel.SIMPLE,
        ),
    )
    
    for i, (title, content) in enumerate(test_posts, 1):
        print(f"\n[Example {i}/4]")
        print(f"Post Title: {title}")
        if content:
            print(f"Post Content: {content}")
        print("-"*60)
        
        post = create_mock_post(title, content)
        comment = manager._generate_comment(post, is_promotional=False, constraints=budget.comment_constraints)
        
        if comment:
            print(f"Generated Comment:\n{comment}\n")
            
            # Detailed validation check
            is_valid, failure_reasons = manager._validate_helpful_comment_with_reasons(comment, budget.comment_constraints)
            print(f"Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
            if not is_valid and failure_reasons:
                for reason in failure_reasons:
                    print(f"  - {reason}")
            print(f"Length: {len(comment)} chars")
        else:
            print("❌ Failed to generate comment")
        
        print()


def show_promotional_examples(manager: RedditEngagementManager):
    """Generate 4 promotional comment examples."""
    print("\n" + "="*60)
    print("PROMOTIONAL COMMENTS (Subtle Brand Mention - Active Mode)")
    print("="*60)
    
    test_posts = [
        ("How do you organize your podcasts?", "Using Apple Podcasts but it's getting messy"),
        ("Looking for podcast app recommendations", "Spotify is okay but want something better"),
        ("Best way to discover new podcasts?", "Always finding the same stuff"),
        ("How do you track which episodes you've listened to?", "Keep losing my place"),
    ]
    
    budget = ActivityBudget(
        upvotes_target=5,
        comments_target=1,
        promotional_ratio=1.0,  # Force promotional for testing
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
    
    for i, (title, content) in enumerate(test_posts, 1):
        print(f"\n[Example {i}/4]")
        print(f"Post Title: {title}")
        if content:
            print(f"Post Content: {content}")
        print("-"*60)
        
        post = create_mock_post(title, content)
        comment = manager._generate_comment(post, is_promotional=True, constraints=budget.comment_constraints)
        
        if comment:
            print(f"Generated Comment:\n{comment}\n")
            
            # Detailed validation and analysis
            is_valid, failure_reasons = manager._validate_promotional_comment_with_reasons(comment, budget.comment_constraints)
            brand_count = comment.lower().count("goodpods")
            has_link = str(manager.brand_config.primary_cta) in comment
            
            print(f"Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
            if not is_valid and failure_reasons:
                for reason in failure_reasons:
                    print(f"  - {reason}")
            print(f"Brand mentions: {brand_count}")
            print(f"Includes link: {'✅' if has_link else '❌'}")
            print(f"Length: {len(comment)} chars")
        else:
            print("❌ Failed to generate comment")
        
        print()


def custom_generation(manager: RedditEngagementManager):
    """Generate a custom comment."""
    print("\n" + "="*60)
    print("CUSTOM COMMENT GENERATION")
    print("="*60)
    
    print("\nEnter post details:")
    title = input("Post title: ")
    content = input("Post content (optional): ")
    
    mode = input("\nMode (1=helpful, 2=promotional): ")
    is_promotional = mode == "2"
    
    budget = ActivityBudget(
        upvotes_target=5,
        comments_target=1,
        promotional_ratio=1.0 if is_promotional else 0.0,
        risk_tolerance=RiskTolerance.MEDIUM,
        allowed_tiers=[1, 2],
        max_posts_per_subreddit_per_day=3,
        comment_constraints=CommentConstraints(
            max_length=300,
            min_post_score=0,
            allow_follow_up_questions=True,
            allow_thread_replies=True,
            complexity_level=ComplexityLevel.MODERATE,
        ),
    )
    
    print("\nGenerating...")
    post = create_mock_post(title, content)
    comment = manager._generate_comment(post, is_promotional=is_promotional, constraints=budget.comment_constraints)
    
    if comment:
        print(f"\n{'-'*60}")
        print(f"Generated Comment:\n{comment}")
        print(f"{'-'*60}\n")
        
        if is_promotional:
            is_valid = manager._validate_promotional_comment(comment)
        else:
            is_valid = manager._validate_helpful_comment(comment)
        
        print(f"Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
        print(f"Length: {len(comment)} chars")
    else:
        print("❌ Failed to generate comment")


def main():
    """Interactive CLI for previewing engagement system."""
    
    print("="*60)
    print("ENGAGEMENT SYSTEM PREVIEW")
    print("="*60)
    print("\nInitializing system...")
    
    # Check for environment variables
    if not os.getenv("REDDIT_CLIENT_ID") or not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠️  WARNING: Environment variables not set!")
        print("   Using test credentials - some features may not work.")
        print("\n   To use with real accounts, set these environment variables:")
        print("   - REDDIT_CLIENT_ID")
        print("   - REDDIT_CLIENT_SECRET")
        print("   - REDDIT_USER_AGENT")
        print("   - REDDIT_USERNAME")
        print("   - REDDIT_PASSWORD")
        print("   - ANTHROPIC_API_KEY")
        print("\n   Continuing with mock mode...")
    
    # Load configs with defaults for missing values
    reddit_config = RedditConfig(
        client_id=os.getenv("REDDIT_CLIENT_ID", "test_client_id"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET", "test_secret"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "test_agent/1.0"),
        username=os.getenv("REDDIT_USERNAME", "test_user"),
        password=os.getenv("REDDIT_PASSWORD", "test_pass"),
    )
    
    # Import centralized model config
    from src.models import get_default_model
    
    llm_config = LLMConfig(
        api_key=os.getenv("ANTHROPIC_API_KEY", "test_api_key"),
        model=get_default_model(),
        max_tokens=300,
        temperature=0.9,
    )
    
    print(f"Using model: {llm_config.model}")
    
    from pathlib import Path
    brands_dir = Path(__file__).parent.parent / "brands"
    brand_loader = BrandLoader(brands_dir)
    brand_config = brand_loader.load_brand_config("goodpods")
    
    # Initialize manager with error handling
    print("Attempting to initialize Reddit Engagement Manager...")
    print("📚 Loading RAG indexes...")
    print("🔗 Connecting to Reddit...")
    print("⏳ This may take 30-60 seconds...")
    
    import signal
    import sys
    
    def timeout_handler(signum, frame):
        print("\n⏰ Initialization timed out!")
        print("This might be due to:")
        print("- Slow network connection") 
        print("- Reddit API being slow")
        print("- Large RAG indexes loading")
        print("\nTry running the validation-only test instead:")
        print("  python scripts/test_validation_only.py")
        sys.exit(1)
    
    # Set 90 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(90)
    
    try:
        manager = RedditEngagementManager(
            reddit_config=reddit_config,
            llm_config=llm_config,
            brand_config=brand_config,
        )
        signal.alarm(0)  # Cancel timeout
        print("✅ System initialized\n")
    except Exception as e:
        print(f"\n❌ Error initializing engagement manager:")
        print(f"   {type(e).__name__}: {e}")
        print("\nThis usually happens when:")
        print("1. Reddit credentials are invalid or Reddit is unreachable")
        print("2. RAG indexes haven't been created")
        print("3. Network connectivity issues")
        print("\nTroubleshooting:")
        print("• Create indexes: python scripts/index_brand_knowledge.py goodpods")
        print("• Create indexes: python scripts/index_brand_knowledge.py warming")
        print("• Check .env file has valid credentials")
        print("• Try the validation-only test: python scripts/test_validation_only.py")
        print("\nExiting...")
        return
    
    # Interactive menu
    while True:
        print("\n" + "="*60)
        print("MENU")
        print("="*60)
        print("1. Generate 4 helpful comments (warming mode)")
        print("2. Generate 4 promotional comments (active mode)")
        print("3. Generate custom comment")
        print("4. Show account health")
        print("5. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            show_helpful_examples(manager)
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            show_promotional_examples(manager)
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            custom_generation(manager)
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            health = manager.get_account_health()
            print(f"\n[ACCOUNT HEALTH]")
            print(f"Karma: {health.karma}")
            print(f"Age: {health.age_days:.1f} days")
            print(f"Health Score: {health.health_score:.1f}/100")
            print(f"Account State: {health.account_state.value.upper()}")
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            print("\nExiting...")
            break
        
        else:
            print("\n❌ Invalid choice")


if __name__ == "__main__":
    main()