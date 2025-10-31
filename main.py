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
    """Run one discovery and generation cycle."""
    try:
        logger.info("🔄 Starting discovery cycle...")
        
        orchestrator = GrowthOrchestrator(brand_id="goodpods")
        
        # Run discovery and generation
        stats = orchestrator.run_discovery_cycle()
        
        logger.info(f"✅ Cycle complete: {stats}")
        
    except Exception as e:
        logger.error(f"❌ Cycle failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def run_posting():
    """Post approved drafts."""
    try:
        logger.info("📤 Posting approved drafts...")
        
        orchestrator = GrowthOrchestrator(brand_id="goodpods")
        
        # Post up to 3 approved drafts
        result = orchestrator.post_approved_drafts(limit=3)
        
        logger.info(f"✅ Posting complete: {result}")
        
    except Exception as e:
        logger.error(f"❌ Posting failed: {e}")
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
    
    # Schedule discovery every hour
    schedule.every(1).hours.do(run_discovery_cycle)
    
    # Schedule posting every 3 hours (stagger from discovery)
    schedule.every(3).hours.at(":30").do(run_posting)
    
    logger.info("📅 Scheduler configured:")
    logger.info("  - Discovery: Every 1 hour")
    logger.info("  - Posting: Every 3 hours (at :30)")
    
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