import os
from datetime import datetime, timedelta
from polygon import RESTClient
from config import Config
from database import db, DailyAggregate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self):
        if not Config.POLYGON_API_KEY:
            raise ValueError("POLYGON_API_KEY not set in environment variables")
        self.client = RESTClient(Config.POLYGON_API_KEY)
        os.makedirs(Config.DATA_DIR, exist_ok=True)
    
    def fetch_daily_aggregates(self, date):
        """
        Fetch daily aggregates for all tickers for a specific date
        """
        logger.info(f"Fetching daily aggregates for {date}")
        
        session = db.get_session()
        try:
            # Format date for API
            date_str = date.strftime('%Y-%m-%d')
            
            # Fetch grouped daily bars for all tickers
            # Note: This requires a paid Polygon.io plan
            aggs = self.client.get_grouped_daily_aggs(
                date=date_str,
                adjusted=True
            )
            
            count = 0
            for agg in aggs:
                # Check if already exists
                existing = session.query(DailyAggregate).filter_by(
                    ticker=agg.ticker,
                    date=date
                ).first()
                
                if existing:
                    # Update existing record
                    existing.volume = agg.volume
                    existing.open = agg.open
                    existing.close = agg.close
                    existing.high = agg.high
                    existing.low = agg.low
                    existing.transactions = agg.transactions if hasattr(agg, 'transactions') else None
                else:
                    # Create new record
                    daily_agg = DailyAggregate(
                        ticker=agg.ticker,
                        date=date,
                        volume=agg.volume,
                        open=agg.open,
                        close=agg.close,
                        high=agg.high,
                        low=agg.low,
                        transactions=agg.transactions if hasattr(agg, 'transactions') else None
                    )
                    session.add(daily_agg)
                
                count += 1
                if count % 100 == 0:
                    session.commit()
                    logger.info(f"Processed {count} tickers...")
            
            session.commit()
            logger.info(f"Successfully fetched and stored {count} daily aggregates for {date}")
            return count
            
        except Exception as e:
            logger.error(f"Error fetching daily aggregates: {e}")
            session.rollback()
            raise
        finally:
            db.close_session()
    
    def fetch_ticker_aggregates(self, ticker, from_date, to_date):
        """
        Fetch aggregates for a specific ticker over a date range
        """
        try:
            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=from_date.strftime('%Y-%m-%d'),
                to=to_date.strftime('%Y-%m-%d'),
                adjusted=True
            )
            
            return list(aggs)
        except Exception as e:
            logger.error(f"Error fetching aggregates for {ticker}: {e}")
            return []
    
    def backfill_data(self, days=30):
        """
        Backfill historical data for the specified number of days
        """
        logger.info(f"Starting backfill for {days} days")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                try:
                    self.fetch_daily_aggregates(current_date)
                    # No rate limiting needed for unlimited plan
                except Exception as e:
                    logger.error(f"Error backfilling data for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        logger.info("Backfill complete")

