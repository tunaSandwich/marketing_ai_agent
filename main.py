#!/usr/bin/env python3
"""Production growth agent - runs discovery cycles on schedule."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Silence HuggingFace tokenizers fork/parallelism warnings and avoid deadlocks
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import schedule
import time
from datetime import datetime

from loguru import logger

from src.orchestrator import GrowthOrchestrator
from src.utils.config import get_settings


def setup_logging():
    """Configure logging for production."""
    logger.remove()  # Remove default handler
    
    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )
    
    # File logging
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "growth_agent_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
    )


def run_discovery_cycle():
    """Deprecated. Use unified orchestrator.run()."""
    logger.warning("run_discovery_cycle() in main.py is deprecated; use orchestrator.run() instead")
    try:
        orchestrator = GrowthOrchestrator(brand_id="goodpods")
        return orchestrator.run_discovery_cycle()
    except Exception as e:
        logger.error(f"❌ Cycle failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


def run_engagement():
    """Deprecated. Use unified orchestrator.run()."""
    logger.warning("run_engagement() in main.py is deprecated; use orchestrator.run() instead")
    try:
        orchestrator = GrowthOrchestrator(brand_id="goodpods")
        return orchestrator.maintain_engagement_ratio()
    except Exception as e:
        logger.error(f"❌ Engagement failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


def main():
    """Main production loop - unified orchestrator with internal scheduling."""
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("🚀 Growth Agent Starting")
    logger.info("=" * 60)
    
    settings = get_settings()
    logger.info(f"Brand: {settings.app.default_brand_id}")
    logger.info(f"Max replies/day: {settings.system.max_replies_per_day}")
    
    try:
        orchestrator = GrowthOrchestrator(brand_id=settings.app.default_brand_id)
        logger.info("Starting unified orchestrator loop (internal scheduling enabled)")
        orchestrator.run()
    except KeyboardInterrupt:
        logger.info("⚠️  Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error in orchestrator: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
