#!/usr/bin/env python3
"""
Backfill 30 days of historical data using Flat Files and detect anomalies
"""
from datetime import datetime, timedelta
from flatfile_fetcher import FlatFileFetcher
from anomaly_detector import AnomalyDetector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info("BACKFILLING 30 DAYS OF MARKET DATA (FLAT FILES)")
    logger.info("=" * 60)
    logger.info("This will fetch data, build lookup tables, and detect anomalies")
    logger.info("Using Flat Files for fast bulk download!")
    logger.info("")
    
    # Initialize components
    data_fetcher = FlatFileFetcher()
    anomaly_detector = AnomalyDetector()
    
    # Backfill 30 days
    logger.info("Starting backfill for 30 days...")
    try:
        data_fetcher.backfill_data(days=30)
        logger.info("✓ Backfill complete!")
    except Exception as e:
        logger.error(f"✗ Error during backfill: {e}")
        return
    
    # Build lookup table for recent dates
    logger.info("\nBuilding lookup tables for all dates...")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Skip weekends
            try:
                logger.info(f"Building lookup table for {current_date}...")
                anomaly_detector.build_lookup_table(current_date)
            except Exception as e:
                logger.error(f"Error building lookup for {current_date}: {e}")
        current_date += timedelta(days=1)
    
    # Detect anomalies for recent dates
    logger.info("\nDetecting anomalies for recent dates...")
    current_date = start_date + timedelta(days=5)  # Start after we have 5 days of history
    
    total_anomalies = 0
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Skip weekends
            try:
                logger.info(f"Detecting anomalies for {current_date}...")
                anomalies = anomaly_detector.detect_anomalies(current_date)
                if anomalies:
                    logger.info(f"  Found {len(anomalies)} anomalies")
                    total_anomalies += len(anomalies)
            except Exception as e:
                logger.error(f"Error detecting anomalies for {current_date}: {e}")
        current_date += timedelta(days=1)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"BACKFILL COMPLETE!")
    logger.info(f"Total anomalies detected: {total_anomalies}")
    logger.info("=" * 60)
    logger.info("\nYou can now:")
    logger.info("1. Run the web app: python app.py")
    logger.info("2. View anomalies at: http://localhost:8888")
    logger.info("3. Process new days: python process_yesterday.py")

if __name__ == '__main__':
    main()

