#!/usr/bin/env python3
"""Production growth agent - runs discovery cycles on schedule."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

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
    """Run one discovery and generation cycle (or warming)."""
    try:
        logger.info("🔄 Starting cycle...")
        
        orchestrator = GrowthOrchestrator(brand_id="goodpods")
        
        # Run cycle (automatically detects if warming needed)
        stats = orchestrator.run_discovery_cycle()
        
        # Check if in warming mode
        if stats.get("mode") == "warming":
            logger.info("🌱 Warming mode active")
            logger.info(f"   Reason: {stats.get('reason')}")
            warming = stats.get('warming_result', {})
            logger.info(f"   Progress: {warming.get('overall_progress_percent', 0):.1f}% complete")
            if warming.get('upvotes'):
                logger.info(f"   Upvoted: {warming['upvotes'].get('upvoted', 0)} posts")
            if warming.get('comment_posted'):
                logger.info(f"   Posted helpful comment: {warming['comment_posted']}")
        else:
            logger.info(f"✅ Cycle complete: {stats}")
        
    except Exception as e:
        logger.error(f"❌ Cycle failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def run_engagement():
    """Maintain healthy engagement ratio."""
    try:
        logger.info("🎯 Running engagement maintenance...")
        
        orchestrator = GrowthOrchestrator(brand_id="goodpods")
        result = orchestrator.maintain_engagement_ratio()
        
        logger.info(f"✅ Engagement complete: {result}")
        
    except Exception as e:
        logger.error(f"❌ Engagement failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def main():
    """Main production loop."""
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("🚀 Growth Agent Starting")
    logger.info("=" * 60)
    
    settings = get_settings()
    logger.info(f"Brand: {settings.app.default_brand_id}")
    logger.info(f"Max replies/day: {settings.system.max_replies_per_day}")
    
    # Run immediately on startup
    logger.info("Running initial cycle...")
    run_discovery_cycle()
    
    # Run initial engagement
    logger.info("Running initial engagement...")
    run_engagement()
    
    # Schedule discovery + auto-posting every hour
    schedule.every(1).hours.do(run_discovery_cycle)
    
    # Schedule engagement maintenance every 2 hours (offset from discovery)
    schedule.every(2).hours.at(":15").do(run_engagement)
    
    logger.info("📅 Scheduler configured:")
    logger.info("  - Discovery + Auto-posting: Every 1 hour")
    logger.info("  - Engagement (upvotes): Every 2 hours at :15")
    logger.info("  - 🎯 Auto-post threshold: 8.0/10")
    logger.info("  - ❌ Auto-reject threshold: <6.0/10")
    
    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            logger.info("⚠️  Shutting down gracefully...")
            break
            
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying


if __name__ == "__main__":
    main()
