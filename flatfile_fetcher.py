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


# Dark pool identification per Polygon.io docs:
# https://polygon.io/knowledge-base/article/does-polygon-offer-dark-pool-data
# Dark pool trades have exchange ID = 4 AND a trf_id field
DARK_POOL_EXCHANGE_ID = 4


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
    
    def fetch_trades_and_aggregate(self, date, dark_pool_only=True, min_trade_size=100):
        """
        Fetch individual trades from flat files and aggregate them
        This allows filtering by dark pool exchanges and minimum trade size
        
        Args:
            date: Date to fetch (datetime.date object)
            dark_pool_only: Only include dark pool trades (TRF/ADF exchanges)
            min_trade_size: Minimum number of shares per trade to include
        
        Returns:
            Number of tickers processed
        """
        logger.info(f"Fetching trades for {date} (dark_pool_only={dark_pool_only}, min_size={min_trade_size})")
        
        # Format the S3 path for trades
        # Path format: us_stocks_sip/trades_v1/YYYY/MM/YYYY-MM-DD.csv.gz
        year = date.strftime('%Y')
        month = date.strftime('%m')
        date_str = date.strftime('%Y-%m-%d')
        s3_key = f'us_stocks_sip/trades_v1/{year}/{month}/{date_str}.csv.gz'
        
        try:
            logger.info(f"Downloading trades file: {s3_key}")
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            
            # Read and decompress the gzipped CSV
            with gzip.GzipFile(fileobj=BytesIO(response['Body'].read())) as gz:
                content = gz.read().decode('utf-8')
                csv_reader = csv.DictReader(StringIO(content))
                
                # Aggregate trades by ticker
                ticker_data = {}
                
                for row in csv_reader:
                    try:
                        ticker = row.get('ticker', '').strip()
                        exchange = int(row.get('exchange', 0))
                        trf_id = row.get('trf_id', '').strip()
                        size = int(row.get('size', 0))
                        price = float(row.get('price', 0))
                        
                        # Filter by dark pool if requested
                        # Per Polygon docs: dark pool = exchange ID 4 + trf_id field present
                        if dark_pool_only:
                            if exchange != DARK_POOL_EXCHANGE_ID or not trf_id:
                                continue
                        
                        # Filter by minimum trade size
                        if size < min_trade_size:
                            continue
                        
                        if not ticker:
                            continue
                        
                        # Initialize ticker data if first time seeing it
                        if ticker not in ticker_data:
                            ticker_data[ticker] = {
                                'trades': 0,
                                'volume': 0,
                                'prices': [],
                                'high': 0,
                                'low': float('inf')
                            }
                        
                        # Aggregate the trade
                        ticker_data[ticker]['trades'] += 1
                        ticker_data[ticker]['volume'] += size
                        ticker_data[ticker]['prices'].append(price)
                        ticker_data[ticker]['high'] = max(ticker_data[ticker]['high'], price)
                        ticker_data[ticker]['low'] = min(ticker_data[ticker]['low'], price)
                        
                    except (ValueError, KeyError) as e:
                        continue  # Skip malformed rows
                
                # Save aggregated data to database
                session = db.get_session()
                try:
                    count = 0
                    for ticker, data in ticker_data.items():
                        if data['trades'] == 0:
                            continue
                        
                        # Calculate open/close from prices
                        open_price = data['prices'][0]
                        close_price = data['prices'][-1]
                        
                        # Check if record exists
                        existing = session.query(DailyAggregate).filter_by(
                            ticker=ticker,
                            date=date
                        ).first()
                        
                        if existing:
                            # Update existing record
                            existing.open = open_price
                            existing.close = close_price
                            existing.high = data['high']
                            existing.low = data['low']
                            existing.volume = data['volume']
                            existing.transactions = data['trades']
                        else:
                            # Insert new record
                            daily_agg = DailyAggregate(
                                ticker=ticker,
                                date=date,
                                open=open_price,
                                close=close_price,
                                volume=data['volume'],
                                high=data['high'],
                                low=data['low'],
                                transactions=data['trades']
                            )
                            session.add(daily_agg)
                        
                        count += 1
                        if count % 1000 == 0:
                            session.commit()
                            logger.info(f"Processed {count} tickers...")
                    
                    session.commit()
                    logger.info(f"✓ Successfully processed {count} tickers from trades file for {date}")
                    return count
                    
                except Exception as e:
                    logger.error(f"Error processing trades data: {e}")
                    session.rollback()
                    raise
                finally:
                    db.close_session()
                    
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403' or error_code == 'AccessDenied':
                logger.error(f"Access denied to trades files. Please check:")
                logger.error("1. Your Polygon.io plan includes Flat Files access")
                logger.error("2. Trades files may require a higher tier plan")
            else:
                logger.error(f"S3 Client Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching trades file: {e}")
            raise
    
    def backfill_data(self, days=30, dark_pool_only=False):
        """
        Backfill historical data using flat files
        
        Args:
            days: Number of days to backfill
            dark_pool_only: Use trades files with dark pool filtering if True
        """
        use_trades = Config.USE_TRADES_FILES or dark_pool_only
        logger.info(f"Starting flat file backfill for {days} days (use_trades={use_trades})")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        success_count = 0
        error_count = 0
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                try:
                    if use_trades:
                        self.fetch_trades_and_aggregate(
                            current_date, 
                            dark_pool_only=Config.DARK_POOL_ONLY,
                            min_trade_size=Config.MIN_TRADE_SIZE
                        )
                    else:
                        self.fetch_daily_aggregates(current_date, dark_pool_only=False)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error backfilling data for {current_date}: {e}")
                    error_count += 1
            
            current_date += timedelta(days=1)
        
        logger.info(f"Flat file backfill complete: {success_count} successful, {error_count} errors")

