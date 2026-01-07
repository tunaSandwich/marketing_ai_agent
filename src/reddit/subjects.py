"""Subject-to-subreddit mapping loader and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError
from loguru import logger


class SubjectsConfig(BaseModel):
    """Top-level subjects configuration."""
    
    subjects: Dict[str, List[str]] = Field(default_factory=dict)

    def get_subreddits_for_subject(self, subject: str) -> List[str]:
        """Return subreddits for a subject (case-insensitive key)."""
        # Find exact or case-insensitive match
        if subject in self.subjects:
            return self.subjects[subject]
        for key, subs in self.subjects.items():
            if key.lower() == subject.lower():
                return subs
        return []


@dataclass
class SubjectsStore:
    """Loader for subject mappings from YAML."""
    
    config_path: Path
    _config: Optional[SubjectsConfig] = None

    def load(self) -> SubjectsConfig:
        """Load YAML configuration from disk."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Subjects mapping not found: {self.config_path}")
        
        try:
            with self.config_path.open(encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            self._config = SubjectsConfig(**raw)
            logger.info(f"Loaded subjects: {len(self._config.subjects)} categories")
            return self._config
        except (yaml.YAMLError, ValidationError) as e:
            logger.error(f"Failed to load subjects: {e}")
            raise

    @property
    def config(self) -> SubjectsConfig:
        if self._config is None:
            return self.load()
        return self._config

    def subreddits_for(self, subject: str) -> List[str]:
        """Convenience accessor."""
        return self.config.get_subreddits_for_subject(subject)


