#!/usr/bin/env python3
"""
Test script for Flat Files implementation
Tests S3 connection and file download
"""
from datetime import datetime, timedelta
from flatfile_fetcher import FlatFileFetcher
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info("TESTING FLAT FILES SETUP")
    logger.info("=" * 60)
    logger.info(f"API Key configured: {bool(Config.POLYGON_API_KEY)}")
    logger.info(f"Use Flat Files: {Config.USE_FLAT_FILES}")
    logger.info(f"Dark Pool Only: {Config.DARK_POOL_ONLY}")
    logger.info(f"Use Trades Files: {Config.USE_TRADES_FILES}")
    logger.info("")
    
    try:
        # Initialize fetcher
        logger.info("Initializing Flat File Fetcher...")
        fetcher = FlatFileFetcher()
        logger.info("✓ Fetcher initialized successfully")
        logger.info("")
        
        # Test with yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).date()
        logger.info(f"Testing with date: {yesterday}")
        logger.info("")
        
        # Test 1: Day Aggregates (faster, no dark pool filtering)
        logger.info("Test 1: Fetching Day Aggregates...")
        try:
            count = fetcher.fetch_daily_aggregates(yesterday, dark_pool_only=False)
            logger.info(f"✓ Successfully fetched {count} tickers from day aggregates")
        except Exception as e:
            logger.error(f"✗ Error fetching day aggregates: {e}")
        
        logger.info("")
        
        # Test 2: Trades (slower, allows dark pool filtering)
        if Config.USE_TRADES_FILES:
            logger.info("Test 2: Fetching and Aggregating Trades (Dark Pool Only)...")
            logger.info("Note: This may take several minutes for large files...")
            try:
                count = fetcher.fetch_trades_and_aggregate(yesterday, dark_pool_only=True)
                logger.info(f"✓ Successfully aggregated {count} tickers from dark pool trades")
            except Exception as e:
                logger.error(f"✗ Error fetching trades: {e}")
                logger.info("This is expected if trades files are very large or not available")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("FLAT FILES TEST COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()

