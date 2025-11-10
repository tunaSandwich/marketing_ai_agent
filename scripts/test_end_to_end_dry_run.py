"""End-to-end dry-run: real data, no actual posting.

This script runs the unified engagement cycle using real Reddit reads and LLM,
but monkeypatches Reddit's `Submission.reply` so no comment is actually posted.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from src.brand.loader import BrandLoader
from src.reddit.engagement import RedditEngagementManager
from src.utils.config import get_settings


@dataclass
class _DummyComment:
    id: str


def main() -> None:
    settings = get_settings()

    # Load brand config
    brands_dir = Path(__file__).parent.parent / "brands"
    brand_loader = BrandLoader(brands_dir)
    brand_config = brand_loader.load_brand_config(settings.app.default_brand_id)

    # Initialize manager (this also loads RAG index for the brand)
    manager = RedditEngagementManager(
        reddit_config=settings.reddit,
        llm_config=settings.llm,
        brand_config=brand_config,
    )

    # Monkeypatch praw Submission.reply to avoid real posting
    try:
        import praw.models.reddit.submission as submission_mod

        original_reply = submission_mod.Submission.reply

        def dry_run_reply(self, body: str):
            # Simulate network and return a dummy comment object
            logger.info("[DRY-RUN] Would post comment on %s: %s...", getattr(self, "id", "?"), body[:140])
            time.sleep(random.uniform(0.2, 0.6))
            return _DummyComment(id=f"dryrun_{int(time.time())}")

        submission_mod.Submission.reply = dry_run_reply  # type: ignore[attr-defined]
        logger.info("✅ Dry-run mode active: Submission.reply is monkeypatched")
    except Exception as e:
        logger.warning(f"Could not monkeypatch Submission.reply, continuing: {e}")
        original_reply = None

    try:
        # Run one engagement cycle end-to-end (no actual posts)
        result = manager.run_engagement_cycle()
        logger.info(
            "Cycle result: type=%s health=%.1f helpful=%d promo=%d errors=%d",
            result.cycle_type,
            result.health_score,
            len(result.helpful_comments_posted),
            len(result.promotional_comments_posted),
            len(result.errors),
        )
    finally:
        # Restore original reply
        if original_reply is not None:
            try:
                import praw.models.reddit.submission as submission_mod

                submission_mod.Submission.reply = original_reply  # type: ignore[attr-defined]
                logger.info("Dry-run patch removed; Submission.reply restored")
            except Exception:
                pass


if __name__ == "__main__":
    main()


