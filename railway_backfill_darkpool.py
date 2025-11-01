#!/usr/bin/env python3
"""
Railway-specific backfill script for dark pool data
Run this as a one-time job on Railway to populate the database
"""
from datetime import datetime, timedelta
from flatfile_fetcher import FlatFileFetcher
from anomaly_detector import AnomalyDetector
from config import Config
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 80)
    logger.info("RAILWAY DARK POOL BACKFILL")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  DARK_POOL_ONLY: {Config.DARK_POOL_ONLY}")
    logger.info(f"  USE_TRADES_FILES: {Config.USE_TRADES_FILES}")
    logger.info(f"  MIN_TRADE_SIZE: {Config.MIN_TRADE_SIZE} shares")
    logger.info(f"  LOOKBACK_DAYS: {Config.LOOKBACK_DAYS}")
    logger.info(f"  Z_SCORE_THRESHOLD: {Config.Z_SCORE_THRESHOLD}")
    logger.info("")
    
    # Get backfill days from command line or default to 30
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    logger.info(f"Backfilling {days} days of dark pool data...")
    logger.info("")
    
    # Initialize components
    try:
        data_fetcher = FlatFileFetcher()
        anomaly_detector = AnomalyDetector()
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        sys.exit(1)
    
    # Step 1: Backfill raw trade data
    logger.info("STEP 1: Fetching dark pool trades from S3...")
    logger.info("-" * 80)
    try:
        data_fetcher.backfill_data(days=days, dark_pool_only=True)
        logger.info("✓ Trade data backfill complete!")
    except Exception as e:
        logger.error(f"✗ Error during backfill: {e}")
        sys.exit(1)
    
    # Step 2: Build lookup tables
    logger.info("")
    logger.info("STEP 2: Building lookup tables...")
    logger.info("-" * 80)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    current_date = start_date
    lookup_count = 0
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Skip weekends
            try:
                logger.info(f"Building lookup for {current_date}...")
                anomaly_detector.build_lookup_table(current_date)
                lookup_count += 1
            except Exception as e:
                logger.error(f"Error building lookup for {current_date}: {e}")
        current_date += timedelta(days=1)
    
    logger.info(f"✓ Built {lookup_count} lookup tables!")
    
    # Step 3: Detect anomalies
    logger.info("")
    logger.info("STEP 3: Detecting dark pool anomalies...")
    logger.info("-" * 80)
    
    # Start detection after we have enough lookback history
    start_detection_date = start_date + timedelta(days=Config.LOOKBACK_DAYS)
    
    total_anomalies = 0
    detection_count = 0
    current_date = start_detection_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Skip weekends
            try:
                logger.info(f"Detecting anomalies for {current_date}...")
                anomalies = anomaly_detector.detect_anomalies(current_date)
                if anomalies:
                    logger.info(f"  ✓ Found {len(anomalies)} anomalies")
                    total_anomalies += len(anomalies)
                else:
                    logger.info(f"  No anomalies detected")
                detection_count += 1
            except Exception as e:
                logger.error(f"Error detecting anomalies for {current_date}: {e}")
        current_date += timedelta(days=1)
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("BACKFILL COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Days processed: {days}")
    logger.info(f"Lookup tables built: {lookup_count}")
    logger.info(f"Anomaly detection runs: {detection_count}")
    logger.info(f"Total dark pool anomalies detected: {total_anomalies}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Check the web UI to view anomalies")
    logger.info("2. The scheduler will continue detecting new anomalies daily")
    logger.info("=" * 80)

if __name__ == '__main__':
    try:
        main()
        # Exit cleanly so Railway knows the job completed
        sys.exit(0)
    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        sys.exit(1)

