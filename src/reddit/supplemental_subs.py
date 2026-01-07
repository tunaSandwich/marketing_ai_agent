"""Utilities to load supplemental subreddits from subjects mapping."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Set

from loguru import logger

from .subjects import SubjectsStore


def _repo_root_from(file_path: Path) -> Path:
    # src/reddit -> src -> repo root
    return file_path.parent.parent.parent


def load_flattened_subject_subreddits(limit: int | None = None) -> List[str]:
    """Load and flatten all subreddits from subjects_to_subreddits.yaml.
    
    Args:
        limit: optional maximum number of unique subreddits to return
        
    Returns:
        De-duplicated, case-sensitive canonical subreddit names.
    """
    try:
        repo_root = _repo_root_from(Path(__file__).resolve())
        cfg_path = repo_root / "configs" / "subjects_to_subreddits.yaml"
        
        store = SubjectsStore(config_path=cfg_path)
        config = store.load()
        
        seen: Set[str] = set()
        ordered: List[str] = []
        
        for _, subs in config.subjects.items():
            for sub in subs:
                name = sub.strip().lstrip("r/")
                if not name:
                    continue
                if name not in seen:
                    seen.add(name)
                    ordered.append(name)
        
        if limit is not None and limit > 0:
            ordered = ordered[:limit]
        
        logger.info(f"Loaded {len(ordered)} supplemental subreddits from subjects map")
        return ordered
    except FileNotFoundError:
        logger.warning("Subjects mapping not found, skipping supplemental subreddits")
        return []
    except Exception as e:
        logger.error(f"Failed to load supplemental subreddits: {e}")
        return []


