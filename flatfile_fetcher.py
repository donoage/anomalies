"""
Flat Files Data Fetcher for Polygon.io using boto3
Uses S3 to download daily aggregate files
"""
import os
import gzip
import csv
from datetime import datetime, timedelta
from io import BytesIO, StringIO
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from config import Config
from database import db, DailyAggregate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Dark pool exchange codes (Trade Reporting Facilities)
DARK_POOL_EXCHANGES = {
    'TRF',  # FINRA Trade Reporting Facility
    'ADF',  # Alternative Display Facility
}


class FlatFileFetcher:
    """
    Fetches data from Polygon.io Flat Files using boto3 S3 client
    """
    
    def __init__(self):
        if not Config.POLYGON_S3_ACCESS_KEY or not Config.POLYGON_S3_SECRET_KEY:
            raise ValueError(
                "S3 credentials not set. Please get your S3 Access Key and Secret Key from "
                "https://polygon.io/dashboard and set POLYGON_S3_ACCESS_KEY and POLYGON_S3_SECRET_KEY"
            )
        
        # Initialize boto3 S3 client for Polygon.io
        # Use S3-specific credentials from dashboard (not regular API key)
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.POLYGON_S3_ACCESS_KEY,
            aws_secret_access_key=Config.POLYGON_S3_SECRET_KEY,
            region_name='us-east-1',
            endpoint_url='https://files.polygon.io'
        )
        
        self.bucket = 'flatfiles'
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        
        logger.info(f"Initialized Flat File Fetcher with bucket: {self.bucket}")
    
    def fetch_daily_aggregates(self, date, dark_pool_only=False):
        """
        Fetch daily aggregates from flat files for a specific date
        Note: Day aggregates don't support dark pool filtering
        
        Args:
            date: Date to fetch (datetime.date object)
            dark_pool_only: Ignored for day aggregates (use fetch_trades_and_aggregate instead)
        
        Returns:
            Number of tickers processed
        """
        if dark_pool_only:
            logger.warning("Day aggregates don't support dark pool filtering. Use fetch_trades_and_aggregate() instead.")
        
        logger.info(f"Fetching flat file aggregates for {date}")
        
        # Format the S3 path for day aggregates
        # Path format: us_stocks_sip/day_aggs_v1/YYYY/MM/YYYY-MM-DD.csv.gz
        year = date.strftime('%Y')
        month = date.strftime('%m')
        filename = f"{date.strftime('%Y-%m-%d')}.csv.gz"
        object_key = f"us_stocks_sip/day_aggs_v1/{year}/{month}/{filename}"
        
        logger.info(f"Downloading: s3://{self.bucket}/{object_key}")
        
        try:
            # Download the file from S3
            response = self.s3_client.get_object(Bucket=self.bucket, Key=object_key)
            
            # Read and decompress the gzipped content
            gzipped_data = response['Body'].read()
            decompressed_data = gzip.decompress(gzipped_data)
            
            # Parse CSV
            csv_content = StringIO(decompressed_data.decode('utf-8'))
            reader = csv.DictReader(csv_content)
            
            session = db.get_session()
            count = 0
            
            try:
                for row in reader:
                    ticker = row['ticker']
                    
                    # Check if already exists
                    existing = session.query(DailyAggregate).filter_by(
                        ticker=ticker,
                        date=date
                    ).first()
                    
                    # Parse values
                    volume = int(row['volume']) if row['volume'] else 0
                    open_price = float(row['open']) if row['open'] else 0
                    close_price = float(row['close']) if row['close'] else 0
                    high_price = float(row['high']) if row['high'] else 0
                    low_price = float(row['low']) if row['low'] else 0
                    transactions = int(row['transactions']) if row.get('transactions') else None
                    
                    if existing:
                        # Update existing record
                        existing.volume = volume
                        existing.open = open_price
                        existing.close = close_price
                        existing.high = high_price
                        existing.low = low_price
                        existing.transactions = transactions
                    else:
                        # Create new record
                        daily_agg = DailyAggregate(
                            ticker=ticker,
                            date=date,
                            volume=volume,
                            open=open_price,
                            close=close_price,
                            high=high_price,
                            low=low_price,
                            transactions=transactions
                        )
                        session.add(daily_agg)
                    
                    count += 1
                    if count % 1000 == 0:
                        session.commit()
                        logger.info(f"Processed {count} tickers...")
                
                session.commit()
                logger.info(f"✓ Successfully processed {count} tickers from flat file for {date}")
                return count
                
            except Exception as e:
                logger.error(f"Error processing flat file data: {e}")
                session.rollback()
                raise
            finally:
                db.close_session()
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403' or error_code == 'AccessDenied':
                logger.error(f"Access denied to flat files. Please check:")
                logger.error("1. Your Polygon.io plan includes Flat Files access")
                logger.error("2. Your API key is correct")
                logger.error("3. Flat files are available for this date")
            else:
                logger.error(f"S3 Client Error: {e}")
            raise
        except NoCredentialsError:
            logger.error("No credentials provided for S3 access")
            raise
        except Exception as e:
            logger.error(f"Error fetching flat file: {e}")
            raise
    
    def backfill_data(self, days=30, dark_pool_only=False):
        """
        Backfill historical data using flat files
        
        Args:
            days: Number of days to backfill
            dark_pool_only: Ignored for day aggregates
        """
        logger.info(f"Starting flat file backfill for {days} days")
        if dark_pool_only:
            logger.warning("Dark pool filtering not available with day aggregates")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        success_count = 0
        error_count = 0
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                try:
                    self.fetch_daily_aggregates(current_date, dark_pool_only=False)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error backfilling data for {current_date}: {e}")
                    error_count += 1
            
            current_date += timedelta(days=1)
        
        logger.info(f"Flat file backfill complete: {success_count} successful, {error_count} errors")

