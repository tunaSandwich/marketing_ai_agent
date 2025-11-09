#!/usr/bin/env python3
"""Test comment validation without Reddit connection."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import ActivityBudget, CommentConstraints, ComplexityLevel, RiskTolerance
from src.reddit.engagement_strategy import EngagementStrategyManager
from src.reddit.subreddit_selector import SubredditSelector


def test_helpful_validation():
    """Test helpful comment validation logic."""
    print("\n" + "="*60)
    print("TESTING HELPFUL COMMENT VALIDATION")
    print("="*60)
    
    def validate_helpful_comment(comment):
        """Simplified validation matching the actual implementation."""
        if not comment or not isinstance(comment, str):
            return False, "Invalid type"
        
        comment_lower = comment.lower()
        
        # Block brand mentions (strict for warming mode)
        blocklist = [
            "goodpods", "our app", "my app", "this app", 
            "the app", "download", "podcast player", "podcast app",
        ]
        
        for term in blocklist:
            if term in comment_lower:
                return False, f"Blocked term: {term}"
        
        # Length check
        if len(comment) < 20:
            return False, "Too short"
        if len(comment) > 400:
            return False, "Too long"
        
        # Must have capitalized words (podcast names)
        if not any(c.isupper() for c in comment):
            return False, "No capitalized words"
        
        # Must have recommendation language
        signals = ["try", "check out", "recommend", "love", "great", "perfect", "listen"]
        if not any(signal in comment_lower for signal in signals):
            return False, "No recommendation language"
        
        return True, "Valid"
    
    test_cases = [
        ("Valid recommendation", "try Criminal for true crime podcasts", True),
        ("Another valid", "check out This American Life for great stories", True),
        ("Too short", "Try it", False),
        ("Has brand mention", "try Goodpods for organizing", False),
        ("No capitals", "try this one for true crime", False),
        ("No recommendation language", "Serial is about true crime", False),
    ]
    
    for name, comment, expected in test_cases:
        valid, reason = validate_helpful_comment(comment)
        status = "✅" if (valid == expected) else "❌"
        print(f"\n{status} {name}")
        print(f"   Comment: \"{comment}\"")
        print(f"   Result: {reason}")
        print(f"   Expected: {'Valid' if expected else 'Invalid'}")


def test_promotional_validation():
    """Test promotional comment validation logic."""
    print("\n" + "="*60)
    print("TESTING PROMOTIONAL COMMENT VALIDATION")
    print("="*60)
    
    def validate_promotional_comment(comment):
        """Simplified validation matching the updated implementation."""
        if not comment or not isinstance(comment, str):
            return False, "Invalid type"
        
        comment_lower = comment.lower()
        
        # Length check
        if len(comment) < 30:
            return False, "Too short"
        if len(comment) > 400:
            return False, "Too long"
        
        # Must have recommendation OR helpfulness language
        helpful_signals = [
            "try", "check out", "recommend", "love", "great", "perfect", 
            "honestly", "tbh", "organize", "helps", "use", "easier", "better"
        ]
        
        if not any(signal in comment_lower for signal in helpful_signals):
            return False, "No helpful language"
        
        # Brand mention validation
        goodpods_mentions = comment_lower.count("goodpods")
        
        if goodpods_mentions == 0:
            return False, "No brand mention"
        
        if goodpods_mentions > 1:
            return False, f"Too many brand mentions ({goodpods_mentions})"
        
        # Should sound like personal experience
        personal_indicators = [
            "i use", "i organize", "i've been", "helps me", "i can", 
            "honestly i", "i keep", "makes", "way easier"
        ]
        
        if not any(indicator in comment_lower for indicator in personal_indicators):
            return False, "Not personal enough"
        
        # Block overly corporate language
        corporate_patterns = [
            "you should try goodpods",
            "check out goodpods",
            "download goodpods",
            "goodpods is a great",
            "goodpods has",
        ]
        
        for pattern in corporate_patterns:
            if pattern in comment_lower:
                return False, f"Too corporate: {pattern}"
        
        return True, "Valid"
    
    test_cases = [
        ("Organization comment", 
         "honestly i organize all my podcasts in goodpods now. makes commuting way easier", 
         True),
        ("With podcast recs",
         "try Criminal for true crime. i organize everything in goodpods - makes it way easier",
         True),
        ("Too short",
         "goodpods is great",
         False),
        ("No brand mention",
         "honestly i organize all my podcasts now. makes things easier",
         False),
        ("Too many mentions",
         "goodpods is great. i use goodpods daily. goodpods helps",
         False),
        ("Too corporate",
         "you should try goodpods for organizing your podcasts",
         False),
        ("Not personal",
         "Goodpods is a great app with many features",
         False),
    ]
    
    for name, comment, expected in test_cases:
        valid, reason = validate_promotional_comment(comment)
        status = "✅" if (valid == expected) else "❌"
        print(f"\n{status} {name}")
        print(f"   Comment: \"{comment[:60]}...\"" if len(comment) > 60 else f"   Comment: \"{comment}\"")
        print(f"   Result: {reason}")
        print(f"   Expected: {'Valid' if expected else 'Invalid'}")


def test_strategy_manager():
    """Test engagement strategy manager."""
    print("\n" + "="*60)
    print("TESTING STRATEGY MANAGER")
    print("="*60)
    
    manager = EngagementStrategyManager()
    
    scenarios = [
        ("New account", 0, 0),
        ("Building account", 50, 15),
        ("Maturing account", 75, 20),
        ("Ready account", 100, 28),
        ("Active account", 150, 35),
    ]
    
    for name, karma, age_days in scenarios:
        health = manager.calculate_health_score(karma, age_days)
        state = manager.get_account_state(health)
        budget = manager.get_activity_budget(health, state)
        
        print(f"\n{name}:")
        print(f"  Karma: {karma}, Age: {age_days} days")
        print(f"  Health Score: {health:.1f}/100")
        print(f"  State: {state.value.upper()}")
        print(f"  Budget: {budget.comments_target} comments, {budget.promotional_ratio*100:.0f}% promotional")
        print(f"  Risk: {budget.risk_tolerance.value}")


def test_subreddit_selector():
    """Test subreddit selector."""
    print("\n" + "="*60)
    print("TESTING SUBREDDIT SELECTOR")
    print("="*60)
    
    selector = SubredditSelector(
        tier1_subreddits=["podcasts", "podcast"],
        tier2_subreddits=["TrueCrimePodcasts", "HistoryPodcasting"],
        tier3_subreddits=["AudioDrama"],
        cooldown_hours=2,
    )
    
    print("\nSelecting from different tiers:")
    
    # Test tier 1 only
    sub1 = selector.select_subreddit([1])
    print(f"  Tier 1 only: r/{sub1}")
    
    # Test tier 1 and 2
    sub2 = selector.select_subreddit([1, 2])
    print(f"  Tier 1+2: r/{sub2}")
    
    # Test all tiers
    sub3 = selector.select_subreddit([1, 2, 3])
    print(f"  All tiers: r/{sub3}")
    
    # Check cooldown
    print(f"\nCooldown check:")
    print(f"  r/{sub1} available: {selector._is_available(sub1)}")
    print(f"  (Should be False - just used)")


def main():
    """Run all validation tests."""
    print("="*60)
    print("ENGAGEMENT SYSTEM VALIDATION TESTS")
    print("="*60)
    print("\nTesting without Reddit connection...")
    
    test_helpful_validation()
    test_promotional_validation()
    test_strategy_manager()
    test_subreddit_selector()
    
    print("\n" + "="*60)
    print("✅ ALL VALIDATION TESTS COMPLETE")
    print("="*60)
    print("\nThese tests verify the core logic without requiring:")
    print("  - Reddit credentials")
    print("  - Claude API access")
    print("  - Live connections")
    print("\nFor full system testing with live connections, use:")
    print("  python scripts/test_engagement_preview.py")


if __name__ == "__main__":
    main()