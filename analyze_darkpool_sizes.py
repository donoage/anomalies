#!/usr/bin/env python3
"""
Analyze dark pool trade sizes to determine optimal minimum threshold
"""
import gzip
import csv
from datetime import datetime, timedelta
from io import BytesIO, StringIO
import boto3
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dark pool identification
DARK_POOL_EXCHANGE_ID = 4

def analyze_darkpool_trades(date):
    """
    Analyze dark pool trade sizes for a given date
    """
    logger.info(f"Analyzing dark pool trades for {date}")
    
    # Initialize S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=Config.POLYGON_S3_ACCESS_KEY,
        aws_secret_access_key=Config.POLYGON_S3_SECRET_KEY,
        region_name='us-east-1',
        endpoint_url='https://files.polygon.io'
    )
    
    # Format S3 path
    year = date.strftime('%Y')
    month = date.strftime('%m')
    date_str = date.strftime('%Y-%m-%d')
    s3_key = f'us_stocks_sip/trades_v1/{year}/{month}/{date_str}.csv.gz'
    
    logger.info(f"Downloading: {s3_key}")
    response = s3_client.get_object(Bucket='flatfiles', Key=s3_key)
    
    # Track trade sizes (sample only first 5M trades for speed)
    trade_sizes = []
    total_trades = 0
    darkpool_trades = 0
    MAX_TRADES = 5_000_000  # Sample first 5M trades
    
    with gzip.GzipFile(fileobj=BytesIO(response['Body'].read())) as gz:
        content = gz.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(content))
        
        for row in csv_reader:
            total_trades += 1
            
            # Stop after sampling enough trades
            if total_trades > MAX_TRADES:
                logger.info(f"Reached sample limit of {MAX_TRADES:,} trades")
                break
            
            try:
                exchange = int(row.get('exchange', 0))
                trf_id = row.get('trf_id', '').strip()
                size = int(row.get('size', 0))
                
                # Check if dark pool
                if exchange == DARK_POOL_EXCHANGE_ID and trf_id:
                    darkpool_trades += 1
                    trade_sizes.append(size)
                
                # Progress update
                if total_trades % 500000 == 0:
                    logger.info(f"Processed {total_trades:,} trades, {darkpool_trades:,} dark pool...")
                    
            except (ValueError, KeyError):
                continue
    
    # Analyze the distribution
    if trade_sizes:
        trade_sizes.sort()
        
        print("\n" + "="*60)
        print(f"DARK POOL TRADE SIZE ANALYSIS - {date}")
        print("="*60)
        print(f"Total trades processed: {total_trades:,}")
        print(f"Dark pool trades: {darkpool_trades:,} ({darkpool_trades/total_trades*100:.2f}%)")
        print(f"\nDark Pool Trade Size Statistics:")
        print(f"  Min size: {min(trade_sizes):,} shares")
        print(f"  Max size: {max(trade_sizes):,} shares")
        print(f"  Mean size: {sum(trade_sizes)/len(trade_sizes):,.0f} shares")
        print(f"  Median size: {trade_sizes[len(trade_sizes)//2]:,} shares")
        
        # Percentiles
        print(f"\nPercentiles:")
        for p in [10, 25, 50, 75, 90, 95, 99]:
            idx = int(len(trade_sizes) * p / 100)
            print(f"  {p}th percentile: {trade_sizes[idx]:,} shares")
        
        # Count trades above various thresholds
        print(f"\nTrades remaining at different thresholds:")
        for threshold in [100, 500, 1000, 2000, 5000, 10000]:
            count = sum(1 for s in trade_sizes if s >= threshold)
            pct = count / len(trade_sizes) * 100
            print(f"  >= {threshold:,} shares: {count:,} trades ({pct:.1f}%)")
        
        # Recommendation
        print(f"\n" + "="*60)
        print("RECOMMENDATION:")
        # Use 75th percentile as a good balance
        recommended = trade_sizes[int(len(trade_sizes) * 0.75)]
        print(f"Set MIN_TRADE_SIZE = {recommended:,} shares")
        print(f"This filters out the bottom 75% of trades (noise)")
        print(f"and keeps {darkpool_trades - int(darkpool_trades * 0.75):,} meaningful trades")
        print("="*60)
        
    else:
        print("No dark pool trades found!")

if __name__ == '__main__':
    # Analyze yesterday's data
    yesterday = datetime.now().date() - timedelta(days=1)
    # If weekend, go back to Friday
    while yesterday.weekday() >= 5:
        yesterday -= timedelta(days=1)
    
    analyze_darkpool_trades(yesterday)

