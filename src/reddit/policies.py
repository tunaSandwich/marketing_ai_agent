"""Subreddit policy loader and accessors."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError
from loguru import logger


class SubredditPolicy(BaseModel):
    """Policy settings for a single subreddit."""
    
    allow_links: bool = Field(default=False, description="Whether links are allowed by default")
    promo_ratio_override: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional promotional ratio override for this subreddit",
    )
    max_length: int | None = Field(default=None, description="Suggested max reply length")
    min_post_score: int | None = Field(default=None, description="Suggested min post score")
    notes: str | None = Field(default=None, description="Free-form guidance")


class SubredditPolicyConfig(BaseModel):
    """Top-level subreddit policy configuration."""
    
    defaults: SubredditPolicy = Field(default_factory=SubredditPolicy)
    subreddits: Dict[str, SubredditPolicy] = Field(default_factory=dict)

    def get_policy(self, subreddit: str) -> SubredditPolicy:
        """Get policy for subreddit, falling back to defaults."""
        key = subreddit.strip().lstrip("r/")  # normalize
        if key in self.subreddits:
            # Merge subreddit-specific over defaults
            base = self.defaults.model_copy(deep=True)
            override = self.subreddits[key]
            merged = base.model_copy(update={k: v for k, v in override.model_dump().items() if v is not None})
            return merged
        return self.defaults


@dataclass
class SubredditPolicyStore:
    """Loader for subreddit policies from YAML."""
    
    config_path: Path
    _config: Optional[SubredditPolicyConfig] = None

    def load(self) -> SubredditPolicyConfig:
        """Load YAML configuration from disk."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Subreddit policies not found: {self.config_path}")
        
        try:
            with self.config_path.open(encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            self._config = SubredditPolicyConfig(**raw)
            logger.info(
                f"Loaded subreddit policies: {len(self._config.subreddits)} entries "
                f"(defaults: allow_links={self._config.defaults.allow_links})"
            )
            return self._config
        except (yaml.YAMLError, ValidationError) as e:
            logger.error(f"Failed to load subreddit policies: {e}")
            raise

    @property
    def config(self) -> SubredditPolicyConfig:
        if self._config is None:
            return self.load()
        return self._config

    def get(self, subreddit: str) -> SubredditPolicy:
        return self.config.get_policy(subreddit)


