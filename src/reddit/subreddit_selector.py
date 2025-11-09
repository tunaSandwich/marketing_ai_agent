"""Subreddit selection with cooldown tracking."""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger


class SubredditSelector:
    """Manages subreddit selection with cooldown tracking."""
    
    def __init__(
        self,
        tier1_subreddits: List[str],
        tier2_subreddits: List[str],
        tier3_subreddits: List[str],
        cooldown_hours: int = 2,
    ):
        """Initialize subreddit selector.
        
        Args:
            tier1_subreddits: Primary target subreddits
            tier2_subreddits: Secondary subreddits
            tier3_subreddits: Tertiary subreddits
            cooldown_hours: Hours before reusing same subreddit
        """
        self.tier1 = tier1_subreddits
        self.tier2 = tier2_subreddits
        self.tier3 = tier3_subreddits
        self.cooldown_hours = cooldown_hours
        self.last_used: Dict[str, datetime] = {}
        
        logger.info(
            f"SubredditSelector initialized with {len(tier1_subreddits)} tier1, "
            f"{len(tier2_subreddits)} tier2, {len(tier3_subreddits)} tier3 subreddits"
        )
    
    def select_subreddit(
        self,
        allowed_tiers: List[int],
        tier_weights: Optional[Dict[int, float]] = None,
    ) -> str:
        """Select a subreddit respecting cooldowns and tier weights.
        
        Args:
            allowed_tiers: List of allowed tier numbers (1, 2, 3)
            tier_weights: Weight for each tier (default: {1: 0.6, 2: 0.3, 3: 0.1})
            
        Returns:
            Selected subreddit name
        """
        if tier_weights is None:
            tier_weights = {1: 0.6, 2: 0.3, 3: 0.1}
        
        # Collect candidates from allowed tiers
        candidates = []
        for tier in allowed_tiers:
            if tier == 1:
                candidates.extend([(sub, 1) for sub in self.tier1])
            elif tier == 2:
                candidates.extend([(sub, 2) for sub in self.tier2])
            elif tier == 3:
                candidates.extend([(sub, 3) for sub in self.tier3])
        
        if not candidates:
            logger.warning("No subreddits available for allowed tiers")
            # Fallback to tier 1
            candidates = [(sub, 1) for sub in self.tier1]
        
        # Filter out subreddits in cooldown
        available = [
            (sub, tier) for sub, tier in candidates
            if self._is_available(sub)
        ]
        
        if not available:
            logger.warning(
                f"All subreddits in cooldown, ignoring cooldown for this cycle"
            )
            available = candidates
        
        # Create weighted list
        weighted_choices = []
        for sub, tier in available:
            weight = tier_weights.get(tier, 0.1)
            # Add subreddit multiple times based on weight
            count = int(weight * 10)
            weighted_choices.extend([sub] * max(1, count))
        
        # Select randomly from weighted list
        selected = random.choice(weighted_choices)
        self.last_used[selected] = datetime.now()
        
        logger.debug(f"Selected subreddit: r/{selected}")
        return selected
    
    def _is_available(self, subreddit: str) -> bool:
        """Check if subreddit is available (not in cooldown).
        
        Args:
            subreddit: Subreddit name to check
            
        Returns:
            True if available
        """
        if subreddit not in self.last_used:
            return True
        
        last_used = self.last_used[subreddit]
        cooldown_until = last_used + timedelta(hours=self.cooldown_hours)
        
        return datetime.now() >= cooldown_until
    
    def get_subreddit_tier(self, subreddit: str) -> Optional[int]:
        """Get the tier of a subreddit.
        
        Args:
            subreddit: Subreddit name
            
        Returns:
            Tier number (1, 2, 3) or None if not found
        """
        if subreddit in self.tier1:
            return 1
        elif subreddit in self.tier2:
            return 2
        elif subreddit in self.tier3:
            return 3
        return None