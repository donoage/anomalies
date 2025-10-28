"""
Flat Files Data Fetcher for Polygon.io
Uses S3 to download daily aggregate files and filter for dark pool trades
"""
import os
import gzip
import csv
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from minio import Minio
from minio.error import S3Error
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
    Fetches data from Polygon.io Flat Files using S3/MinIO
    """
    
    def __init__(self):
        if not Config.POLYGON_API_KEY:
            raise ValueError("POLYGON_API_KEY not set in environment variables")
        
        # Initialize MinIO client for Polygon.io S3
        # Polygon uses the API key as both access key and secret key
        self.client = Minio(
            "files.polygon.io",
            access_key=Config.POLYGON_API_KEY,
            secret_key=Config.POLYGON_API_KEY,
            secure=True,
            region="us-east-1"
        )
        
        self.bucket = "flatfiles"
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        
        logger.info(f"Initialized Flat File Fetcher with bucket: {self.bucket}")
    
    def fetch_daily_aggregates(self, date, dark_pool_only=True):
        """
        Fetch daily aggregates from flat files for a specific date
        
        Args:
            date: Date to fetch (datetime.date object)
            dark_pool_only: If True, only include dark pool trades
        
        Returns:
            Number of tickers processed
        """
        logger.info(f"Fetching flat file aggregates for {date} (dark_pool_only={dark_pool_only})")
        
        # Format the S3 path for day aggregates
        # Path format: us_stocks_sip/day_aggs_v1/YYYY/MM/YYYY-MM-DD.csv.gz
        year = date.strftime('%Y')
        month = date.strftime('%m')
        filename = f"{date.strftime('%Y-%m-%d')}.csv.gz"
        object_path = f"us_stocks_sip/day_aggs_v1/{year}/{month}/{filename}"
        
        logger.info(f"Downloading: {object_path}")
        
        try:
            # Download the file from S3
            response = self.client.get_object(self.bucket, object_path)
            
            # Read and decompress the gzipped content
            gzipped_data = response.read()
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
                logger.info(f"Successfully processed {count} tickers from flat file for {date}")
                return count
                
            except Exception as e:
                logger.error(f"Error processing flat file data: {e}")
                session.rollback()
                raise
            finally:
                db.close_session()
                
        except S3Error as e:
            logger.error(f"S3 Error downloading flat file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching flat file: {e}")
            raise
        finally:
            if response:
                response.close()
                response.release_conn()
    
    def fetch_trades_and_aggregate(self, date, dark_pool_only=True):
        """
        Fetch trades from flat files and aggregate manually
        This allows filtering by exchange (dark pool vs lit pool)
        
        Args:
            date: Date to fetch (datetime.date object)
            dark_pool_only: If True, only include dark pool trades
        
        Returns:
            Number of tickers processed
        """
        logger.info(f"Fetching trades flat file for {date} (dark_pool_only={dark_pool_only})")
        
        # Path format: us_stocks_sip/trades_v1/YYYY/MM/YYYY-MM-DD.csv.gz
        year = date.strftime('%Y')
        month = date.strftime('%m')
        filename = f"{date.strftime('%Y-%m-%d')}.csv.gz"
        object_path = f"us_stocks_sip/trades_v1/{year}/{month}/{filename}"
        
        logger.info(f"Downloading: {object_path}")
        
        try:
            # Download the file from S3
            response = self.client.get_object(self.bucket, object_path)
            
            # Read and decompress the gzipped content
            gzipped_data = response.read()
            decompressed_data = gzip.decompress(gzipped_data)
            
            # Parse CSV and aggregate by ticker
            csv_content = StringIO(decompressed_data.decode('utf-8'))
            reader = csv.DictReader(csv_content)
            
            # Aggregate trades by ticker
            ticker_data = {}
            
            for row in reader:
                ticker = row['ticker']
                exchange = row.get('exchange', '')
                
                # Filter for dark pool if requested
                if dark_pool_only and exchange not in DARK_POOL_EXCHANGES:
                    continue
                
                if ticker not in ticker_data:
                    ticker_data[ticker] = {
                        'trades': [],
                        'volume': 0,
                        'transactions': 0
                    }
                
                # Parse trade data
                price = float(row['price']) if row.get('price') else 0
                size = int(row['size']) if row.get('size') else 0
                
                ticker_data[ticker]['trades'].append(price)
                ticker_data[ticker]['volume'] += size
                ticker_data[ticker]['transactions'] += 1
            
            # Calculate OHLC and store in database
            session = db.get_session()
            count = 0
            
            try:
                for ticker, data in ticker_data.items():
                    if not data['trades']:
                        continue
                    
                    # Calculate OHLC
                    open_price = data['trades'][0]
                    close_price = data['trades'][-1]
                    high_price = max(data['trades'])
                    low_price = min(data['trades'])
                    
                    # Check if already exists
                    existing = session.query(DailyAggregate).filter_by(
                        ticker=ticker,
                        date=date
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.volume = data['volume']
                        existing.open = open_price
                        existing.close = close_price
                        existing.high = high_price
                        existing.low = low_price
                        existing.transactions = data['transactions']
                    else:
                        # Create new record
                        daily_agg = DailyAggregate(
                            ticker=ticker,
                            date=date,
                            volume=data['volume'],
                            open=open_price,
                            close=close_price,
                            high=high_price,
                            low=low_price,
                            transactions=data['transactions']
                        )
                        session.add(daily_agg)
                    
                    count += 1
                    if count % 100 == 0:
                        session.commit()
                        logger.info(f"Processed {count} tickers...")
                
                session.commit()
                logger.info(f"Successfully aggregated {count} tickers from trades for {date}")
                return count
                
            except Exception as e:
                logger.error(f"Error aggregating trades data: {e}")
                session.rollback()
                raise
            finally:
                db.close_session()
                
        except S3Error as e:
            logger.error(f"S3 Error downloading trades file: {e}")
            logger.info("Note: Trades files are much larger and may not be available for all dates")
            raise
        except Exception as e:
            logger.error(f"Error fetching trades file: {e}")
            raise
        finally:
            if response:
                response.close()
                response.release_conn()
    
    def backfill_data(self, days=30, dark_pool_only=True, use_trades=False):
        """
        Backfill historical data using flat files
        
        Args:
            days: Number of days to backfill
            dark_pool_only: If True, only include dark pool trades
            use_trades: If True, use trades files (allows dark pool filtering)
                       If False, use day aggregates files (faster, no filtering)
        """
        logger.info(f"Starting flat file backfill for {days} days")
        logger.info(f"Dark pool only: {dark_pool_only}, Use trades: {use_trades}")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                try:
                    if use_trades:
                        # Use trades files for dark pool filtering
                        self.fetch_trades_and_aggregate(current_date, dark_pool_only)
                    else:
                        # Use day aggregates (faster, but no dark pool filtering)
                        self.fetch_daily_aggregates(current_date, dark_pool_only)
                except Exception as e:
                    logger.error(f"Error backfilling data for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        logger.info("Flat file backfill complete")

