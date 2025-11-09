"""Engagement strategy manager - calculates health scores and activity budgets."""

import random
from typing import Dict, List
from loguru import logger

from ..models import (
    AccountState,
    ActivityBudget,
    CommentConstraints,
    ComplexityLevel,
    RiskTolerance,
    AccountHealth,
)


class EngagementStrategyManager:
    """Manages engagement strategy based on account health."""
    
    def __init__(self):
        """Initialize strategy manager."""
        logger.info("EngagementStrategyManager initialized")
    
    def calculate_health_score(
        self,
        karma: int,
        age_days: float,
        recent_activity_quality: float = 0.5,
    ) -> float:
        """Calculate account health score (0-100).
        
        Args:
            karma: Current account karma
            age_days: Account age in days
            recent_activity_quality: Quality of recent activity (0-1)
            
        Returns:
            Health score from 0-100
        """
        # Karma component (0-50 points)
        karma_score = min(karma / 100 * 50, 50)
        
        # Age component (0-40 points)
        age_score = min(age_days / 30 * 40, 40)
        
        # Activity quality component (0-10 points)
        quality_score = recent_activity_quality * 10
        
        total = karma_score + age_score + quality_score
        health_score = min(total, 100.0)
        
        logger.debug(
            f"Health calculation: karma={karma_score:.1f}, "
            f"age={age_score:.1f}, quality={quality_score:.1f}, "
            f"total={health_score:.1f}"
        )
        
        return health_score
    
    def get_account_state(self, health_score: float) -> AccountState:
        """Determine account state from health score.
        
        Args:
            health_score: Health score (0-100)
            
        Returns:
            Account state enum
        """
        if health_score < 25:
            return AccountState.NEW
        elif health_score < 50:
            return AccountState.BUILDING
        elif health_score < 75:
            return AccountState.MATURING
        elif health_score < 90:
            return AccountState.READY
        else:
            return AccountState.ACTIVE
    
    def get_activity_budget(
        self,
        health_score: float,
        account_state: AccountState,
    ) -> ActivityBudget:
        """Get activity budget for current health score.
        
        Args:
            health_score: Current health score (0-100)
            account_state: Current account state
            
        Returns:
            Activity budget for this cycle
        """
        if account_state == AccountState.NEW:
            return ActivityBudget(
                upvotes_target=random.randint(15, 20),
                comments_target=random.randint(2, 3),
                promotional_ratio=0.0,
                risk_tolerance=RiskTolerance.LOW,
                allowed_tiers=[1],
                max_posts_per_subreddit_per_day=5,
                comment_constraints=CommentConstraints(
                    max_length=100,
                    min_post_score=10,
                    allow_follow_up_questions=False,
                    allow_thread_replies=False,
                    complexity_level=ComplexityLevel.SIMPLE,
                ),
            )
        
        elif account_state == AccountState.BUILDING:
            return ActivityBudget(
                upvotes_target=random.randint(10, 15),
                comments_target=random.randint(1, 2),
                promotional_ratio=0.0,
                risk_tolerance=RiskTolerance.LOW,
                allowed_tiers=[1, 2],
                max_posts_per_subreddit_per_day=4,
                comment_constraints=CommentConstraints(
                    max_length=150,
                    min_post_score=5,
                    allow_follow_up_questions=False,
                    allow_thread_replies=False,
                    complexity_level=ComplexityLevel.SIMPLE,
                ),
            )
        
        elif account_state in [AccountState.MATURING, AccountState.READY]:
            return ActivityBudget(
                upvotes_target=random.randint(5, 10),
                comments_target=random.randint(0, 1),
                promotional_ratio=0.0,
                risk_tolerance=RiskTolerance.MEDIUM,
                allowed_tiers=[1, 2],
                max_posts_per_subreddit_per_day=3,
                comment_constraints=CommentConstraints(
                    max_length=200,
                    min_post_score=3,
                    allow_follow_up_questions=True,
                    allow_thread_replies=False,
                    complexity_level=ComplexityLevel.MODERATE,
                ),
            )
        
        else:  # ACTIVE
            return ActivityBudget(
                upvotes_target=random.randint(5, 10),
                comments_target=random.randint(1, 2),
                promotional_ratio=0.10,  # 10% promotional
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
    
    def should_run_discovery_cycle(self, account_state: AccountState) -> bool:
        """Determine if discovery cycle should run.
        
        Discovery cycles only run in ACTIVE state.
        
        Args:
            account_state: Current account state
            
        Returns:
            True if discovery cycle should run
        """
        return account_state == AccountState.ACTIVE