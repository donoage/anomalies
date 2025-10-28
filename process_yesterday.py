#!/usr/bin/env python3
"""
Process anomalies for yesterday's trading data
"""
from datetime import datetime, timedelta
from data_fetcher import DataFetcher
from anomaly_detector import AnomalyDetector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Calculate yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    # Skip if weekend
    if yesterday.weekday() >= 5:
        logger.info(f"Yesterday ({yesterday}) was a weekend. Skipping.")
        return
    
    logger.info(f"Processing data for {yesterday}")
    logger.info("=" * 60)
    
    # Initialize components
    data_fetcher = DataFetcher()
    anomaly_detector = AnomalyDetector()
    
    # Step 1: Fetch daily aggregates
    logger.info("Step 1: Fetching daily aggregates from Polygon.io...")
    try:
        count = data_fetcher.fetch_daily_aggregates(yesterday)
        logger.info(f"✓ Successfully fetched {count} ticker aggregates")
    except Exception as e:
        logger.error(f"✗ Error fetching data: {e}")
        return
    
    # Step 2: Build lookup table
    logger.info("\nStep 2: Building lookup table with rolling statistics...")
    try:
        ticker_count = anomaly_detector.build_lookup_table(yesterday)
        logger.info(f"✓ Lookup table built for {ticker_count} tickers")
    except Exception as e:
        logger.error(f"✗ Error building lookup table: {e}")
        return
    
    # Step 3: Detect anomalies
    logger.info("\nStep 3: Detecting anomalies...")
    try:
        anomalies = anomaly_detector.detect_anomalies(yesterday)
        logger.info(f"✓ Detected {len(anomalies)} anomalies")
    except Exception as e:
        logger.error(f"✗ Error detecting anomalies: {e}")
        return
    
    # Step 4: Display top anomalies
    if anomalies:
        logger.info("\n" + "=" * 60)
        logger.info("TOP 20 ANOMALIES")
        logger.info("=" * 60)
        
        # Sort by z-score
        sorted_anomalies = sorted(anomalies, key=lambda x: x.z_score, reverse=True)[:20]
        
        print(f"\n{'Ticker':<10}{'Trades':>12}{'Avg (5d)':>12}{'Z-Score':>10}{'Price Chg':>12}{'Close':>10}")
        print("-" * 76)
        
        for a in sorted_anomalies:
            price_change = f"{a.price_diff:+.2f}%" if a.price_diff else "N/A"
            print(
                f"{a.ticker:<10}"
                f"{a.trades:>12,}"
                f"{a.avg_trades:>12,.0f}"
                f"{a.z_score:>10.2f}"
                f"{price_change:>12}"
                f"${a.close_price:>9.2f}"
            )
        
        logger.info("\n" + "=" * 60)
        logger.info(f"Processing complete for {yesterday}")
        logger.info("=" * 60)
    else:
        logger.info("\nNo anomalies detected for this date.")
        logger.info("Try lowering Z_SCORE_THRESHOLD in config or check if data exists.")

if __name__ == '__main__':
    main()

