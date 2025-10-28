#!/usr/bin/env python3
"""
Quick backfill for last 6 days to populate yesterday's anomalies
"""
from datetime import datetime, timedelta
from flatfile_fetcher import FlatFileFetcher
from anomaly_detector import AnomalyDetector
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info("BACKFILLING LAST 6 DAYS")
    logger.info("=" * 60)
    
    # Initialize components
    if Config.USE_FLAT_FILES:
        logger.info("Using Flat Files")
        fetcher = FlatFileFetcher()
    else:
        logger.info("Using REST API")
        from data_fetcher import DataFetcher
        fetcher = DataFetcher()
    
    detector = AnomalyDetector()
    
    # Backfill last 6 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Skip weekends
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing {current_date}")
                logger.info(f"{'='*60}")
                
                # Fetch data
                count = fetcher.fetch_daily_aggregates(current_date)
                logger.info(f"✓ Fetched {count} tickers")
                
                # Build lookup table
                detector.build_lookup_table(current_date)
                logger.info(f"✓ Built lookup table")
                
                # Detect anomalies (only if we have enough history)
                days_back = (end_date - current_date).days
                if days_back <= 1:  # Only detect for yesterday and today
                    anomalies = detector.detect_anomalies(current_date)
                    logger.info(f"✓ Detected {len(anomalies)} anomalies")
                    
            except Exception as e:
                logger.error(f"✗ Error processing {current_date}: {e}")
        
        current_date += timedelta(days=1)
    
    logger.info("\n" + "=" * 60)
    logger.info("BACKFILL COMPLETE!")
    logger.info("=" * 60)

if __name__ == '__main__':
    main()

